"""
Unit tests for the LLM Semantic-Validation Layer.

Tests cover:
1. Provider abstraction and connection failure fallback to REVIEW.
2. Structured JSON response parsing and Pydantic validation.
3. High-confidence semantic classification (PASS).
4. Non-compliant semantic declaration (FAIL).
5. Low-confidence auto-downgrade to REVIEW (< threshold).
6. Anti-hallucination verification (rejecting fabricated evidence).
7. Timeout handling gracefully converting to REVIEW.
8. Malformed JSON handling gracefully converting to REVIEW.
9. Deterministic safety (deterministic rules are never sent to LLM).
10. Disabled LLM behavior (LLM_ENABLED=false defaults to REVIEW without crashes).
"""

from unittest.mock import MagicMock, patch
import requests
from django.test import TestCase, override_settings

from apps.rules_engine.engine import LegalMetrologyRuleEngine
from apps.rules_engine.semantic.providers import OpenRouterProvider, get_llm_provider
from apps.rules_engine.semantic.evaluator import (
    SemanticEvaluator,
    verify_evidence_presence,
    is_semantic_rule,
)
from apps.scans.canonical import build_canonical_package_data


class SemanticLLMProviderTests(TestCase):
    """Tests for the OpenRouterProvider abstraction and resilience."""

    def test_01_provider_initialization_defaults(self):
        """OpenRouterProvider initializes with settings defaults."""
        provider = OpenRouterProvider()
        self.assertTrue(provider.base_url.startswith("http"))
        self.assertIn("minimax", provider.model.lower())
        self.assertGreater(provider.timeout, 0.0)

    def test_02_is_available_check(self):
        """is_available() checks if API key is configured."""
        provider = OpenRouterProvider(api_key="test_key")
        self.assertTrue(provider.is_available())

        provider_no_key = OpenRouterProvider(api_key="")
        self.assertFalse(provider_no_key.is_available())

    @patch("apps.rules_engine.semantic.providers.requests.post")
    def test_03_connection_error_returns_review(self, mock_post):
        """When OpenRouter service is unreachable, provider gracefully returns REVIEW."""
        mock_post.side_effect = requests.exceptions.ConnectionError("Connection refused")

        provider = OpenRouterProvider(api_key="test_key")
        res = provider.evaluate_semantic_rule(
            rule_id="PCR-SEM-01",
            section_ref="Rule 6(1)",
            statutory_requirement="Must indicate manufacturer",
            candidate_text="Manufactured by Heritage Foods, Pune",
            field_name="manufacturer_address",
        )

        self.assertEqual(res["status"], "REVIEW")
        self.assertEqual(res["confidence"], 0.0)
        self.assertTrue(res["requires_human_review"])
        self.assertIn("unreachable", res["reason"].lower())

    @patch("apps.rules_engine.semantic.providers.requests.post")
    def test_04_timeout_returns_review(self, mock_post):
        """When OpenRouter times out, provider returns REVIEW with timeout reason."""
        mock_post.side_effect = requests.exceptions.Timeout("Read timeout after 10s")

        provider = OpenRouterProvider(api_key="test_key", timeout=5.0)
        res = provider.evaluate_semantic_rule(
            rule_id="PCR-SEM-02",
            section_ref="Rule 6(1)",
            statutory_requirement="Must declare generic name",
            candidate_text="Pure Desi Cow Ghee",
            field_name="commodity_name",
        )

        self.assertEqual(res["status"], "REVIEW")
        self.assertTrue(res["requires_human_review"])
        self.assertIn("timed out", res["reason"].lower())

    @patch("apps.rules_engine.semantic.providers.requests.post")
    def test_05_malformed_json_returns_review(self, mock_post):
        """When LLM returns malformed JSON, provider returns REVIEW."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "choices": [{"message": {"content": "Not a JSON: I think this is compliant."}}]
        }
        mock_post.return_value = mock_resp

        provider = OpenRouterProvider(api_key="test_key")
        res = provider.evaluate_semantic_rule(
            rule_id="PCR-SEM-03",
            section_ref="Rule 6(1)",
            statutory_requirement="Requirement text",
            candidate_text="Sample text",
            field_name="field",
        )

        self.assertEqual(res["status"], "REVIEW")
        self.assertTrue(res["requires_human_review"])
        self.assertIn("invalid json", res["reason"].lower())


class SemanticEvaluatorTests(TestCase):
    """Tests for SemanticEvaluator, anti-hallucination, and confidence thresholds."""

    def setUp(self):
        self.mock_provider = MagicMock()
        self.evaluator = SemanticEvaluator(provider=self.mock_provider)
        self.evaluator.confidence_threshold = 0.70

    def test_06_evidence_presence_verification(self):
        """Anti-hallucination verification confirms evidence text actually exists in package data."""
        candidate = "Packed by Heritage Foods Ltd, Industrial Area, Pune 411018"
        raw_ocr = "Batch 101 MRP Rs 350 Packed by Heritage Foods Ltd, Industrial Area, Pune 411018"

        # Verbatim evidence
        self.assertTrue(verify_evidence_presence("Heritage Foods Ltd", candidate, raw_ocr))

        # Case-insensitive evidence
        self.assertTrue(verify_evidence_presence("heritage foods ltd", candidate, raw_ocr))

        # Hallucinated evidence not in text
        self.assertFalse(verify_evidence_presence("Nestle India Pvt Ltd", candidate, raw_ocr))

        # Empty evidence
        self.assertFalse(verify_evidence_presence("", candidate, raw_ocr))

    @override_settings(LLM_ENABLED=True)
    def test_07_valid_high_confidence_pass(self):
        """Valid LLM output with genuine evidence and high confidence produces PASS."""
        self.mock_provider.evaluate_semantic_rule.return_value = {
            "rule_id": "PCR-SEM-PASS",
            "status": "PASS",
            "confidence": 0.95,
            "evidence": "Pure Desi Ghee",
            "reason": "Text clearly declares standard commodity name.",
            "requires_human_review": False,
        }

        package_data = {
            "commodity_name": {"raw": "Pure Desi Ghee", "detected": True}
        }
        rule = {
            "rule_id_code": "PCR-SEM-PASS",
            "section_ref": "Rule 6(1)(b)",
            "is_semantic": True,
            "condition": {"field": "commodity_name"},
        }

        res = self.evaluator.evaluate_rule(rule, package_data, raw_ocr_text="Pure Desi Ghee 500ml")
        self.assertEqual(res["status"], "PASS")
        self.assertFalse(res["requires_human_review"])
        self.assertAlmostEqual(res["confidence"], 0.95, places=2)
        self.assertEqual(res["evaluation_source"], "llm_semantic")

    @override_settings(LLM_ENABLED=True)
    def test_08_valid_high_confidence_fail(self):
        """Valid LLM output detecting a non-compliant semantic declaration produces FAIL."""
        self.mock_provider.evaluate_semantic_rule.return_value = {
            "rule_id": "PCR-SEM-FAIL",
            "status": "FAIL",
            "confidence": 0.92,
            "evidence": "Customer contact: None",
            "reason": "Explicitly denies consumer care details.",
            "requires_human_review": False,
        }

        package_data = {
            "consumer_care_details": {"raw": "Customer contact: None", "detected": True}
        }
        rule = {
            "rule_id_code": "PCR-SEM-FAIL",
            "section_ref": "Rule 6(2)",
            "is_semantic": True,
            "condition": {"field": "consumer_care_details"},
        }

        res = self.evaluator.evaluate_rule(rule, package_data, raw_ocr_text="Customer contact: None")
        self.assertEqual(res["status"], "FAIL")
        self.assertFalse(res["requires_human_review"])
        self.assertEqual(res["evidence"]["raw_value"], "Customer contact: None")

    @override_settings(LLM_ENABLED=True)
    def test_09_hallucinated_evidence_downgrades_to_review(self):
        """CRITICAL: If LLM reports evidence that DOES NOT exist in OCR, downgrade to REVIEW."""
        self.mock_provider.evaluate_semantic_rule.return_value = {
            "rule_id": "PCR-SEM-HALLUCINATE",
            "status": "FAIL",
            "confidence": 0.95,
            "evidence": "FABRICATED TEXT THAT NEVER APPEARED ON PACKAGE",
            "reason": "Claiming violation based on invented evidence.",
            "requires_human_review": False,
        }

        package_data = {
            "commodity_name": {"raw": "Real Product 500g", "detected": True}
        }
        rule = {
            "rule_id_code": "PCR-SEM-HALLUCINATE",
            "section_ref": "Rule 6(1)(b)",
            "is_semantic": True,
            "condition": {"field": "commodity_name"},
        }

        res = self.evaluator.evaluate_rule(rule, package_data, raw_ocr_text="Real Product 500g")
        self.assertEqual(res["status"], "REVIEW")
        self.assertTrue(res["requires_human_review"])
        self.assertIn("could not be verified", res["reason"].lower())

    @override_settings(LLM_ENABLED=True)
    def test_10_low_confidence_downgrades_to_review(self):
        """If LLM confidence is below threshold (< 0.70), return REVIEW rather than FAIL."""
        self.mock_provider.evaluate_semantic_rule.return_value = {
            "rule_id": "PCR-SEM-LOWCONF",
            "status": "FAIL",
            "confidence": 0.55,  # Below 0.70
            "evidence": "Special Mixed Oil",
            "reason": "Uncertain whether blend conforms to generic commodity name.",
            "requires_human_review": False,
        }

        package_data = {
            "commodity_name": {"raw": "Special Mixed Oil", "detected": True}
        }
        rule = {
            "rule_id_code": "PCR-SEM-LOWCONF",
            "section_ref": "Rule 6(1)(b)",
            "is_semantic": True,
            "condition": {"field": "commodity_name"},
        }

        res = self.evaluator.evaluate_rule(rule, package_data, raw_ocr_text="Special Mixed Oil")
        self.assertEqual(res["status"], "REVIEW")
        self.assertTrue(res["requires_human_review"])
        self.assertIn("below threshold", res["reason"].lower())

    @override_settings(LLM_ENABLED=False)
    def test_11_llm_disabled_defaults_to_review(self):
        """When LLM_ENABLED=false, semantic rules return REVIEW without calling LLM."""
        package_data = {
            "commodity_name": {"raw": "Special Food", "detected": True}
        }
        rule = {
            "rule_id_code": "PCR-SEM-DISABLED",
            "section_ref": "Rule 6(1)(b)",
            "is_semantic": True,
            "condition": {"field": "commodity_name"},
        }

        res = self.evaluator.evaluate_rule(rule, package_data)
        self.assertEqual(res["status"], "REVIEW")
        self.assertTrue(res["requires_human_review"])
        self.assertEqual(res["evaluation_source"], "fallback_manual")
        self.mock_provider.evaluate_semantic_rule.assert_not_called()


class RuleEngineSemanticIntegrationTests(TestCase):
    """Tests integration of semantic evaluation inside LegalMetrologyRuleEngine."""

    def test_12_deterministic_rules_never_sent_to_llm(self):
        """Arithmetic, numeric, format, and existence checks are NEVER routed to LLM."""
        mock_provider = MagicMock()
        semantic_evaluator = SemanticEvaluator(provider=mock_provider)

        deterministic_rules = [
            {"rule_id_code": "D1", "condition": {"type": "required_field", "field": "mrp"}},
            {"rule_id_code": "D2", "condition": {"type": "numeric_check", "field": "net_quantity"}},
            {"rule_id_code": "D3", "condition": {"type": "date_check"}},
            {"rule_id_code": "D4", "condition": {"type": "calculation_check"}},
            {"rule_id_code": "D5", "condition": {"type": "font_size_check", "field": "mrp"}},
        ]

        for r in deterministic_rules:
            self.assertFalse(is_semantic_rule(r))

        engine = LegalMetrologyRuleEngine(rules=deterministic_rules, semantic_evaluator=semantic_evaluator)
        package_data = build_canonical_package_data([
            {"field_type": "mrp", "value": "₹100", "confidence": 0.95},
            {"field_type": "net_quantity", "value": "500 g", "confidence": 0.95},
        ])

        results = engine.evaluate(package_data)
        self.assertEqual(len(results), 5)
        # LLM was never called
        mock_provider.evaluate_semantic_rule.assert_not_called()

    @override_settings(LLM_ENABLED=True)
    def test_13_semantic_rule_routed_and_merged(self):
        """Rules explicitly marked as semantic are routed to LLM and integrated into results."""
        mock_provider = MagicMock()
        mock_provider.evaluate_semantic_rule.return_value = {
            "rule_id": "SEMANTIC-RULE-1",
            "status": "PASS",
            "confidence": 0.91,
            "evidence": "Refined Sunflower Oil",
            "reason": "Matches common commodity nomenclature.",
            "requires_human_review": False,
        }
        semantic_evaluator = SemanticEvaluator(provider=mock_provider)

        mixed_rules = [
            {
                "rule_id_code": "DET-1",
                "condition": {"type": "required_field", "field": "mrp"},
                "category": "general",
            },
            {
                "rule_id_code": "SEMANTIC-RULE-1",
                "is_semantic": True,
                "category": "general",
                "condition": {"type": "semantic_check", "field": "commodity_name"},
                "section_ref": "Rule 6(1)(b)",
            },
        ]

        engine = LegalMetrologyRuleEngine(rules=mixed_rules, semantic_evaluator=semantic_evaluator)
        package_data = build_canonical_package_data([
            {"field_type": "mrp", "value": "₹220", "confidence": 0.95},
            {"field_type": "commodity_name", "value": "Refined Sunflower Oil", "confidence": 0.95},
        ])

        results = engine.evaluate(package_data)
        self.assertEqual(len(results), 2)

        res_by_id = {r["rule_id"]: r for r in results}
        # Deterministic check passed
        self.assertEqual(res_by_id["DET-1"]["status"], "PASS")
        # Semantic check passed via LLM
        self.assertEqual(res_by_id["SEMANTIC-RULE-1"]["status"], "PASS")
        self.assertEqual(res_by_id["SEMANTIC-RULE-1"]["evaluation_source"], "llm_semantic")
        mock_provider.evaluate_semantic_rule.assert_called_once()
