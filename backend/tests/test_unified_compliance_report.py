"""
Tests for the Unified Compliance Report Layer.

Covers:
1. Fully compliant package -> overall_status: COMPLIANT
2. Multiple violations -> overall_status: NON_COMPLIANT
3. Uncertain OCR -> status: REVIEW, overall_status: NEEDS_REVIEW (never auto-fail)
4. LLM unavailable -> fallback to REVIEW, overall_status: NEEDS_REVIEW
5. Semantic REVIEW -> ambiguous LLM classification to REVIEW
6. Mixed PASS/FAIL/REVIEW results -> FAIL triggers NON_COMPLIANT while reviews/warnings are cleanly separated
7. Raw OCR evidence preservation across all findings and root evidence
8. Database persistence on ComplianceCheck.report_data and serialization
"""

from datetime import date
from unittest.mock import MagicMock, patch
from django.test import TestCase
from django.contrib.auth import get_user_model

from apps.scans.canonical import build_canonical_package_data
from apps.rules_engine.engine import LegalMetrologyRuleEngine
from apps.compliance.report import (
    generate_compliance_report,
    extract_package_evidence,
    _build_rule_finding,
)
from apps.compliance.models import ComplianceCheck, Violation
from apps.compliance.serializers import ComplianceCheckDetailSerializer
from apps.scans.models import Scan
from apps.scans.serializers import ComplianceCheckSerializer
from apps.product_master.models import Product

User = get_user_model()


class UnifiedComplianceReportTests(TestCase):
    """Comprehensive test suite for the unified compliance-report layer."""

    def setUp(self):
        self.engine = LegalMetrologyRuleEngine.from_json_file()
        self.user = User.objects.create_user(
            username="inspector_sharma",
            password="testpassword123",
        )
        self.product = Product.objects.create(
            gtin_barcode="8901030865421",
            brand_name="Heritage Foods",
            product_name="Pure Cow Ghee 500ml",
            category="food",
            manufacturer_name="Heritage Foods Ltd",
            manufacturer_address="Plot 12, Pune, Maharashtra 411018",
        )

    def test_01_fully_compliant_package(self):
        """Clean package with all statutory declarations yields COMPLIANT overall status."""
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
        report = generate_compliance_report(canonical, results, inspection_id="INSP-TEST-001")

        # Recommended structure assertions
        self.assertEqual(report["inspection_id"], "INSP-TEST-001")
        self.assertEqual(report["overall_status"], "COMPLIANT")
        self.assertIn("summary", report)
        self.assertIn("violations", report)
        self.assertIn("warnings", report)
        self.assertIn("reviews", report)
        self.assertIn("passed_rules", report)
        self.assertIn("evidence", report)
        self.assertIn("generated_at", report)

        # Status counts
        self.assertEqual(report["summary"]["failed"], 0)
        self.assertEqual(len(report["violations"]), 0)
        self.assertGreater(report["summary"]["passed"], 0)
        self.assertGreater(len(report["passed_rules"]), 0)

        # Raw evidence preservation
        self.assertGreater(len(report["evidence"]), 0)
        mrp_evidence = next((e for e in report["evidence"] if e["field"] == "mrp"), None)
        self.assertIsNotNone(mrp_evidence)
        self.assertIn("349.00", mrp_evidence["raw_text"])

    def test_02_multiple_violations(self):
        """Confirmed deterministic violations produce FAIL and NON_COMPLIANT overall status."""
        canonical = build_canonical_package_data(
            extracted_fields=[
                # Violation 1: Non-statutory MRP wording (no inclusive of taxes)
                {"field_type": "mrp", "value": "Retail Price ₹200 + local taxes extra", "confidence": 0.95},
                # Violation 2: Non-standard unit symbol 'gms'
                {"field_type": "net_quantity", "value": "500 gms", "confidence": 0.94},
                # Violation 3: Expiry before manufacture date
                {"field_type": "mfg_date", "value": "12/2026", "confidence": 0.95},
                {"field_type": "expiry_date", "value": "01/2026", "confidence": 0.95},
            ],
            raw_text="Product sample Retail Price ₹200 + local taxes extra 500 gms Mfg 12/2026 Exp 01/2026",
        )

        results = self.engine.evaluate(canonical, product=self.product)
        report = generate_compliance_report(canonical, results, inspection_id="INSP-VIOL-002")

        self.assertEqual(report["overall_status"], "NON_COMPLIANT")
        self.assertGreaterEqual(report["summary"]["failed"], 2)
        self.assertGreaterEqual(len(report["violations"]), 2)

        # Inspect violation structure according to specification
        for v in report["violations"]:
            self.assertIn("rule_id", v)
            self.assertIn("section_ref", v)
            self.assertIn("title", v)
            self.assertEqual(v["status"], "FAIL")
            self.assertIn(v["severity"], ["LOW", "MEDIUM", "HIGH", "CRITICAL"])
            self.assertIn("detected_value", v)
            self.assertIn("expected", v)
            self.assertIn("reason", v)
            self.assertIn("evidence", v)
            self.assertIn("raw_text", v["evidence"])
            self.assertIn("source_panel", v)
            self.assertIsInstance(v["confidence"], float)
            self.assertIn("requires_human_review", v)

        # Check date consistency violation
        date_viol = next((v for v in report["violations"] if v["rule_id"] == "PCR-DATE-CONSISTENCY"), None)
        self.assertIsNotNone(date_viol)
        self.assertIn("Expiry date", date_viol["reason"])

    def test_03_uncertain_ocr_produces_review_never_fail(self):
        """Uncertain OCR or low confidence MUST yield status REVIEW, not FAIL."""
        # Low confidence OCR for net quantity (0.42 < 0.60)
        canonical = build_canonical_package_data(
            extracted_fields=[
                {"field_type": "mrp", "value": "MRP ₹150.00 incl. of all taxes", "confidence": 0.95},
                {"field_type": "net_quantity", "value": "250 ml", "confidence": 0.42},
                {"field_type": "mfg_date", "value": "01/2026", "confidence": 0.90},
            ],
            raw_text="MRP ₹150.00 incl. of all taxes ... blurry 250ml",
        )

        results = self.engine.evaluate(canonical, product=self.product)
        report = generate_compliance_report(canonical, results, inspection_id="INSP-UNCERTAIN-003")

        # The net quantity check must be in reviews, NOT in violations
        net_qty_viol = next((v for v in report["violations"] if "NETQTY" in v["rule_id"]), None)
        self.assertIsNone(net_qty_viol, "Uncertain OCR must never produce an automatic violation!")

        net_qty_rev = next((r for r in report["reviews"] if "NETQTY" in r["rule_id"] or r.get("evidence", {}).get("field") == "net_quantity"), None)
        self.assertIsNotNone(net_qty_rev)
        self.assertEqual(net_qty_rev["status"], "REVIEW")
        self.assertTrue(net_qty_rev["requires_human_review"])
        self.assertIn("confidence", net_qty_rev["reason"].lower())

        # Overall status must be NEEDS_REVIEW (not NON_COMPLIANT)
        self.assertEqual(report["overall_status"], "NEEDS_REVIEW")

    def test_04_llm_unavailable_falls_back_to_review(self):
        """When LLM is unavailable or fails, semantic rules gracefully become REVIEW."""
        canonical = build_canonical_package_data([
            {"field_type": "mrp", "value": "MRP ₹100.00 incl. of all taxes", "confidence": 0.95},
            {"field_type": "net_quantity", "value": "100 g", "confidence": 0.95},
            {"field_type": "consumer_care_details", "value": "Ambiguous contact note", "confidence": 0.85},
        ])

        # Mock LLM provider raise ConnectionError
        with patch("apps.rules_engine.semantic.evaluator.get_llm_provider") as mock_get_p:
            mock_provider = MagicMock()
            mock_provider.evaluate_semantic_rule.side_effect = ConnectionError("Ollama connection failed")
            mock_get_p.return_value = mock_provider

            engine = LegalMetrologyRuleEngine.from_json_file()
            results = engine.evaluate(canonical, product=self.product)
            report = generate_compliance_report(canonical, results, inspection_id="INSP-LLM-OFFLINE-004")

            # Deterministic rules evaluate normally
            self.assertGreater(report["summary"]["passed"], 0)

            # Semantic review is recorded
            sem_rev = next((r for r in report["reviews"] if r.get("evaluation_source") == "semantic_llm"), None)
            if sem_rev:
                self.assertEqual(sem_rev["status"], "REVIEW")
                self.assertTrue(sem_rev["requires_human_review"])

            self.assertEqual(report["overall_status"], "NEEDS_REVIEW")

    def test_05_semantic_review_via_llm_downgrade(self):
        """LLM producing low-confidence or unverified result is downgraded to REVIEW."""
        synthetic_results = [
            {
                "rule_id": "PCR-SEM-01",
                "section_ref": "Rule 6(1)(f)",
                "title": "Consumer Care Verification",
                "status": "REVIEW",
                "severity": "HIGH",
                "confidence": 0.55,
                "detected_value": "Vague helpline text",
                "expected": "Clear contact info with telephone/email",
                "reason": "Model confidence is below threshold (0.55 < 0.70). Officer verification required.",
                "evidence": {"field": "consumer_care_details", "raw_text": "Vague helpline text"},
                "requires_human_review": True,
                "evaluation_source": "semantic_llm",
            },
            {
                "rule_id": "PCR2011-R6-1-C-NETQTY",
                "section_ref": "Rule 6(1)(c)",
                "title": "Net Quantity Requirement",
                "status": "PASS",
                "severity": "HIGH",
                "confidence": 0.95,
                "detected_value": "500 ml",
                "expected": "Mandatory declaration of net quantity",
                "reason": "Mandatory declaration net_quantity is present with value '500 ml'.",
                "evidence": {"field": "net_quantity", "raw_text": "500 ml"},
                "requires_human_review": False,
                "evaluation_source": "deterministic",
            }
        ]

        canonical = build_canonical_package_data([
            {"field_type": "net_quantity", "value": "500 ml", "confidence": 0.95},
            {"field_type": "consumer_care_details", "value": "Vague helpline text", "confidence": 0.80},
        ])

        report = generate_compliance_report(canonical, synthetic_results, inspection_id="INSP-SEM-005")

        self.assertEqual(report["overall_status"], "NEEDS_REVIEW")
        self.assertEqual(report["summary"]["failed"], 0)
        self.assertEqual(report["summary"]["review_required"], 1)
        self.assertEqual(report["summary"]["passed"], 1)
        self.assertEqual(len(report["violations"]), 0)
        self.assertEqual(len(report["reviews"]), 1)

    def test_06_mixed_pass_fail_review_results(self):
        """In mixed results, FAIL results in NON_COMPLIANT while reviews and warnings are preserved."""
        synthetic_results = [
            # Passing rule
            {
                "rule_id": "PCR2011-R6-1-B-GENERIC-NAME",
                "section_ref": "Rule 6(1)(b)",
                "status": "PASS",
                "severity": "MEDIUM",
                "confidence": 0.96,
                "evidence": {"field": "commodity_name", "raw_value": "Pure Ghee"},
                "reason": "Commodity name declared.",
                "requires_human_review": False,
            },
            # Confirmed deterministic failure
            {
                "rule_id": "PCR2011-R2-M-MRP-FORMAT",
                "section_ref": "Rule 2(m)",
                "status": "FAIL",
                "severity": "HIGH",
                "confidence": 0.95,
                "evidence": {"field": "mrp", "raw_value": "Rs 200 plus tax"},
                "reason": "MRP does not state inclusive of all taxes.",
                "requires_human_review": False,
            },
            # Review required item
            {
                "rule_id": "PCR-SEM-01",
                "section_ref": "Rule 6(1)(f)",
                "status": "REVIEW",
                "severity": "MEDIUM",
                "confidence": 0.50,
                "evidence": {"field": "consumer_care_details", "raw_value": "Call factory"},
                "reason": "Uncertain contact statement.",
                "requires_human_review": True,
            },
            # Warning item (should NOT turn into violation)
            {
                "rule_id": "PCR2011-R8-DECLARATION-PROMINENCE",
                "section_ref": "Rule 8",
                "status": "WARNING",
                "severity": "LOW",
                "confidence": 0.88,
                "evidence": {"field": "general", "raw_value": "Contrast is moderate"},
                "reason": "Text contrast is sub-optimal but legible.",
                "requires_human_review": False,
            },
        ]

        canonical = build_canonical_package_data([
            {"field_type": "commodity_name", "value": "Pure Ghee", "confidence": 0.96},
            {"field_type": "mrp", "value": "Rs 200 plus tax", "confidence": 0.95},
        ])

        report = generate_compliance_report(canonical, synthetic_results, inspection_id="INSP-MIXED-006")

        # FAIL dictates overall status
        self.assertEqual(report["overall_status"], "NON_COMPLIANT")
        self.assertEqual(report["summary"]["passed"], 1)
        self.assertEqual(report["summary"]["failed"], 1)
        self.assertEqual(report["summary"]["warnings"], 1)
        self.assertEqual(report["summary"]["review_required"], 1)

        # Warning is not in violations
        self.assertEqual(len(report["violations"]), 1)
        self.assertEqual(report["violations"][0]["rule_id"], "PCR2011-R2-M-MRP-FORMAT")
        self.assertEqual(len(report["warnings"]), 1)
        self.assertEqual(report["warnings"][0]["rule_id"], "PCR2011-R8-DECLARATION-PROMINENCE")
        self.assertEqual(len(report["reviews"]), 1)
        self.assertEqual(report["reviews"][0]["rule_id"], "PCR-SEM-01")

    def test_07_never_discard_raw_ocr_evidence(self):
        """Verifies raw OCR text and source panel are preserved in evidence and findings."""
        raw_stream = "BRAND NEW HERITAGE GHEE 500ml ₹349.00 INCL OF TAXES"
        canonical = build_canonical_package_data(
            extracted_fields=[
                {
                    "field_type": "mrp",
                    "value": "₹349.00 INCL OF TAXES",
                    "confidence": 0.92,
                    "source_panel": "mandatory_declaration",
                    "bbox": [10, 20, 100, 50],
                },
            ],
            raw_text=raw_stream,
        )

        results = self.engine.evaluate(canonical, product=self.product)
        report = generate_compliance_report(canonical, results, inspection_id="INSP-EVIDENCE-007")

        # Root evidence contains both field items and raw OCR stream
        field_ev = next((e for e in report["evidence"] if e["field"] == "mrp"), None)
        self.assertIsNotNone(field_ev)
        self.assertEqual(field_ev["raw_text"], "₹349.00 INCL OF TAXES")
        self.assertEqual(field_ev["source_panel"], "mandatory_declaration")
        self.assertEqual(field_ev["bounding_box"], [10, 20, 100, 50])

        stream_ev = next((e for e in report["evidence"] if e["field"] == "_raw_ocr_stream"), None)
        self.assertIsNotNone(stream_ev)
        self.assertEqual(stream_ev["raw_text"], raw_stream)

    def test_08_database_persistence_and_serialization(self):
        """Verifies report_data stores on ComplianceCheck and serializes properly."""
        scan = Scan.objects.create(
            performed_by=self.user,
            role_context="officer",
            product=self.product,
            status="processed",
        )

        canonical = build_canonical_package_data([
            {"field_type": "mrp", "value": "MRP ₹349.00 incl. of all taxes", "confidence": 0.95},
            {"field_type": "net_quantity", "value": "500 ml", "confidence": 0.95},
        ])
        results = self.engine.evaluate(canonical, product=self.product)
        report = generate_compliance_report(canonical, results, scan=scan)

        check = ComplianceCheck.objects.create(
            scan=scan,
            verdict="compliant",
            overall_confidence=0.95,
            evaluated_against_rule_set_date=date.today(),
            report_data=report,
        )

        # Retrieve from DB
        fresh_check = ComplianceCheck.objects.get(id=check.id)
        self.assertIsInstance(fresh_check.report_data, dict)
        self.assertEqual(fresh_check.report_data["inspection_id"], f"INSP-{scan.id}")
        self.assertEqual(fresh_check.report_data["overall_status"], report["overall_status"])
        self.assertEqual(fresh_check.report_data["summary"]["total_rules"], report["summary"]["total_rules"])

        # Test Scan's ComplianceCheckSerializer
        scan_check_serializer = ComplianceCheckSerializer(fresh_check)
        self.assertIn("report_data", scan_check_serializer.data)
        self.assertEqual(scan_check_serializer.data["report_data"]["inspection_id"], f"INSP-{scan.id}")

        # Test Compliance's ComplianceCheckDetailSerializer
        detail_serializer = ComplianceCheckDetailSerializer(fresh_check)
        self.assertIn("report_data", detail_serializer.data)
        self.assertEqual(detail_serializer.data["report_data"]["overall_status"], report["overall_status"])
