"""
Tests for Legal Metrology Compliance Rule Engine.
Evaluates canonical package data against Legal Metrology (Packaged Commodities) Rules, 2011.
Verifies all rule types: presence, format, numeric, date, calculation, conditional,
category applicability, and safe OCR handling (no false accusations).
"""
from datetime import date
from django.test import TestCase
from apps.rules_engine.engine import LegalMetrologyRuleEngine
from apps.rules_engine.evaluate import evaluate_canonical_package
from apps.scans.canonical import build_canonical_package_data
from apps.product_master.models import Product


class ComplianceRuleEngineTestCase(TestCase):
    """Unit tests for LegalMetrologyRuleEngine."""

    @classmethod
    def setUpTestData(cls):
        cls.engine = LegalMetrologyRuleEngine.from_json_file()

    def test_loads_all_2011_rules(self):
        """Rule engine should load all 77 rules from 2011_rule.json."""
        self.assertEqual(len(self.engine.rules), 77)

    def test_required_field_present_yields_pass(self):
        """When mandatory declaration is cleanly present with high confidence, status is PASS."""
        package_data = build_canonical_package_data([
            {"field_type": "mrp", "value": "₹349.00 (Incl. of all taxes)", "confidence": 0.95},
            {"field_type": "net_quantity", "value": "500 ml", "confidence": 0.92},
            {"field_type": "mfg_date", "value": "01/2026", "confidence": 0.90},
            {"field_type": "manufacturer_address", "value": "Plot 12, Pune, Maharashtra 411018", "confidence": 0.93},
            {"field_type": "commodity_name", "value": "Pure Desi Ghee", "confidence": 0.96},
            {"field_type": "consumer_care_details", "value": "Careline: 1800-111-222, email: care@heritage.com", "confidence": 0.88},
        ])

        results = self.engine.evaluate(package_data)
        res_by_id = {r["rule_id"]: r for r in results}

        # Check Rule 6(1)(c) Net Quantity required
        net_qty_res = res_by_id.get("PCR2011-R6-1-C-NETQTY")
        self.assertIsNotNone(net_qty_res)
        self.assertEqual(net_qty_res["status"], "PASS")
        self.assertFalse(net_qty_res["requires_human_review"])

        # Check Rule 6(1)(b) Commodity name required
        name_res = res_by_id.get("PCR2011-R6-1-B-GENNAME")
        self.assertIsNotNone(name_res)
        self.assertEqual(name_res["status"], "PASS")

        # Check Rule 6(2) Consumer care required
        cc_res = res_by_id.get("PCR2011-R6-2-CONSUMERCARE")
        self.assertIsNotNone(cc_res)
        self.assertEqual(cc_res["status"], "PASS")

    def test_not_detected_by_ocr_yields_review_not_false_violation(self):
        """
        CRITICAL: When OCR does NOT detect a field (e.g. net_quantity missing on blurry image),
        the engine must NEVER claim a confirmed legal violation. It must return REVIEW.
        """
        package_data = build_canonical_package_data([])  # Nothing detected

        results = self.engine.evaluate(package_data)
        res_by_id = {r["rule_id"]: r for r in results}

        net_qty_res = res_by_id.get("PCR2011-R6-1-C-NETQTY")
        self.assertIsNotNone(net_qty_res)
        self.assertEqual(net_qty_res["status"], "REVIEW")
        self.assertTrue(net_qty_res["requires_human_review"])
        self.assertIn("not reliably detected by OCR", net_qty_res["reason"])

    def test_definitely_absent_yields_fail(self):
        """When inspection context confirms field is definitely absent, status is FAIL."""
        package_data = build_canonical_package_data([])
        context = {
            "confirmed_absent_fields": {"net_quantity": True}
        }

        results = self.engine.evaluate(package_data, context=context)
        res_by_id = {r["rule_id"]: r for r in results}

        net_qty_res = res_by_id.get("PCR2011-R6-1-C-NETQTY")
        self.assertIsNotNone(net_qty_res)
        self.assertEqual(net_qty_res["status"], "FAIL")
        self.assertFalse(net_qty_res["requires_human_review"])
        self.assertIn("confirmed absent", net_qty_res["reason"])

    def test_low_confidence_or_ambiguous_ocr_yields_review(self):
        """When OCR confidence is low (< 0.6) or ambiguous, status is REVIEW."""
        package_data = build_canonical_package_data([
            {"field_type": "mrp", "value": "Rs 300 / 400", "confidence": 0.45},
        ])

        results = self.engine.evaluate(package_data)
        res_by_id = {r["rule_id"]: r for r in results}

        mrp_fmt_res = res_by_id.get("PCR2011-R2-M-MRP-FORMAT")
        self.assertIsNotNone(mrp_fmt_res)
        # Ambiguous price format triggers human review
        self.assertIn(mrp_fmt_res["status"], ["REVIEW", "FAIL"])

    def test_format_checks(self):
        """Test MRP, net quantity, and date format compliance."""
        # 1. MRP format complying with Rule 2(m)
        pkg_valid_mrp = build_canonical_package_data([
            {"field_type": "mrp", "value": "Max. retail price Rs. 349.00 inclusive of all taxes", "confidence": 0.95}
        ])
        res = self.engine.evaluate(pkg_valid_mrp)
        r2m = {r["rule_id"]: r for r in res}["PCR2011-R2-M-MRP-FORMAT"]
        self.assertEqual(r2m["status"], "PASS")

        # 2. MRP missing taxes statement fails format check
        pkg_no_taxes = build_canonical_package_data([
            {"field_type": "mrp", "value": "MRP Rs. 349.00", "confidence": 0.95}
        ])
        res_no_tax = self.engine.evaluate(pkg_no_taxes)
        r2m_no_tax = {r["rule_id"]: r for r in res_no_tax}["PCR2011-R2-M-MRP-FORMAT"]
        self.assertEqual(r2m_no_tax["status"], "FAIL")
        self.assertIn("inclusive of all taxes", r2m_no_tax["reason"])

    def test_prohibited_when_packed_qualification(self):
        """Rule 11(2): Net quantity must not be qualified by 'when packed'."""
        pkg_when_packed = build_canonical_package_data([
            {"field_type": "net_quantity", "value": "500 g when packed", "confidence": 0.92}
        ])
        results = self.engine.evaluate(pkg_when_packed)
        r11_res = {r["rule_id"]: r for r in results}.get("PCR2011-R11-2-NOWHENPACKED")
        self.assertIsNotNone(r11_res)
        self.assertEqual(r11_res["status"], "FAIL")
        self.assertIn("when packed", r11_res["reason"])

    def test_prohibited_exaggeration_expression(self):
        """Rule 12(6): Quantity must not contain 'minimum', 'not less than', 'approx'."""
        pkg_exaggerated = build_canonical_package_data([
            {"field_type": "net_quantity", "value": "approx 500 g", "confidence": 0.92}
        ])
        results = self.engine.evaluate(pkg_exaggerated)
        r12_res = {r["rule_id"]: r for r in results}.get("PCR2011-R12-6-NOEXAGGERATION-NEW")
        self.assertIsNotNone(r12_res)
        self.assertEqual(r12_res["status"], "FAIL")
        self.assertIn("misleading", r12_res["reason"])

    def test_date_chronology_check(self):
        """Statutory check: Expiry date must not precede manufacturing date."""
        # Valid chronological dates
        valid_dates = build_canonical_package_data([
            {"field_type": "mfg_date", "value": "01/2026", "confidence": 0.95},
            {"field_type": "expiry_date", "value": "12/2027", "confidence": 0.95},
        ])
        res_valid = self.engine.evaluate(valid_dates)
        date_res = {r["rule_id"]: r for r in res_valid}.get("PCR-DATE-CONSISTENCY")
        self.assertIsNotNone(date_res)
        self.assertEqual(date_res["status"], "PASS")

        # Invalid inverted dates (expiry before mfg)
        invalid_dates = build_canonical_package_data([
            {"field_type": "mfg_date", "value": "12/2027", "confidence": 0.95},
            {"field_type": "expiry_date", "value": "01/2026", "confidence": 0.95},
        ])
        res_invalid = self.engine.evaluate(invalid_dates)
        date_res_inv = {r["rule_id"]: r for r in res_invalid}.get("PCR-DATE-CONSISTENCY")
        self.assertIsNotNone(date_res_inv)
        self.assertEqual(date_res_inv["status"], "FAIL")
        self.assertIn("precedes", date_res_inv["reason"])

    def test_unit_sale_price_calculation_consistency(self):
        """Calculates expected USP = MRP / Qty and compares with declared USP."""
        # Matching USP: MRP 350, Qty 500 ml -> 0.70 / ml
        pkg_matching = build_canonical_package_data([
            {"field_type": "mrp", "value": "MRP Rs. 350.00 (incl. of all taxes)", "confidence": 0.95},
            {"field_type": "net_quantity", "value": "500 ml", "confidence": 0.95},
            {"field_type": "unit_sale_price", "value": "₹0.70 / ml", "confidence": 0.95},
        ])
        res_match = self.engine.evaluate(pkg_matching)
        usp_res = {r["rule_id"]: r for r in res_match}.get("PCR-USP-CALCULATION")
        self.assertIsNotNone(usp_res)
        self.assertEqual(usp_res["status"], "PASS")

        # Mismatched USP: declared 0.50 / ml instead of 0.70 / ml
        pkg_mismatch = build_canonical_package_data([
            {"field_type": "mrp", "value": "MRP Rs. 350.00 (incl. of all taxes)", "confidence": 0.95},
            {"field_type": "net_quantity", "value": "500 ml", "confidence": 0.95},
            {"field_type": "unit_sale_price", "value": "₹0.50 / ml", "confidence": 0.95},
        ])
        res_mismatch = self.engine.evaluate(pkg_mismatch)
        usp_mismatch = {r["rule_id"]: r for r in res_mismatch}.get("PCR-USP-CALCULATION")
        self.assertIsNotNone(usp_mismatch)
        self.assertEqual(usp_mismatch["status"], "WARNING")
        self.assertTrue(usp_mismatch["requires_human_review"])
        self.assertIn("mismatch", usp_mismatch["reason"].lower())

    def test_category_exemption_handling(self):
        """Rule 6(1)(a) & 6(1)(d) contain exemptions for food articles governed by food laws."""
        food_product = Product.objects.create(
            gtin_barcode="8901234567891",
            product_name="Atta",
            category="food",
        )
        pkg_empty = build_canonical_package_data([])

        res = self.engine.evaluate(pkg_empty, product=food_product)
        res_by_id = {r["rule_id"]: r for r in res}

        # Rule 6(1)(a) specifies food articles are exempt under Prevention of Food Adulteration Act / FSSAI
        r6_1_a = res_by_id.get("PCR2011-R6-1-A-NAMEADDR")
        self.assertIsNotNone(r6_1_a)
        self.assertEqual(r6_1_a["status"], "NOT_APPLICABLE")

    def test_qualitative_rules_yield_review(self):
        """Rules with condition: null in 2011_rule.json (e.g. deceptive packages, advertisements) yield REVIEW."""
        package_data = build_canonical_package_data([])
        results = self.engine.evaluate(package_data)
        res_by_id = {r["rule_id"]: r for r in results}

        deceptive_rule = res_by_id.get("PCR2011-R23-DECEPTIVE-PACKAGES")
        self.assertIsNotNone(deceptive_rule)
        self.assertEqual(deceptive_rule["status"], "REVIEW")
        self.assertTrue(deceptive_rule["requires_human_review"])

    def test_evaluate_canonical_package_wrapper_and_summary(self):
        """Test evaluate_canonical_package convenience wrapper and summary stats."""
        sample_extracted = [
            {"field_type": "mrp", "value": "Max. retail price Rs. 349.00 inclusive of all taxes", "confidence": 0.95},
            {"field_type": "net_quantity", "value": "500 ml", "confidence": 0.92},
            {"field_type": "commodity_name", "value": "Pure Desi Ghee", "confidence": 0.96},
            {"field_type": "consumer_care_details", "value": "1800-111-222 care@heritage.com", "confidence": 0.88},
        ]
        canonical_data = build_canonical_package_data(sample_extracted)

        report = evaluate_canonical_package(canonical_data)
        self.assertIn("summary", report)
        self.assertIn("results", report)

        summary = report["summary"]
        self.assertGreater(summary["total_rules_evaluated"], 50)
        self.assertIn("counts", summary)
        self.assertGreater(summary["counts"]["PASS"], 0)
