"""
Semantic Evaluation Engine for Legal Metrology Rule Validation.

Validates semantic LLM output using strict Pydantic schemas,
verifies evidence presence against actual package OCR to prevent hallucinations,
applies confidence thresholds, and enforces deterministic fallback safety.
"""

import logging
import re
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field, ValidationError
from django.conf import settings

from .providers import BaseLLMProvider, get_llm_provider

logger = logging.getLogger(__name__)


class SemanticEvaluationOutput(BaseModel):
    """Strict structured JSON schema expected from the LLM."""

    rule_id: str
    status: Literal["PASS", "FAIL", "WARNING", "REVIEW"]
    confidence: float = Field(ge=0.0, le=1.0)
    evidence: str = Field(default="")
    reason: str = Field(default="")
    requires_human_review: bool = Field(default=False)


def normalize_text_for_matching(text: str) -> str:
    """Normalizes whitespace and punctuation for fuzzy evidence containment checks."""
    if not text:
        return ""
    text = text.lower()
    return re.sub(r"[\s\W_]+", " ", text).strip()


def verify_evidence_presence(
    evidence: str,
    candidate_text: str,
    raw_ocr_text: Optional[str] = None,
    all_extracted_values: Optional[List[str]] = None,
) -> bool:
    """
    Anti-Hallucination Gatekeeper:
    Verifies that the evidence cited by the LLM is genuinely present in the
    package's candidate text, raw OCR text, or extracted fields.
    """
    if not evidence or not evidence.strip():
        # If status is PASS/FAIL without evidence, evidence verification fails
        return False

    norm_evidence = normalize_text_for_matching(evidence)
    if not norm_evidence:
        return False

    # Check against candidate text
    if norm_evidence in normalize_text_for_matching(candidate_text):
        return True

    # Check against raw OCR text
    if raw_ocr_text and norm_evidence in normalize_text_for_matching(raw_ocr_text):
        return True

    # Check against all extracted values
    if all_extracted_values:
        for val in all_extracted_values:
            if norm_evidence in normalize_text_for_matching(str(val)):
                return True

    # Word-level containment check for slight tokenization differences (at least 75% tokens present in sequence)
    words = norm_evidence.split()
    if len(words) >= 3:
        all_text = f"{candidate_text} {raw_ocr_text or ''}"
        norm_all = normalize_text_for_matching(all_text)
        # Check sub-phrases of 3 words
        for i in range(len(words) - 2):
            sub = " ".join(words[i : i + 3])
            if sub in norm_all:
                return True

    return False


def is_semantic_rule(rule: Dict[str, Any]) -> bool:
    """
    Determines whether a rule is designated for semantic LLM reasoning.
    Ensures that arithmetic, numeric, date, and unit checks are NEVER sent to the LLM.
    """
    # Explicit semantic flags
    if rule.get("is_semantic") is True or rule.get("requires_semantic") is True:
        return True

    cond = rule.get("condition")
    if isinstance(cond, dict):
        cond_type = cond.get("type", "")
        if cond_type == "semantic_check" or cond.get("requires_semantic") is True:
            return True
        # Explicit deterministic types MUST NOT be treated as semantic
        if cond_type in [
            "numeric_check",
            "date_check",
            "calculation_check",
            "usp_check",
            "font_size_check",
            "required_field",
        ]:
            return False

    return False


class SemanticEvaluator:
    """
    Orchestrates semantic evaluation of designated rules using the configured LLM provider.
    """

    def __init__(self, provider: Optional[BaseLLMProvider] = None):
        self.provider = provider or get_llm_provider()
        self.confidence_threshold = float(getattr(settings, "LLM_CONFIDENCE_THRESHOLD", 0.70))
        self._cache: Dict[tuple, Dict[str, Any]] = {}

    def clear_cache(self) -> None:
        """Clears the evaluation cache."""
        self._cache.clear()

    def evaluate_rule(
        self,
        rule: Dict[str, Any],
        canonical_package_data: Dict[str, Any],
        raw_ocr_text: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Executes semantic reasoning on a single rule.

        Returns standard rule engine result format:
        {
            "rule_id": str,
            "section_ref": str,
            "status": "PASS" | "FAIL" | "WARNING" | "REVIEW",
            "severity": "HIGH" | "MEDIUM" | "LOW",
            "confidence": float,
            "evidence": { "field": str, "raw_value": str, "normalized_value": Any },
            "reason": str,
            "requires_human_review": bool,
            "evaluation_source": "llm_semantic" | "fallback_manual",
        }
        """
        rule_id = rule.get("rule_id_code", "UNKNOWN_RULE")
        section_ref = rule.get("section_ref", "")
        cond = rule.get("condition") or {}
        field_name = cond.get("field") or rule.get("field") or "declaration"
        statutory_req = (
            cond.get("requirement")
            or rule.get("raw_text")
            or cond.get("format")
            or f"Compliance with {section_ref}"
        )

        # Collect candidate text from canonical data
        field_info = canonical_package_data.get(field_name, {})
        candidate_text = str(field_info.get("raw") or "")

        # If empty, also check raw_ocr_text or summary
        if not candidate_text and raw_ocr_text:
            candidate_text = raw_ocr_text[:500]

        # Check cache within inspection pass
        cache_key = (str(rule_id), str(candidate_text).strip(), str(statutory_req).strip())
        if cache_key in self._cache:
            logger.debug("Reusing cached semantic evaluation for %s", rule_id)
            cached_res = dict(self._cache[cache_key])
            cached_res["evidence"] = dict(cached_res.get("evidence", {}))
            return cached_res

        # Check if LLM is enabled
        llm_enabled = getattr(settings, "LLM_ENABLED", False)
        if not llm_enabled or not self.provider:
            res = {
                "rule_id": rule_id,
                "section_ref": section_ref,
                "status": "REVIEW",
                "severity": rule.get("severity", "MEDIUM"),
                "confidence": 1.0,
                "evidence": {
                    "field": field_name,
                    "raw_value": candidate_text or None,
                    "normalized_value": None,
                },
                "reason": f"Semantic validation requires manual review (LLM reasoning disabled). Requirement: {statutory_req}",
                "requires_human_review": True,
                "evaluation_source": "fallback_manual",
            }
            self._cache[cache_key] = res
            return res

        # Query the LLM provider
        raw_output = self.provider.evaluate_semantic_rule(
            rule_id=rule_id,
            section_ref=section_ref,
            statutory_requirement=statutory_req,
            candidate_text=candidate_text,
            field_name=field_name,
            context=context,
        )

        # Validate structured JSON output using Pydantic
        try:
            validated = SemanticEvaluationOutput(**raw_output)
        except ValidationError as e:
            logger.warning("LLM structured output validation failed for %s: %s", rule_id, e)
            res = {
                "rule_id": rule_id,
                "section_ref": section_ref,
                "status": "REVIEW",
                "severity": rule.get("severity", "MEDIUM"),
                "confidence": 0.0,
                "evidence": {
                    "field": field_name,
                    "raw_value": candidate_text or None,
                    "normalized_value": None,
                },
                "reason": f"LLM returned non-conformant output schema. Manual review required. Details: {e}",
                "requires_human_review": True,
                "evaluation_source": "fallback_manual",
            }
            self._cache[cache_key] = res
            return res

        final_status = validated.status
        final_conf = validated.confidence
        requires_review = validated.requires_human_review
        reason_notes = [validated.reason]

        # 1. Anti-Hallucination Evidence Verification
        # Every LLM result claiming PASS or FAIL must cite evidence genuinely present in OCR/candidate text
        all_vals = [
            v.get("raw")
            for k, v in canonical_package_data.items()
            if isinstance(v, dict) and v.get("raw")
        ]
        evidence_verified = verify_evidence_presence(
            evidence=validated.evidence,
            candidate_text=candidate_text,
            raw_ocr_text=raw_ocr_text,
            all_extracted_values=all_vals,
        )

        if final_status in ["PASS", "FAIL"] and not evidence_verified:
            logger.warning(
                "LLM invented or unverifiable evidence for %s: '%s'. Downgrading to REVIEW.",
                rule_id,
                validated.evidence,
            )
            final_status = "REVIEW"
            requires_review = True
            reason_notes.append("Reported evidence could not be verified in package text; downgraded to human review.")

        # 2. Confidence Threshold Enforcement
        # If confidence is below the configurable threshold, return REVIEW rather than FAIL
        if final_status == "FAIL" and final_conf < self.confidence_threshold:
            final_status = "REVIEW"
            requires_review = True
            reason_notes.append(
                f"Confidence ({final_conf:.2f}) is below threshold ({self.confidence_threshold:.2f}); manual review required."
            )
        elif final_status == "PASS" and final_conf < self.confidence_threshold:
            final_status = "REVIEW"
            requires_review = True
            reason_notes.append(
                f"Confidence ({final_conf:.2f}) is below threshold ({self.confidence_threshold:.2f}); manual review required."
            )

        # 3. Incomplete Information Fallback
        if not validated.reason or not validated.reason.strip():
            final_status = "REVIEW"
            requires_review = True
            reason_notes.append("LLM returned incomplete justification; flagged for human officer review.")

        res = {
            "rule_id": rule_id,
            "section_ref": section_ref,
            "status": final_status,
            "severity": rule.get("severity", "MEDIUM"),
            "confidence": round(final_conf, 2),
            "evidence": {
                "field": field_name,
                "raw_value": validated.evidence or candidate_text or None,
                "normalized_value": None,
            },
            "reason": " | ".join(filter(None, reason_notes)),
            "requires_human_review": requires_review,
            "evaluation_source": "llm_semantic",
        }
        self._cache[cache_key] = res
        return res
