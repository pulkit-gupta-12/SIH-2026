"""
Automated unit & integration tests for Phase 5: Cross-Flow Integration Wiring.
Covers the cross-flow linkages between Citizen App (4.1), Field Officer Console (4.2),
and Rule Engine Admin Console (4.3):

1. Check 1 (Critical): Rule Admin published rule supersedes prior versions cleanly
   and is actively evaluated by Officer & Citizen scan engines across temporal boundaries.
2. Check 2: Citizen complaint filing calculates risk and appears directly in Officer's
   Inspection Queue with correct priority ranking and metadata.
3. Bonus Check: Rule Admin dashboard converges live cross-flow case, scan, and complaint metrics.
"""
from datetime import date, timedelta
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

from apps.accounts.models import Role, RoleAssignment
from apps.product_master.models import Product
from apps.scans.models import Scan, ScanImage, ExtractedField
from apps.compliance.models import ComplianceCheck, Violation, ProductComplianceHistory
from apps.cases.models import Case, ImprovementNotice, PenaltyCase
from apps.complaints.models import Complaint
from apps.inspections.models import InspectionTarget
from apps.rules_engine.models import (
    RuleSource,
    Rule,
    RuleNotification,
    RuleDraft,
    RuleSimulationResult,
)
from apps.rules_engine.evaluate import evaluate_scan

User = get_user_model()


class CrossFlowIntegrationTests(TestCase):
    def setUp(self):
        self.client = APIClient()

        # 1. Roles
        self.citizen_role, _ = Role.objects.get_or_create(name="citizen")
        self.officer_role, _ = Role.objects.get_or_create(name="field_officer")
        self.admin_role, _ = Role.objects.get_or_create(name="national_admin")

        # 2. Users
        self.citizen_user = User.objects.create_user(
            username="citizen_integration",
            password="password123",
            email="citizen@integration.com",
            first_name="Citizen",
            last_name="Tester",
        )
        RoleAssignment.objects.create(user=self.citizen_user, role=self.citizen_role)

        self.officer_user = User.objects.create_user(
            username="officer_integration",
            password="password123",
            email="officer@delhi.gov.in",
            first_name="Rajesh",
            last_name="Kumar",
        )
        RoleAssignment.objects.create(user=self.officer_user, role=self.officer_role, state="DL")

        self.admin_user = User.objects.create_user(
            username="admin_integration",
            password="password123",
            email="admin@doca.gov.in",
            first_name="Admin",
            last_name="National",
        )
        RoleAssignment.objects.create(user=self.admin_user, role=self.admin_role)

        # 3. Base Product
        self.product = Product.objects.create(
            gtin_barcode="8901234567899",
            brand_name="Heritage Foods",
            product_name="Heritage Atta 1kg",
            category="food",
            manufacturer_name="Heritage Consumer Products Ltd",
            manufacturer_address="Okhla Industrial Area, New Delhi",
        )

        # 4. Base Rule Source & Initial Live Rules
        self.source = RuleSource.objects.create(
            notification_no="G.S.R. 2011-BASE",
            title="Base Packaged Commodities Rules 2011",
            published_date=date(2011, 1, 1),
        )

        # Rule V1: Minimum font height 2.0 mm for net_quantity
        self.rule_v1_font = Rule.objects.create(
            rule_id_code="PCR-NETQTY-FONT-V1",
            section_ref="Rule 18, Table II",
            category="general",
            condition={"type": "font_size_check", "field": "net_quantity", "min_height_mm": 2.0},
            effective_from=date(2011, 1, 1),
            status="in_force",
            source=self.source,
        )

    def test_01_check1_published_rule_supersedes_cleanly_and_evaluates_temporally(self):
        """
        Check 1: Rule Admin publishes new rule (2.5mm threshold) effective 2026-04-01.
        Verify:
        - Prior rule V1 is cleanly repealed with effective_to=2026-04-01 and superseded_by=new_rule.
        - No overlapping active rules exist.
        - Scans on packages with 2.2mm font size pass prior to 2026-04-01 and fail after 2026-04-01.
        """
        self.client.force_authenticate(user=self.admin_user)

        # 1. Admin creates draft for 2.5 mm amendment
        draft = RuleDraft.objects.create(
            rule_id_code="PCR2026-NETQTY-FONT-V2",
            section_ref="PC Amendment Rules 2026, Rule 18",
            category="general",
            old_clause_text="Min height 2.0 mm",
            new_clause_text="Min height 2.5 mm for <=1000g, 6.5 mm for >1000g",
            proposed_condition={
                "type": "font_size_check",
                "field": "net_quantity",
                "min_height_mm": 2.5,
                "min_height_mm_large_pack": 6.5,
                "pack_size_threshold_g": 1000,
            },
            effective_date=date(2026, 4, 1),
            supersedes_rule=self.rule_v1_font,
            status="approved",
        )

        # 2. Admin publishes rule live
        resp_pub = self.client.post(f"/api/rules/{draft.id}/publish/", format="json")
        self.assertEqual(resp_pub.status_code, status.HTTP_201_CREATED)
        new_rule_id = resp_pub.json()["id"]

        # 3. Database verification of supersession
        self.rule_v1_font.refresh_from_db()
        self.assertEqual(self.rule_v1_font.status, "repealed")
        self.assertEqual(self.rule_v1_font.effective_to, date(2026, 4, 1))
        self.assertEqual(self.rule_v1_font.superseded_by_id, new_rule_id)

        new_rule = Rule.objects.get(pk=new_rule_id)
        self.assertEqual(new_rule.status, "in_force")
        self.assertEqual(new_rule.effective_from, date(2026, 4, 1))
        self.assertIsNone(new_rule.effective_to)

        # Confirm NO active overlapping rules on net_quantity font size
        active_font_rules = Rule.objects.filter(
            status="in_force",
            condition__type="font_size_check",
            condition__field="net_quantity",
        )
        self.assertEqual(active_font_rules.count(), 1)
        self.assertEqual(active_font_rules.first().id, new_rule_id)

        # 4. Cross-flow evaluation on 2.2 mm font package:
        extracted = [
            {"field_type": "net_quantity", "extracted_value": "1000g", "font_size_mm": 2.2},
            {"field_type": "mrp", "extracted_value": "₹85.00", "font_size_mm": 3.0},
        ]

        # Scan Date: 2026-03-15 (Pre-amendment) -> Evaluates against V1 (2.0mm) -> PASS
        v_pre = evaluate_scan(extracted, self.product, scan_date=date(2026, 3, 15))
        font_v_pre = [v for v in v_pre if v["rule"].condition.get("field") == "net_quantity" and v["rule"].condition.get("type") == "font_size_check"]
        self.assertEqual(len(font_v_pre), 0)

        # Scan Date: 2026-04-15 (Post-amendment) -> Evaluates against V2 (2.5mm) -> FAIL (1 violation)
        v_post = evaluate_scan(extracted, self.product, scan_date=date(2026, 4, 15))
        font_v_post = [v for v in v_post if v["rule"].condition.get("field") == "net_quantity" and v["rule"].condition.get("type") == "font_size_check"]
        self.assertEqual(len(font_v_post), 1)
        self.assertEqual(font_v_post[0]["rule"].id, new_rule_id)
        self.assertIn("2.2mm, below minimum required 2.5mm", font_v_post[0]["message"])

    def test_02_check2_citizen_complaint_appears_in_officer_queue(self):
        """
        Check 2: Citizen files complaint -> Appears in Officer's Inspection Queue
        with correct calculated priority score and source metadata.
        """
        # Step 1: Citizen files complaint
        self.client.force_authenticate(user=self.citizen_user)

        complaint_payload = {
            "product": self.product.id,
            "description": "Overcharging detected at local supermarket; printed MRP obscured with sticker.",
            "location": "Connaught Place, New Delhi, Delhi",
            "photo_urls": ["http://localhost:8000/media/evidence_overcharge.jpg"],
        }
        resp_file = self.client.post("/api/complaints/", complaint_payload, format="json")
        self.assertEqual(resp_file.status_code, status.HTTP_201_CREATED)
        complaint_data = resp_file.json()
        complaint_id = complaint_data["id"]

        self.assertGreaterEqual(complaint_data["risk_score"], 60.0)
        self.assertEqual(complaint_data["routed_to_state"], "Delhi")
        self.assertEqual(complaint_data["status"], "open")

        # Step 2: Officer views inspection queue
        self.client.force_authenticate(user=self.officer_user)

        # Also create a baseline low-priority inspection target
        InspectionTarget.objects.create(
            product=self.product,
            assigned_to=self.officer_user,
            source="risk_engine",
            priority_score=45.0,
            status="pending",
        )

        resp_queue = self.client.get("/api/inspections/queue/")
        self.assertEqual(resp_queue.status_code, status.HTTP_200_OK)
        queue_items = resp_queue.json()

        # Handle paginated or plain list
        items = queue_items.get("results", queue_items) if isinstance(queue_items, dict) else queue_items
        self.assertGreaterEqual(len(items), 2)

        # Confirm citizen complaint is ranked above lower-priority target
        first_item = items[0]
        self.assertEqual(first_item["source"], "complaint")
        self.assertEqual(first_item["complaint"], complaint_id)
        self.assertEqual(first_item["priority_score"], complaint_data["risk_score"])
        self.assertEqual(first_item["product_detail"]["product_name"], "Heritage Atta 1kg")

    def test_03_bonus_admin_dashboard_converges_live_cases_and_complaints(self):
        """
        Bonus Check: Rule Admin dashboard converges live case, scan, and complaint metrics.
        """
        self.client.force_authenticate(user=self.officer_user)

        # 1. Create a scan & check
        scan = Scan.objects.create(
            product=self.product,
            performed_by=self.officer_user,
            role_context="officer",
            status="processed",
        )
        check = ComplianceCheck.objects.create(
            scan=scan,
            verdict="non_compliant",
            evaluated_against_rule_set_date=date.today(),
        )
        viol = Violation.objects.create(
            compliance_check=check,
            rule=self.rule_v1_font,
            description="Net quantity declaration font height below 2.0 mm",
        )
        ProductComplianceHistory.objects.create(
            product=self.product,
            violation=viol,
            is_first_time=True,
        )

        # 2. Officer opens a Case
        resp_case = self.client.post("/api/cases/", {
            "product": self.product.id,
            "violation": viol.id,
            "rectification_days": 30,
        }, format="json")
        self.assertEqual(resp_case.status_code, status.HTTP_201_CREATED)

        # 3. Citizen files a complaint
        self.client.force_authenticate(user=self.citizen_user)
        self.client.post("/api/complaints/", {
            "product": self.product.id,
            "description": "Smudged packaging in Karol Bagh",
            "location": "Karol Bagh, New Delhi, Delhi",
        }, format="json")

        # 4. Admin queries dashboard analytics
        self.client.force_authenticate(user=self.admin_user)
        resp_admin = self.client.get("/api/rules/admin-dashboard/")
        self.assertEqual(resp_admin.status_code, status.HTTP_200_OK)
        admin_data = resp_admin.json()

        # Assert convergence
        self.assertGreaterEqual(admin_data["kpis"]["total_cases"], 1)
        self.assertGreaterEqual(admin_data["kpis"]["open_cases"], 1)
        self.assertTrue(any(item["category"] == "general" for item in admin_data["violations_by_category"]))
        self.assertTrue(any(item["region"] == "Delhi" for item in admin_data["violations_by_region"]))
        self.assertTrue(any(item["username"] == self.officer_user.username for item in admin_data["officer_performance"]))
