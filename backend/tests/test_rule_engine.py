"""
Unit Tests for Legal Metrology Rule Engine & Classification logic.
Matches Step 5 test cases in 08_Rule_Engine_Dataset_Build_Instructions.md.
"""
from datetime import date
from django.test import TestCase
from apps.product_master.models import Product
from apps.rules_engine.models import Rule, RuleSource
from apps.rules_engine.evaluate import evaluate_scan
from apps.compliance.models import ComplianceCheck, Violation
from apps.compliance.history import classify_and_record


class RuleEngineTestCase(TestCase):
    def setUp(self):
        # Create Rule Source
        self.source = RuleSource.objects.create(
            notification_no="G.S.R. 202(E)",
            title="Legal Metrology (Packaged Commodities) Rules, 2011",
            published_date=date(2011, 3, 7),
        )

        # 1. Mandatory Mfg Date Rule (Repealed 2024-01-01)
        self.rule_mfg_v1 = Rule.objects.create(
            rule_id_code="PCR2011-R6-1-D-MFGDATE",
            section_ref="PC Rules 2011, Rule 6(1)(d)",
            category="general",
            condition={
                "type": "required_field",
                "field": "mfg_date",
                "exemptions": ["spare_parts_with_warranty"],
            },
            effective_from=date(2011, 1, 1),
            effective_to=date(2024, 1, 1),
            status="repealed",
            source=self.source,
        )

        # 2. Mandatory Mfg Date Rule V2 (In Force from 2024-01-01)
        self.rule_mfg_v2 = Rule.objects.create(
            rule_id_code="PCR2023-R6-1-D-MFGDATE-V2",
            section_ref="PC (Amendment) Rules 2023, Rule 6(1)(d)",
            category="general",
            condition={
                "type": "required_field",
                "field": "mfg_date",
                "exemptions": ["spare_parts_with_warranty"],
            },
            effective_from=date(2024, 1, 1),
            status="in_force",
            source=self.source,
        )
        self.rule_mfg_v1.superseded_by = self.rule_mfg_v2
        self.rule_mfg_v1.save()

        # 3. Font Size Check Rule
        self.rule_font = Rule.objects.create(
            rule_id_code="PCR-NETQTY-FONTSIZE",
            section_ref="PC Rules 2011, Rule 18",
            category="general",
            condition={
                "type": "font_size_check",
                "field": "net_quantity",
                "min_height_mm": 2.0,
                "min_height_mm_large_pack": 6.0,
                "pack_size_threshold_g": 1000,
            },
            effective_from=date(2011, 1, 1),
            status="in_force",
            source=self.source,
        )

        # 4. COO Import Rule (Physical packaging, PC Rules 2011)
        self.rule_coo_physical = Rule.objects.create(
            rule_id_code="PCR2011-R6-1-G-COO-IMPORT",
            section_ref="PC Rules 2011, Rule 6(1)(a) proviso & Rule 6(10)",
            category="import",
            condition={
                "type": "conditional_required_field",
                "field": "country_of_origin",
                "applies_if": {
                    "category": "import",
                    "channel": "physical",
                }
            },
            effective_from=date(2011, 1, 1),
            status="in_force",
            source=self.source,
        )

        # 5. COO E-commerce Rule (Digital listings, PC Amendment Rules 2026)
        self.rule_coo_ecommerce = Rule.objects.create(
            rule_id_code="PCR2026-ECOMM-COO-FILTER",
            section_ref="PC (Packaged Commodities) Amendment Rules 2026, Rule 6(10)",
            category="ecommerce",
            condition={
                "type": "conditional_required_field",
                "field": "country_of_origin",
                "applies_if": {
                    "channel": "ecommerce",
                    "category": "import"
                }
            },
            effective_from=date(2026, 1, 1),
            status="in_force",
            source=self.source,
        )

        # Test Products
        self.food_product = Product.objects.create(
            brand_name="Test Brand",
            product_name="Atta 5kg",
            category="food",
        )
        self.exempt_product = Product.objects.create(
            brand_name="AutoParts",
            product_name="Spark Plug",
            category="spare_parts_with_warranty",
        )
        self.import_product = Product.objects.create(
            brand_name="ImportBrand",
            product_name="Imported Camera",
            category="import",
        )
        from apps.accounts.models import User
        self.user = User.objects.create_user(username="test_officer", email="officer@test.com", password="password")

    def test_missing_mfg_date_flagged(self):
        """Test missing mfg_date triggers a violation for standard products."""
        fields = [{"field_type": "mrp", "value": "₹149"}]
        violations = evaluate_scan(fields, self.food_product, scan_date=date(2026, 1, 1))
        self.assertTrue(any(v["field"] == "mfg_date" for v in violations))

    def test_exempted_category_not_flagged(self):
        """Test exempted product category bypasses required_field violation."""
        fields = [{"field_type": "mrp", "value": "₹149"}]
        violations = evaluate_scan(fields, self.exempt_product, scan_date=date(2026, 1, 1))
        self.assertFalse(any(v["field"] == "mfg_date" for v in violations))

    def test_rule_versioning_respected(self):
        """Test pre-2024 scan evaluates against repealed rule V1, post-2024 against V2."""
        fields = []
        violations_pre = evaluate_scan(fields, self.food_product, scan_date=date(2022, 6, 1))
        mfg_rules_pre = [v["rule"].rule_id_code for v in violations_pre if v["field"] == "mfg_date"]
        self.assertIn("PCR2011-R6-1-D-MFGDATE", mfg_rules_pre)
        self.assertNotIn("PCR2023-R6-1-D-MFGDATE-V2", mfg_rules_pre)

        violations_post = evaluate_scan(fields, self.food_product, scan_date=date(2026, 1, 1))
        mfg_rules_post = [v["rule"].rule_id_code for v in violations_post if v["field"] == "mfg_date"]
        self.assertIn("PCR2023-R6-1-D-MFGDATE-V2", mfg_rules_post)
        self.assertNotIn("PCR2011-R6-1-D-MFGDATE", mfg_rules_post)

    def test_font_size_large_pack_threshold(self):
        """Test font size threshold increases for packages > 1000g."""
        # 1500g product with 3.0mm font size (below 6.0mm requirement)
        self.food_product.net_qty_g = 1500
        fields = [{"field_type": "net_quantity", "value": "1.5 kg", "font_size_mm": 3.0}]

        violations = evaluate_scan(fields, self.food_product, scan_date=date(2026, 1, 1))
        font_violations = [v for v in violations if v["field"] == "net_quantity" and v["violation_type"] == "font_too_small"]
        self.assertEqual(len(font_violations), 1)

    def test_first_time_vs_repeat_classification(self):
        """Test first violation returns improvement notice, repeat violation returns penalty case."""
        from apps.scans.models import Scan
        scan = Scan.objects.create(performed_by=self.user, status="processed")
        check = ComplianceCheck.objects.create(scan=scan, verdict="non_compliant", evaluated_against_rule_set_date=date.today())
        viol1 = Violation.objects.create(
            compliance_check=check,
            rule=self.rule_mfg_v2,
            description="Missing mfg date",
        )

        outcome1 = classify_and_record(self.food_product, viol1)
        self.assertEqual(outcome1, "improvement_notice")

        viol2 = Violation.objects.create(
            compliance_check=check,
            rule=self.rule_mfg_v2,
            description="Missing mfg date again",
        )
        outcome2 = classify_and_record(self.food_product, viol2)
        self.assertEqual(outcome2, "penalty_case")

    def test_ecommerce_vs_import_channel_no_double_count(self):
        """Test channel selection gates rules to prevent double counting of missing COO."""
        # Scenario A: channel="ecommerce", category="import", missing country_of_origin
        fields = [{"field_type": "mrp", "value": "₹999"}]
        violations_ecomm = evaluate_scan(fields, self.import_product, scan_date=date(2026, 1, 1), channel="ecommerce")
        coo_ecomm_rules = [v["rule"].rule_id_code for v in violations_ecomm if v["field"] == "country_of_origin"]
        self.assertEqual(len(coo_ecomm_rules), 1)
        self.assertIn("PCR2026-ECOMM-COO-FILTER", coo_ecomm_rules)
        self.assertNotIn("PCR2011-R6-1-G-COO-IMPORT", coo_ecomm_rules)

        # Scenario B: channel="physical", category="import", missing country_of_origin
        violations_phys = evaluate_scan(fields, self.import_product, scan_date=date(2026, 1, 1), channel="physical")
        coo_phys_rules = [v["rule"].rule_id_code for v in violations_phys if v["field"] == "country_of_origin"]
        self.assertEqual(len(coo_phys_rules), 1)
        self.assertIn("PCR2011-R6-1-G-COO-IMPORT", coo_phys_rules)
        self.assertNotIn("PCR2026-ECOMM-COO-FILTER", coo_phys_rules)

        # Scenario C: channel=None (default), category="import", missing country_of_origin
        violations_def = evaluate_scan(fields, self.import_product, scan_date=date(2026, 1, 1), channel=None)
        coo_def_rules = [v["rule"].rule_id_code for v in violations_def if v["field"] == "country_of_origin"]
        self.assertEqual(len(coo_def_rules), 1)
        self.assertIn("PCR2011-R6-1-G-COO-IMPORT", coo_def_rules)
        self.assertNotIn("PCR2026-ECOMM-COO-FILTER", coo_def_rules)

