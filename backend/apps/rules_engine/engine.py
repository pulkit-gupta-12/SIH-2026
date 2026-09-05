"""
Legal Metrology Compliance Rule Engine.

Evaluates canonical package data against the Legal Metrology (Packaged Commodities) Rules, 2011.
Source of Truth: backend/apps/rules_engine/2011_rule.json & active Rule database models.
"""

import os
import json
import logging
import concurrent.futures
from datetime import date, datetime
from typing import Any, Dict, List, Optional, Union

from .evaluators import (
    evaluate_required_field,
    evaluate_format,
    evaluate_numeric,
    evaluate_date,
    evaluate_calculation,
    evaluate_conditional,
    evaluate_placement,
    evaluate_font_size,
    evaluate_qualitative_manual,
)
from .semantic.evaluator import SemanticEvaluator, is_semantic_rule

logger = logging.getLogger(__name__)

# Default paths to the statutory rules JSON files (2011 and 2026)
DEFAULT_2011_RULES_PATH = os.path.join(os.path.dirname(__file__), "2011_rules.json")
if not os.path.exists(DEFAULT_2011_RULES_PATH):
    DEFAULT_2011_RULES_PATH = os.path.join(os.path.dirname(__file__), "2011_rule.json")

DEFAULT_2026_RULES_PATH = os.path.join(os.path.dirname(__file__), "2026_rules.json")



# Natural language / description mapping to canonical package field keys
FIELD_MAPPING = {
    # MRP
    "mrp": "mrp",
    "retail sale price": "mrp",
    "retail price": "mrp",
    "maximum retail price": "mrp",
    "price": "mrp",

    # Net Quantity
    "net_quantity": "net_quantity",
    "net quantity": "net_quantity",
    "net quantity (in standard unit of weight, measure, or number)": "net_quantity",
    "declaration of quantity": "net_quantity",
    "declaration of quantity for specific commodities": "net_quantity",
    "quantity": "net_quantity",

    # Dates
    "mfg_date": "mfg_date",
    "month and year in which the commodity is manufactured or pre-packed or imported": "mfg_date",
    "month and year": "mfg_date",
    "expiry_date": "expiry_date",
    "best_before_date": "best_before_date",

    # Manufacturer & Address
    "name and address of the manufacturer, packer, or importer": "manufacturer_address",
    "complete address of the manufacturer, packer, or importer": "manufacturer_address",
    "manufacturer_address": "manufacturer_address",
    "manufacturer_name": "manufacturer_name",
    "name of manufacturer, packer, or importer": "manufacturer_name",

    # Consumer Care
    "consumer_care_details": "consumer_care_details",
    "name, address, telephone number, e mail address, if available, of the person who can be or the office which can be, contacted, in case of consumer complaints": "consumer_care_details",
    "consumer complaints": "consumer_care_details",

    # Commodity / Product Name
    "commodity_name": "commodity_name",
    "product_name": "commodity_name",
    "common or generic names of the commodity (and name and number/quantity of each product if multiple)": "commodity_name",
    "generic name": "commodity_name",

    # Others
    "unit_sale_price": "unit_sale_price",
    "country_of_origin": "country_of_origin",
    "fssai_license_no": "fssai_license_no",
    "batch_number": "batch_number",
    "barcode": "barcode",
}


class LegalMetrologyRuleEngine:
    """
    Compliance evaluation engine for Legal Metrology Packaged Commodities Rules.
    Uses only 2011_rules.json and 2026_rules.json (does not use seed_rules.json).
    """

    def __init__(
        self,
        rules: Optional[List[Dict[str, Any]]] = None,
        semantic_evaluator: Optional[SemanticEvaluator] = None,
    ):
        self.rules: List[Dict[str, Any]] = rules or []
        self.semantic_evaluator = semantic_evaluator or SemanticEvaluator()

    @classmethod
    def from_json_file(
        cls,
        filepath: Optional[str] = None,
        semantic_evaluator: Optional[SemanticEvaluator] = None,
        include_2026: bool = False,
    ) -> "LegalMetrologyRuleEngine":
        """
        Loads rules from JSON files:
        Uses 2011_rules.json (or 2011_rule.json), and optionally 2026_rules.json.
        Does NOT use seed_rules.json.
        """
        target_path = filepath or DEFAULT_2011_RULES_PATH
        all_rules = []
        if os.path.exists(target_path):
            with open(target_path, "r", encoding="utf-8") as f:
                all_rules.extend(json.load(f))
        else:
            logger.warning("Rules JSON not found at: %s", target_path)

        # Also load 2026_rules.json when explicitly requested or configured
        if include_2026 and not filepath and os.path.exists(DEFAULT_2026_RULES_PATH):
            try:
                with open(DEFAULT_2026_RULES_PATH, "r", encoding="utf-8") as f:
                    r26 = json.load(f)
                    for r in r26:
                        # Normalize field names for engine consumption
                        if "section_ref" not in r and "source_section" in r:
                            r["section_ref"] = r["source_section"]
                        if isinstance(r.get("category"), list) and r["category"]:
                            r["category"] = r["category"][0]
                    all_rules.extend(r26)
            except Exception as e:
                logger.warning("Failed to load 2026_rules.json: %s", e)

        return cls(all_rules, semantic_evaluator=semantic_evaluator)

    @classmethod
    def from_all_statutory_rules(
        cls,
        semantic_evaluator: Optional[SemanticEvaluator] = None,
    ) -> "LegalMetrologyRuleEngine":
        """Loads both 2011_rules.json and 2026_rules.json combined."""
        return cls.from_json_file(include_2026=True, semantic_evaluator=semantic_evaluator)

    @classmethod
    def from_db(
        cls,
        scan_date: Optional[date] = None,
        category: Optional[str] = None,
        semantic_evaluator: Optional[SemanticEvaluator] = None,
    ) -> "LegalMetrologyRuleEngine":
        """Loads rules from the Django Rule model table."""
        from django.db.models import Q
        from .models import Rule

        eval_date = scan_date or date.today()
        cat = category or "general"

        qs = Rule.objects.filter(
            category__in=[cat, "general", "ecommerce"],
            effective_from__lte=eval_date,
        ).filter(
            Q(effective_to__isnull=True) | Q(effective_to__gt=eval_date)
        )

        db_rules = []
        for r in qs:
            db_rules.append({
                "rule_id_code": r.rule_id_code,
                "section_ref": r.section_ref,
                "category": r.category,
                "condition": r.condition,
                "effective_from": str(r.effective_from),
                "effective_to": str(r.effective_to) if r.effective_to else None,
                "status": r.status,
                "raw_text": getattr(r, "raw_text", ""),
            })

        return cls(db_rules, semantic_evaluator=semantic_evaluator)

    def resolve_field(self, field_str: str) -> str:
        """Maps natural language rule field description to canonical package key."""
        if not field_str:
            return "general"
        clean = field_str.lower().strip()
        return FIELD_MAPPING.get(clean, clean)

    def is_rule_applicable(
        self,
        rule: Dict[str, Any],
        product_category: str,
        scan_date: date,
        channel: str = "physical",
    ) -> bool:
        """
        Validates whether a rule is applicable to the product category,
        channel, and scan date.
        """
        # Category applicability
        rule_cat = rule.get("category", "general")
        if isinstance(rule_cat, list):
            cats = rule_cat
        else:
            cats = [rule_cat]

        if not any(c in ["general", product_category, channel] for c in cats):
            return False

        # Effective date validation
        eff_from = rule.get("effective_from")
        if eff_from:
            try:
                from_date = datetime.strptime(eff_from[:10], "%Y-%m-%d").date()
                if scan_date < from_date:
                    return False
            except ValueError:
                pass

        eff_to = rule.get("effective_to")
        if eff_to:
            try:
                to_date = datetime.strptime(eff_to[:10], "%Y-%m-%d").date()
                if scan_date >= to_date:
                    return False
            except ValueError:
                pass

        # Check withdrawn / repealed status
        status = rule.get("status_in_this_source_version") or rule.get("status")
        if status in ["withdrawn", "repealed"]:
            return False

        return True

    def evaluate(
        self,
        canonical_package_data: Dict[str, Any],
        product: Any = None,
        scan_date: Optional[date] = None,
        channel: str = "physical",
        context: Optional[Dict[str, Any]] = None,
        raw_ocr_text: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Evaluates canonical package data against the loaded Legal Metrology rules.

        Returns: List of structured rule evaluation results.
        """
        eval_date = scan_date or date.today()
        prod_cat = getattr(product, "category", None) or (context.get("category") if context else "general")
        eval_context = {
            "channel": channel,
            "category": prod_cat,
            **(context or {}),
        }
        raw_ocr = raw_ocr_text or canonical_package_data.get("_meta", {}).get("raw_text")

        results: List[Dict[str, Any]] = []

        # If rules list is empty, default to loading 2011_rule.json
        rules_to_eval = self.rules
        if not rules_to_eval:
            engine_2011 = LegalMetrologyRuleEngine.from_json_file(semantic_evaluator=self.semantic_evaluator)
            rules_to_eval = engine_2011.rules

        semantic_rules_to_eval = []
        for rule in rules_to_eval:
            rule_id = rule.get("rule_id_code", "UNKNOWN_RULE")

            # 1. Applicability Check
            if not self.is_rule_applicable(rule, prod_cat, eval_date, channel):
                results.append({
                    "rule_id": rule_id,
                    "section_ref": rule.get("section_ref", ""),
                    "status": "NOT_APPLICABLE",
                    "severity": "LOW",
                    "confidence": 1.0,
                    "evidence": {
                        "field": "category",
                        "raw_value": prod_cat,
                        "normalized_value": None,
                    },
                    "reason": f"Rule {rule_id} is not applicable to category '{prod_cat}' on date {eval_date}.",
                    "requires_human_review": False,
                })
                continue

            # 2. Semantic Evaluation Check - Queue for parallel execution
            # Only rules explicitly marked as semantic/LLM-required are routed to SemanticEvaluator
            if is_semantic_rule(rule):
                semantic_rules_to_eval.append(rule)
                continue

            cond = rule.get("condition")

            # 3. Qualitative / Administrative Rules (no structured condition)
            if not cond or not isinstance(cond, dict):
                res = evaluate_qualitative_manual(rule, canonical_package_data, product, eval_context)
                res["section_ref"] = rule.get("section_ref", "")
                results.append(res)
                continue


            cond_type = cond.get("type", "")
            field_name_raw = cond.get("field", "")
            resolved_key = self.resolve_field(field_name_raw)
            field_data = canonical_package_data.get(resolved_key, {})

            # 3. Dispatch to Specific Evaluators
            if cond_type == "required_field":
                res = evaluate_required_field(rule, resolved_key, field_data, product, eval_context)
            elif cond_type == "format_check":
                res = evaluate_format(rule, resolved_key, field_data, product, eval_context)
            elif cond_type == "numeric_check":
                res = evaluate_numeric(rule, resolved_key, field_data, product, eval_context)
            elif cond_type == "date_check":
                res = evaluate_date(rule, canonical_package_data, product, eval_context)
            elif cond_type == "font_size_check":
                res = evaluate_font_size(rule, resolved_key, field_data, product, eval_context)
            elif cond_type == "placement_check":
                res = evaluate_placement(rule, resolved_key, field_data, product, eval_context)
            elif cond_type == "conditional_required_field":
                res = evaluate_conditional(rule, resolved_key, field_data, product, eval_context)
            elif cond_type in ["calculation_check", "usp_check"]:
                res = evaluate_calculation(rule, canonical_package_data, product, eval_context)
            else:
                # Unknown condition type
                res = evaluate_qualitative_manual(rule, canonical_package_data, product, eval_context)

            res["section_ref"] = rule.get("section_ref", "")
            results.append(res)

        # 3.5 Evaluate semantic rules concurrently
        if semantic_rules_to_eval:
            def evaluate_single(rule):
                res = self.semantic_evaluator.evaluate_rule(
                    rule=rule,
                    canonical_package_data=canonical_package_data,
                    raw_ocr_text=raw_ocr,
                    context=eval_context,
                )
                res["section_ref"] = rule.get("section_ref", "")
                return res

            with concurrent.futures.ThreadPoolExecutor(max_workers=min(10, len(semantic_rules_to_eval))) as executor:
                futures = [executor.submit(evaluate_single, r) for r in semantic_rules_to_eval]
                for future in concurrent.futures.as_completed(futures):
                    try:
                        results.append(future.result())
                    except Exception as e:
                        logger.error("Semantic evaluation failed: %s", e)

        # 4. Built-in statutory cross-field consistency checks
        # Expiry vs Mfg Date check (if both declared)
        if canonical_package_data.get("mfg_date", {}).get("detected") and canonical_package_data.get("expiry_date", {}).get("detected"):
            date_res = evaluate_date(
                {"rule_id_code": "PCR-DATE-CONSISTENCY", "section_ref": "PC Rules 2011, Rule 6(1)(d)"},
                canonical_package_data,
                product,
                eval_context
            )
            date_res["section_ref"] = "PC Rules 2011, Rule 6(1)(d)"
            results.append(date_res)

        # Unit Sale Price Calculation Check (if USP is declared)
        if canonical_package_data.get("unit_sale_price", {}).get("detected"):
            usp_calc_res = evaluate_calculation(
                {"rule_id_code": "PCR-USP-CALCULATION", "section_ref": "PC (Second Amendment) Rules 2021, Rule 6(1)(e)"},
                canonical_package_data,
                product,
                eval_context
            )
            usp_calc_res["section_ref"] = "PC (Second Amendment) Rules 2021, Rule 6(1)(e)"
            results.append(usp_calc_res)

        return results

    @staticmethod
    def summarize_results(results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Aggregates rule evaluation results into counts and overall verdict.
        """
        counts = {
            "PASS": 0,
            "FAIL": 0,
            "WARNING": 0,
            "REVIEW": 0,
            "NOT_APPLICABLE": 0,
        }
        violations = []
        reviews_needed = []

        for r in results:
            st = r.get("status", "REVIEW")
            counts[st] = counts.get(st, 0) + 1

            if st == "FAIL":
                violations.append(r)
            elif st in ["REVIEW", "WARNING"] and r.get("requires_human_review"):
                reviews_needed.append(r)

        if counts["FAIL"] > 0:
            overall_verdict = "non_compliant"
        elif counts["REVIEW"] > 0:
            overall_verdict = "needs_review"
        else:
            overall_verdict = "compliant"

        return {
            "overall_verdict": overall_verdict,
            "counts": counts,
            "violations": violations,
            "reviews_needed": reviews_needed,
            "total_rules_evaluated": len(results),
        }
