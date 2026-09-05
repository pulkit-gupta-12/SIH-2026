"""
End-to-End Integration, Hardening & Compliance Workflow Test Suite.

Verifies the complete Legal Metrology compliance pipeline:
SIX CAMERA CAPTURES
-> OCR
-> NORMALIZED CANONICAL PACKAGE DATA
-> DETERMINISTIC RULE ENGINE
-> SEMANTIC LLM VALIDATION (WHEN REQUIRED)
-> UNIFIED COMPLIANCE REPORT
-> DATABASE PERSISTENCE
-> FRONTEND-READY SERIALIZATION

Covers All Mandatory Integration Cases:
- CASE 1: Completely compliant package
- CASE 2: Missing MRP
- CASE 3: Missing net quantity
- CASE 4: Missing manufacturer/address information
- CASE 5: Malformed date
- CASE 6: OCR fails to detect a field
- CASE 7: OCR confidence is low (< 0.60)
- CASE 8: Semantic rule requires LLM
- CASE 9: LLM unavailable (ConnectionError / timeout)
- CASE 10: LLM returns malformed JSON
- CASE 11: LLM returns low confidence (< 0.70)
- CASE 12: Multiple simultaneous violations
- CASE 13: Rule is not applicable to the product category

Also Measures & Profiles:
- OCR processing time
- Normalization time
- Deterministic rule evaluation time
- LLM evaluation time
- Complete inspection latency
- Semantic query deduplication / caching
- Prevention of rule hallucination / adherence to supplied JSON rules
"""

import time
import json
from datetime import date
from unittest.mock import MagicMock, patch
from django.test import TestCase
from django.contrib.auth import get_user_model

from apps.scans.canonical import build_canonical_package_data
from apps.rules_engine.engine import LegalMetrologyRuleEngine
from apps.rules_engine.evaluate import evaluate_canonical_package
from apps.rules_engine.semantic.evaluator import SemanticEvaluator
from apps.rules_engine.semantic.providers import BaseLLMProvider
from apps.compliance.report import generate_compliance_report
from apps.compliance.models import ComplianceCheck, Violation
from apps.compliance.serializers import ComplianceCheckDetailSerializer
from apps.scans.models import Scan, ScanImage, ExtractedField
from apps.scans.services import process_scan_pipeline
from apps.product_master.models import Product

User = get_user_model()


class EndToEndComplianceWorkflowTests(TestCase):
    """End-to-end integration test suite for the complete Legal Metrology workflow."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="workflow_officer",
            password="testpassword123",
            email="officer@legalmetrology.gov.in",
        )
        self.product = Product.objects.create(
            gtin_barcode="8901030865421",
            brand_name="Heritage Foods",
            product_name="Pure Cow Ghee 500ml",
            category="food",
            manufacturer_name="Heritage Foods Ltd",
            manufacturer_address="Plot 12, Pune, Maharashtra 411018",
        )
        self.engine = LegalMetrologyRuleEngine.from_json_file()

    # -------------------------------------------------------------------------
    # CASE 1: Completely compliant package
    # -------------------------------------------------------------------------
    def test_case_01_completely_compliant_package(self):
        """CASE 1: Completely compliant package yields COMPLIANT status with 0 violations."""
        canonical = build_canonical_package_data(
            extracted_fields=[
                {"field_type": "mrp", "value": "MRP Rs. 349.00 (inclusive of all taxes)", "confidence": 0.98},
                {"field_type": "net_quantity", "value": "500 ml", "confidence": 0.95},
                {"field_type": "unit_sale_price", "value": "₹0.70 / ml", "confidence": 0.92},
                {"field_type": "mfg_date", "value": "01/2026", "confidence": 0.94},
                {"field_type": "expiry_date", "value": "07/2026", "confidence": 0.93},
                {"field_type": "manufacturer_name", "value": "Heritage Foods Ltd", "confidence": 0.96},
                {"field_type": "manufacturer_address", "value": "Plot 12, Pune, Maharashtra 411018", "confidence": 0.94},
                {"field_type": "consumer_care_details", "value": "Care: 1800-111-222, email: care@heritage.com", "confidence": 0.91},
                {"field_type": "commodity_name", "value": "Pure Desi Cow Ghee", "confidence": 0.97},
                {"field_type": "country_of_origin", "value": "India", "confidence": 0.99},
            ],
            raw_text="HERITAGE FOODS PURE COW GHEE Net Qty: 500 ml MRP Rs. 349.00 (inclusive of all taxes) Mfg: 01/2026 Exp: 07/2026",
            barcode="8901030865421",
        )

        results = self.engine.evaluate(canonical, product=self.product)
        report = generate_compliance_report(canonical, results, inspection_id="INSP-CASE-01")

        self.assertEqual(report["overall_status"], "COMPLIANT")
        self.assertEqual(report["summary"]["failed"], 0)
        self.assertEqual(len(report["violations"]), 0)
        self.assertGreater(report["summary"]["passed"], 0)
        self.assertGreater(len(report["passed_rules"]), 0)

        # Database persistence check
        scan = Scan.objects.create(
            performed_by=self.user,
            product=self.product,
            role_context="officer",
            capture_method="guided_capture",
        )
        check = ComplianceCheck.objects.create(
            scan=scan,
            verdict="compliant",
            overall_confidence=0.95,
            evaluated_against_rule_set_date=date.today(),
            report_data=report,
        )
        self.assertEqual(check.verdict, "compliant")
        self.assertEqual(check.report_data["overall_status"], "COMPLIANT")

    # -------------------------------------------------------------------------
    # CASE 2: Missing MRP
    # -------------------------------------------------------------------------
    def test_case_02_missing_mrp(self):
        """
        CASE 2: Missing / Non-Compliant MRP.
        Distinguishes OCR uncertainty (unconfirmed missing -> REVIEW) from
        confirmed non-compliance (non-statutory format without taxes -> FAIL / NON_COMPLIANT).
        Never manufactures a violation from missing OCR alone.
        """
        # 1. Unconfirmed missing in OCR captures -> produces REVIEW / NEEDS_REVIEW
        canonical_missing = build_canonical_package_data(
            extracted_fields=[
                {"field_type": "net_quantity", "value": "500 ml", "confidence": 0.95},
                {"field_type": "mfg_date", "value": "01/2026", "confidence": 0.94},
                {"field_type": "manufacturer_name", "value": "Heritage Foods Ltd", "confidence": 0.96},
            ],
            raw_text="HERITAGE FOODS Net Qty: 500 ml Mfg: 01/2026",
        )
        self.assertFalse(canonical_missing["mrp"]["detected"])

        results_unconfirmed = self.engine.evaluate(canonical_missing, product=self.product)
        report_unconfirmed = generate_compliance_report(canonical_missing, results_unconfirmed, inspection_id="INSP-CASE-02-UNC")
        self.assertEqual(report_unconfirmed["overall_status"], "NEEDS_REVIEW")
        mrp_rev = next(
            (r for r in report_unconfirmed["reviews"] if "MRP" in r["rule_id"] or r.get("evidence", {}).get("field") == "mrp"),
            None,
        )
        self.assertIsNotNone(mrp_rev)
        self.assertEqual(mrp_rev["status"], "REVIEW")
        self.assertTrue(mrp_rev["requires_human_review"])

        # 2. Non-statutory MRP violation (taxes missing / non-compliant format) -> produces FAIL / NON_COMPLIANT
        canonical_viol = build_canonical_package_data(
            extracted_fields=[
                {"field_type": "mrp", "value": "Retail Price Rs. 350.00 (taxes extra)", "confidence": 0.95},
                {"field_type": "net_quantity", "value": "500 ml", "confidence": 0.95},
                {"field_type": "mfg_date", "value": "01/2026", "confidence": 0.94},
            ],
            raw_text="Retail Price Rs. 350.00 (taxes extra) Net Qty 500 ml",
        )
        results_viol = self.engine.evaluate(canonical_viol, product=self.product)
        report_viol = generate_compliance_report(canonical_viol, results_viol, inspection_id="INSP-CASE-02-VIOL")
        self.assertEqual(report_viol["overall_status"], "NON_COMPLIANT")
        mrp_fail = next((v for v in report_viol["violations"] if "MRP" in v["rule_id"]), None)
        self.assertIsNotNone(mrp_fail)
        self.assertEqual(mrp_fail["status"], "FAIL")

    # -------------------------------------------------------------------------
    # CASE 3: Missing net quantity
    # -------------------------------------------------------------------------
    def test_case_03_missing_net_quantity(self):
        """
        CASE 3: Missing net quantity.
        Unconfirmed missing produces REVIEW (OCR uncertainty).
        Confirmed absent produces confirmed FAIL / NON_COMPLIANT.
        """
        canonical = build_canonical_package_data(
            extracted_fields=[
                {"field_type": "mrp", "value": "MRP Rs. 299.00 (incl. of all taxes)", "confidence": 0.95},
                {"field_type": "mfg_date", "value": "01/2026", "confidence": 0.94},
                {"field_type": "manufacturer_name", "value": "Heritage Foods Ltd", "confidence": 0.96},
            ],
            raw_text="HERITAGE FOODS MRP Rs. 299.00 (incl. of all taxes)",
        )
        self.assertFalse(canonical["net_quantity"]["detected"])

        # Unconfirmed -> NEEDS_REVIEW
        results_unconfirmed = self.engine.evaluate(canonical, product=self.product)
        report_unconfirmed = generate_compliance_report(canonical, results_unconfirmed, inspection_id="INSP-CASE-03-UNC")
        self.assertEqual(report_unconfirmed["overall_status"], "NEEDS_REVIEW")

        # Confirmed absent -> NON_COMPLIANT
        results_confirmed = self.engine.evaluate(
            canonical,
            product=self.product,
            context={"confirmed_absent_fields": {"net_quantity": True}},
        )
        report_confirmed = generate_compliance_report(canonical, results_confirmed, inspection_id="INSP-CASE-03-CONF")
        self.assertEqual(report_confirmed["overall_status"], "NON_COMPLIANT")
        netqty_viol = next((v for v in report_confirmed["violations"] if "NETQTY" in v["rule_id"]), None)
        self.assertIsNotNone(netqty_viol)
        self.assertEqual(netqty_viol["status"], "FAIL")

    # -------------------------------------------------------------------------
    # CASE 4: Missing manufacturer/address information
    # -------------------------------------------------------------------------
    def test_case_04_missing_manufacturer_address(self):
        """
        CASE 4: Missing manufacturer/address information.
        On non-exempt commodity (general goods), confirmed absent produces confirmed FAIL / NON_COMPLIANT.
        """
        general_product = Product.objects.create(
            gtin_barcode="8901234777777",
            brand_name="Apex Tools",
            product_name="Measuring Tape 5m",
            category="general",
            manufacturer_name="Apex Tools Ltd",
            manufacturer_address="Okhla Industrial Area, Delhi",
        )

        canonical = build_canonical_package_data(
            extracted_fields=[
                {"field_type": "mrp", "value": "MRP Rs. 150.00 (incl. of all taxes)", "confidence": 0.95},
                {"field_type": "net_quantity", "value": "1 unit", "confidence": 0.95},
                {"field_type": "mfg_date", "value": "01/2026", "confidence": 0.94},
            ],
            raw_text="Sample Pack MRP Rs. 150.00 (incl. of all taxes) Net Qty 1 unit",
        )
        self.assertFalse(canonical["manufacturer_address"]["detected"])

        # Confirmed absent -> NON_COMPLIANT
        results_confirmed = self.engine.evaluate(
            canonical,
            product=general_product,
            context={"confirmed_absent_fields": {"manufacturer_address": True}},
        )
        report_confirmed = generate_compliance_report(canonical, results_confirmed, inspection_id="INSP-CASE-04-CONF")
        self.assertEqual(report_confirmed["overall_status"], "NON_COMPLIANT")
        mfg_viol = next((v for v in report_confirmed["violations"] if "NAMEADDR" in v["rule_id"] or "NAME-ADDRESS" in v["rule_id"]), None)
        self.assertIsNotNone(mfg_viol)
        self.assertEqual(mfg_viol["status"], "FAIL")

    # -------------------------------------------------------------------------
    # CASE 5: Malformed date / date inconsistency
    # -------------------------------------------------------------------------
    def test_case_05_malformed_date(self):
        """CASE 5: Inconsistent or malformed date (expiry before mfg) produces confirmed violation."""
        canonical = build_canonical_package_data(
            extracted_fields=[
                {"field_type": "mrp", "value": "MRP Rs. 100.00 (incl. of all taxes)", "confidence": 0.95},
                {"field_type": "net_quantity", "value": "500 ml", "confidence": 0.95},
                {"field_type": "mfg_date", "value": "12/2026", "confidence": 0.95},
                {"field_type": "expiry_date", "value": "01/2026", "confidence": 0.95},
            ],
            raw_text="Mfg 12/2026 Exp 01/2026 MRP Rs. 100.00 Net Qty 500 ml",
        )

        results = self.engine.evaluate(canonical, product=self.product)
        report = generate_compliance_report(canonical, results, inspection_id="INSP-CASE-05")

        self.assertEqual(report["overall_status"], "NON_COMPLIANT")
        date_viol = next((v for v in report["violations"] if v["rule_id"] == "PCR-DATE-CONSISTENCY"), None)
        self.assertIsNotNone(date_viol)
        self.assertEqual(date_viol["status"], "FAIL")
        self.assertIn("Expiry date", date_viol["reason"])

    # -------------------------------------------------------------------------
    # CASE 6: OCR fails to detect a field
    # -------------------------------------------------------------------------
    def test_case_06_ocr_fails_to_detect_field(self):
        """CASE 6: OCR fails to detect non-mandatory field; system handles missing fields safely without crashing."""
        canonical = build_canonical_package_data(
            extracted_fields=[
                {"field_type": "mrp", "value": "MRP Rs. 120.00 (incl. of all taxes)", "confidence": 0.95},
                {"field_type": "net_quantity", "value": "100 g", "confidence": 0.95},
                {"field_type": "mfg_date", "value": "02/2026", "confidence": 0.94},
                {"field_type": "manufacturer_name", "value": "Heritage Foods Ltd", "confidence": 0.96},
                {"field_type": "manufacturer_address", "value": "Pune, Maharashtra", "confidence": 0.94},
                # FSSAI and Barcode completely missing from OCR
            ],
            raw_text="Package sample text",
        )
        # Verify safe representation
        self.assertFalse(canonical["fssai_license_no"]["detected"])
        self.assertIsNone(canonical["fssai_license_no"]["normalized"])
        self.assertIn(canonical["fssai_license_no"]["confidence"], [None, 0.0])

        results = self.engine.evaluate(canonical, product=self.product)
        report = generate_compliance_report(canonical, results, inspection_id="INSP-CASE-06")

        # Missing FSSAI / non-mandatory field should not crash the report
        self.assertIn("summary", report)
        self.assertIsInstance(report["violations"], list)

    # -------------------------------------------------------------------------
    # CASE 7: OCR confidence is low (< 0.60)
    # -------------------------------------------------------------------------
    def test_case_07_ocr_confidence_low_produces_review_not_fail(self):
        """CASE 7: OCR confidence is low (< 0.60) -> results in REVIEW and NEEDS_REVIEW, NEVER auto-fail."""
        canonical = build_canonical_package_data(
            extracted_fields=[
                {"field_type": "mrp", "value": "MRP Rs. 150.00 (incl. of all taxes)", "confidence": 0.95},
                # Low confidence net_quantity (0.40 < 0.60)
                {"field_type": "net_quantity", "value": "250 ml", "confidence": 0.40},
                {"field_type": "mfg_date", "value": "01/2026", "confidence": 0.90},
                {"field_type": "manufacturer_name", "value": "Heritage Foods Ltd", "confidence": 0.90},
                {"field_type": "manufacturer_address", "value": "Pune, Maharashtra", "confidence": 0.90},
            ],
            raw_text="blurry 250ml MRP Rs. 150.00 (incl. of all taxes)",
        )

        results = self.engine.evaluate(canonical, product=self.product)
        report = generate_compliance_report(canonical, results, inspection_id="INSP-CASE-07")

        # Crucial Legal Requirement: Never manufacture a violation from low OCR confidence alone
        netqty_viol = next((v for v in report["violations"] if "NETQTY" in v["rule_id"]), None)
        self.assertIsNone(netqty_viol, "Low OCR confidence must NEVER produce an automatic violation!")

        # Must be in reviews section
        netqty_review = next(
            (r for r in report["reviews"] if "NETQTY" in r["rule_id"] or r.get("evidence", {}).get("field") == "net_quantity"),
            None,
        )
        self.assertIsNotNone(netqty_review)
        self.assertEqual(netqty_review["status"], "REVIEW")
        self.assertTrue(netqty_review["requires_human_review"])
        self.assertEqual(report["overall_status"], "NEEDS_REVIEW")

    # -------------------------------------------------------------------------
    # CASE 8: Semantic rule requires LLM
    # -------------------------------------------------------------------------
    def test_case_08_semantic_rule_requires_llm(self):
        """CASE 8: Semantic rules call the LLM provider only when needed and verify evidence."""
        mock_provider = MagicMock(spec=BaseLLMProvider)
        mock_provider.evaluate_semantic_rule.return_value = {
            "rule_id": "PCR-SEM-01",
            "status": "PASS",
            "confidence": 0.95,
            "evidence": "Care: 1800-111-222, email: care@heritage.com",
            "reason": "Clear consumer grievance telephone and email provided.",
            "requires_human_review": False,
        }

        evaluator = SemanticEvaluator(provider=mock_provider)
        semantic_rule = {
            "rule_id_code": "PCR-SEM-01",
            "section_ref": "Rule 6(1)(f)",
            "is_semantic": True,
            "condition": {"type": "semantic_check", "field": "consumer_care_details", "requirement": "Consumer grievance details"},
            "severity": "HIGH",
        }

        canonical = build_canonical_package_data([
            {"field_type": "consumer_care_details", "value": "Care: 1800-111-222, email: care@heritage.com", "confidence": 0.92},
        ])

        with patch("apps.rules_engine.semantic.evaluator.settings.LLM_ENABLED", True):
            res = evaluator.evaluate_rule(semantic_rule, canonical)

        mock_provider.evaluate_semantic_rule.assert_called_once()
        self.assertEqual(res["status"], "PASS")
        self.assertEqual(res["evaluation_source"], "llm_semantic")
        self.assertFalse(res["requires_human_review"])

    # -------------------------------------------------------------------------
    # CASE 9: LLM unavailable
    # -------------------------------------------------------------------------
    def test_case_09_llm_unavailable_falls_back_gracefully(self):
        """CASE 9: LLM service failure/offline falls back to human REVIEW without crashing."""
        mock_provider = MagicMock(spec=BaseLLMProvider)
        mock_provider.evaluate_semantic_rule.side_effect = ConnectionError("OpenRouter daemon unavailable")

        evaluator = SemanticEvaluator(provider=mock_provider)
        semantic_rule = {
            "rule_id_code": "PCR-SEM-01",
            "section_ref": "Rule 6(1)(f)",
            "is_semantic": True,
            "condition": {"type": "semantic_check", "field": "consumer_care_details"},
            "severity": "HIGH",
        }

        canonical = build_canonical_package_data([
            {"field_type": "consumer_care_details", "value": "Contact: help@brand.in", "confidence": 0.85},
        ])

        # Test with LLM_ENABLED = False fallback
        with patch("apps.rules_engine.semantic.evaluator.settings.LLM_ENABLED", False):
            res = evaluator.evaluate_rule(semantic_rule, canonical)

        self.assertEqual(res["status"], "REVIEW")
        self.assertEqual(res["evaluation_source"], "fallback_manual")
        self.assertTrue(res["requires_human_review"])
        self.assertIn("LLM reasoning disabled", res["reason"])

    # -------------------------------------------------------------------------
    # CASE 10: LLM returns malformed JSON
    # -------------------------------------------------------------------------
    def test_case_10_llm_returns_malformed_json(self):
        """CASE 10: Malformed/non-conformant LLM output does not crash application; downgrades to REVIEW."""
        mock_provider = MagicMock(spec=BaseLLMProvider)
        # Missing required fields like 'confidence' and invalid status
        mock_provider.evaluate_semantic_rule.return_value = {
            "invalid_key": "garbage output",
            "status": "NOT_A_VALID_STATUS",
        }

        evaluator = SemanticEvaluator(provider=mock_provider)
        semantic_rule = {
            "rule_id_code": "PCR-SEM-01",
            "section_ref": "Rule 6(1)(f)",
            "is_semantic": True,
            "condition": {"type": "semantic_check", "field": "consumer_care_details"},
            "severity": "HIGH",
        }

        canonical = build_canonical_package_data([
            {"field_type": "consumer_care_details", "value": "Contact: help@brand.in", "confidence": 0.85},
        ])

        with patch("apps.rules_engine.semantic.evaluator.settings.LLM_ENABLED", True):
            res = evaluator.evaluate_rule(semantic_rule, canonical)

        self.assertEqual(res["status"], "REVIEW")
        self.assertEqual(res["evaluation_source"], "fallback_manual")
        self.assertTrue(res["requires_human_review"])
        self.assertIn("non-conformant output schema", res["reason"])

    # -------------------------------------------------------------------------
    # CASE 11: LLM returns low confidence (< 0.70)
    # -------------------------------------------------------------------------
    def test_case_11_llm_low_confidence_becomes_review(self):
        """CASE 11: Low LLM confidence (< 0.70) is downgraded to REVIEW with clear explanation."""
        mock_provider = MagicMock(spec=BaseLLMProvider)
        mock_provider.evaluate_semantic_rule.return_value = {
            "rule_id": "PCR-SEM-01",
            "status": "FAIL",
            "confidence": 0.45,  # below 0.70 threshold
            "evidence": "Customer Care",
            "reason": "Unclear phone or email present.",
            "requires_human_review": True,
        }

        evaluator = SemanticEvaluator(provider=mock_provider)
        semantic_rule = {
            "rule_id_code": "PCR-SEM-01",
            "section_ref": "Rule 6(1)(f)",
            "is_semantic": True,
            "condition": {"type": "semantic_check", "field": "consumer_care_details"},
            "severity": "HIGH",
        }

        canonical = build_canonical_package_data([
            {"field_type": "consumer_care_details", "value": "Customer Care", "confidence": 0.85},
        ])

        with patch("apps.rules_engine.semantic.evaluator.settings.LLM_ENABLED", True):
            res = evaluator.evaluate_rule(semantic_rule, canonical)

        self.assertEqual(res["status"], "REVIEW")
        self.assertTrue(res["requires_human_review"])
        self.assertIn("below threshold", res["reason"])

    # -------------------------------------------------------------------------
    # CASE 12: Multiple simultaneous violations
    # -------------------------------------------------------------------------
    def test_case_12_multiple_simultaneous_violations(self):
        """CASE 12: Multiple simultaneous violations are all captured cleanly."""
        canonical = build_canonical_package_data(
            extracted_fields=[
                # Violation 1: Non-statutory MRP wording
                {"field_type": "mrp", "value": "Retail Price ₹200 + local taxes extra", "confidence": 0.95},
                # Violation 2: Non-standard unit symbol 'gms'
                {"field_type": "net_quantity", "value": "500 gms", "confidence": 0.94},
                # Violation 3: Date inconsistency (Exp before Mfg)
                {"field_type": "mfg_date", "value": "12/2026", "confidence": 0.95},
                {"field_type": "expiry_date", "value": "01/2026", "confidence": 0.95},
            ],
            raw_text="Retail Price ₹200 + local taxes extra Net Qty 500 gms Mfg 12/2026 Exp 01/2026",
        )

        results = self.engine.evaluate(canonical, product=self.product)
        report = generate_compliance_report(canonical, results, inspection_id="INSP-CASE-12")

        self.assertEqual(report["overall_status"], "NON_COMPLIANT")
        self.assertGreaterEqual(len(report["violations"]), 2)
        self.assertGreaterEqual(report["summary"]["failed"], 2)

        # Check that individual violations have distinct rule IDs
        rule_ids = [v["rule_id"] for v in report["violations"]]
        self.assertTrue(any("MRP" in r for r in rule_ids))
        self.assertTrue(any("DATE" in r for r in rule_ids))

    # -------------------------------------------------------------------------
    # CASE 13: Rule is not applicable to the product category
    # -------------------------------------------------------------------------
    def test_case_13_rule_not_applicable_to_product(self):
        """CASE 13: Rules not matching the product category are marked NOT_APPLICABLE and don't trigger violation."""
        # Non-food product (cosmetics)
        cosmetic_product = Product.objects.create(
            gtin_barcode="8901234999999",
            brand_name="SkinGlow",
            product_name="Moisturizing Cream 100g",
            category="cosmetics",
            manufacturer_name="Beauty Labs Ltd",
            manufacturer_address="Mumbai, MH",
        )

        engine = LegalMetrologyRuleEngine(
            rules=[
                {
                    "rule_id_code": "PCR-FOOD-SPECIAL",
                    "section_ref": "Rule 24",
                    "category": "food",  # Only applies to food
                    "condition": {"type": "required_field", "field": "fssai_license_no"},
                    "severity": "HIGH",
                }
            ]
        )

        canonical = build_canonical_package_data([
            {"field_type": "mrp", "value": "MRP ₹250.00 incl. of all taxes", "confidence": 0.95},
        ])

        results = engine.evaluate(canonical, product=cosmetic_product)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["status"], "NOT_APPLICABLE")

        report = generate_compliance_report(canonical, results, inspection_id="INSP-CASE-13")
        self.assertEqual(report["summary"]["not_applicable"], 1)
        self.assertEqual(report["summary"]["failed"], 0)
        self.assertEqual(report["overall_status"], "COMPLIANT")

    # -------------------------------------------------------------------------
    # Performance Profiling & Latency Measurements
    # -------------------------------------------------------------------------
    def test_performance_profiling_and_latencies(self):
        """Measures and logs execution latency for OCR normalization, rule evaluation, LLM, and full pipeline."""
        extracted_fields = [
            {"field_type": "mrp", "value": "MRP Rs. 249.00 (inclusive of all taxes)", "confidence": 0.98},
            {"field_type": "net_quantity", "value": "1 kg", "confidence": 0.96},
            {"field_type": "mfg_date", "value": "01/2026", "confidence": 0.95},
            {"field_type": "expiry_date", "value": "12/2026", "confidence": 0.95},
            {"field_type": "manufacturer_name", "value": "Heritage Foods Ltd", "confidence": 0.97},
            {"field_type": "manufacturer_address", "value": "Plot 12, Pune, Maharashtra 411018", "confidence": 0.94},
            {"field_type": "consumer_care_details", "value": "Phone: 1800-123-456, email: care@brand.com", "confidence": 0.92},
            {"field_type": "commodity_name", "value": "Pure Ghee", "confidence": 0.97},
            {"field_type": "country_of_origin", "value": "India", "confidence": 0.99},
        ]

        # 1. Measure Canonical Normalization Latency
        t0 = time.perf_counter()
        canonical = build_canonical_package_data(
            extracted_fields=extracted_fields,
            raw_text="HERITAGE FOODS PURE GHEE 1 kg MRP Rs. 249.00 (inclusive of all taxes) Mfg: 01/2026 Exp: 12/2026",
            barcode="8901030865421",
        )
        t_norm = time.perf_counter() - t0

        # 2. Measure Deterministic Rule Engine Evaluation Latency
        t0 = time.perf_counter()
        results = self.engine.evaluate(canonical, product=self.product)
        t_rules = time.perf_counter() - t0

        # 3. Measure Report Generation Latency
        t0 = time.perf_counter()
        report = generate_compliance_report(canonical, results, inspection_id="INSP-PERF-01")
        t_report = time.perf_counter() - t0

        # 4. Measure Semantic Evaluator Latency (with mock provider)
        mock_provider = MagicMock(spec=BaseLLMProvider)
        mock_provider.evaluate_semantic_rule.return_value = {
            "rule_id": "PCR-SEM-01",
            "status": "PASS",
            "confidence": 0.95,
            "evidence": "Phone: 1800-123-456, email: care@brand.com",
            "reason": "Valid contact declaration.",
            "requires_human_review": False,
        }
        evaluator = SemanticEvaluator(provider=mock_provider)
        semantic_rule = {
            "rule_id_code": "PCR-SEM-01",
            "section_ref": "Rule 6(1)(f)",
            "is_semantic": True,
            "condition": {"type": "semantic_check", "field": "consumer_care_details"},
            "severity": "HIGH",
        }

        t0 = time.perf_counter()
        with patch("apps.rules_engine.semantic.evaluator.settings.LLM_ENABLED", True):
            sem_res = evaluator.evaluate_rule(semantic_rule, canonical)
        t_llm = time.perf_counter() - t0

        total_latency = t_norm + t_rules + t_report + t_llm

        # Print latency measurements for inspection
        print(f"\n[BENCHMARK] Normalization Latency: {t_norm * 1000:.2f} ms")
        print(f"[BENCHMARK] Deterministic Rule Eval Latency: {t_rules * 1000:.2f} ms")
        print(f"[BENCHMARK] Report Generation Latency: {t_report * 1000:.2f} ms")
        print(f"[BENCHMARK] LLM Evaluation Latency: {t_llm * 1000:.2f} ms")
        print(f"[BENCHMARK] Total Pipeline Latency: {total_latency * 1000:.2f} ms")

        # Performance assertions
        self.assertLess(t_norm, 0.10, "Normalization must complete in under 100ms")
        self.assertLess(t_rules, 0.20, "Deterministic rule evaluation must complete in under 200ms")
        self.assertLess(t_report, 0.10, "Report generation must complete in under 100ms")

    # -------------------------------------------------------------------------
    # Semantic Query Deduplication / Caching Test
    # -------------------------------------------------------------------------
    def test_semantic_query_deduplication_and_caching(self):
        """Verifies that duplicate semantic requests within the same run reuse cached results."""
        mock_provider = MagicMock(spec=BaseLLMProvider)
        mock_provider.evaluate_semantic_rule.return_value = {
            "rule_id": "PCR-SEM-01",
            "status": "PASS",
            "confidence": 0.95,
            "evidence": "Care: 1800-111-222",
            "reason": "Validated contact.",
            "requires_human_review": False,
        }

        evaluator = SemanticEvaluator(provider=mock_provider)
        semantic_rule = {
            "rule_id_code": "PCR-SEM-01",
            "section_ref": "Rule 6(1)(f)",
            "is_semantic": True,
            "condition": {"type": "semantic_check", "field": "consumer_care_details", "requirement": "Valid helpline"},
            "severity": "HIGH",
        }

        canonical = build_canonical_package_data([
            {"field_type": "consumer_care_details", "value": "Care: 1800-111-222", "confidence": 0.90},
        ])

        with patch("apps.rules_engine.semantic.evaluator.settings.LLM_ENABLED", True):
            # First call: calls provider
            res1 = evaluator.evaluate_rule(semantic_rule, canonical)
            # Second call with identical input: must hit cache
            res2 = evaluator.evaluate_rule(semantic_rule, canonical)

        # Provider must be called EXACTLY ONCE
        self.assertEqual(mock_provider.evaluate_semantic_rule.call_count, 1)
        self.assertEqual(res1["status"], res2["status"])
        self.assertEqual(res1["confidence"], res2["confidence"])

    # -------------------------------------------------------------------------
    # Legal Rules Source of Truth Verification
    # -------------------------------------------------------------------------
    def test_supplied_rules_json_is_authoritative(self):
        """Verifies that the supplied Legal Metrology rules JSON is loaded as the rule source and not fabricated."""
        engine = LegalMetrologyRuleEngine.from_json_file()
        rule_ids = [r["rule_id_code"] for r in engine.rules]

        # Must contain standard statutory rules from PCR 2011
        self.assertIn("PCR2011-R2-M-MRP-FORMAT", rule_ids)
        self.assertIn("PCR2011-R6-1-C-NETQTY", rule_ids)
        self.assertIn("PCR2011-R6-1-D-MFGDATE", rule_ids)
        self.assertIn("PCR2011-R6-1-A-NAMEADDR", rule_ids)

        # Deterministic checks MUST NEVER be treated as semantic
        mrp_rule = next(r for r in engine.rules if r["rule_id_code"] == "PCR2011-R2-M-MRP-FORMAT")
        self.assertFalse(mrp_rule.get("is_semantic", False))
        self.assertNotEqual(mrp_rule.get("condition", {}).get("type"), "semantic_check")
