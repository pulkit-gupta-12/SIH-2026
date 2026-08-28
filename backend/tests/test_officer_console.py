"""
Automated unit tests for Phase 4.2: Field Officer Console.
Tests all 6 screens/endpoints:
1. Inspection Queue (GET /api/inspections/queue/)
2. Guided Capture (POST /api/scans/)
3. Processing Result (GET /api/scans/{id}/processing-result/)
4. Review Findings Confirm/Override (POST /api/compliance-checks/{id}/confirm|override/)
5. Violation History Timeline (GET /api/products/{id}/violation-history/)
6. Case Creation (POST /api/cases/ for Improvement Notice vs Penalty Case)
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
from apps.rules_engine.models import Rule, RuleSource

User = get_user_model()


class FieldOfficerConsoleTests(TestCase):
    def setUp(self):
        self.client = APIClient()

        # Roles
        self.officer_role, _ = Role.objects.get_or_create(name="field_officer")
        self.citizen_role, _ = Role.objects.get_or_create(name="citizen")

        # Users
        self.officer_user = User.objects.create_user(
            username="officer_test",
            password="password123",
            email="officer@test.gov.in",
            first_name="Field",
            last_name="Officer",
        )
        RoleAssignment.objects.create(user=self.officer_user, role=self.officer_role, state="DL")

        self.citizen_user = User.objects.create_user(
            username="citizen_test",
            password="password123",
            email="citizen@test.com",
        )
        RoleAssignment.objects.create(user=self.citizen_user, role=self.citizen_role)

        # Rule & Source
        self.source = RuleSource.objects.create(
            notification_no="G.S.R. OFFICER-TEST",
            title="Officer Test Source",
            published_date=date(2022, 1, 1),
        )
        self.rule_mfg = Rule.objects.create(
            rule_id_code="PCR-OFFICER-MFG",
            section_ref="Rule 6(1)(d)",
            category="general",
            condition={"type": "required_field", "field": "mfg_date"},
            effective_from=date(2022, 1, 1),
            status="in_force",
            source=self.source,
        )

        # Product 1: First-time violation
        self.product_first_time = Product.objects.create(
            gtin_barcode="8901111222233",
            brand_name="FirstBrand",
            product_name="FirstBrand Spices 100g",
            category="food",
            manufacturer_name="Spices Ltd",
            manufacturer_address="Okhla Phase 3, New Delhi",
        )

        # Product 2: Repeat violation
        self.product_repeat = Product.objects.create(
            gtin_barcode="8904444555566",
            brand_name="RepeatBrand",
            product_name="RepeatBrand Cooking Oil 1L",
            category="food",
            manufacturer_name="Oil Industries Ltd",
            manufacturer_address="Naraina, New Delhi",
        )

        # Create scan & check for Product 1 (First Time)
        self.scan1 = Scan.objects.create(
            product=self.product_first_time,
            performed_by=self.officer_user,
            role_context="officer",
            capture_method="guided_capture",
            status="processed",
        )
        self.check1 = ComplianceCheck.objects.create(
            scan=self.scan1,
            verdict="non_compliant",
            overall_confidence=0.92,
            evaluated_against_rule_set_date=date.today(),
        )
        self.viol1 = Violation.objects.create(
            compliance_check=self.check1,
            rule=self.rule_mfg,
            description="Mfg date is missing on declaration panel",
        )
        self.history1 = ProductComplianceHistory.objects.create(
            product=self.product_first_time,
            violation=self.viol1,
            is_first_time=True,
            case=None,
        )

        # Create scan & check for Product 2 (Repeat)
        self.scan2 = Scan.objects.create(
            product=self.product_repeat,
            performed_by=self.officer_user,
            role_context="officer",
            capture_method="guided_capture",
            status="processed",
        )
        self.check2 = ComplianceCheck.objects.create(
            scan=self.scan2,
            verdict="non_compliant",
            overall_confidence=0.94,
            evaluated_against_rule_set_date=date.today(),
        )
        self.viol2 = Violation.objects.create(
            compliance_check=self.check2,
            rule=self.rule_mfg,
            description="Mfg date is missing (repeat inspection)",
        )
        self.history2 = ProductComplianceHistory.objects.create(
            product=self.product_repeat,
            violation=self.viol2,
            is_first_time=False,  # Repeat violation!
            case=None,
        )

    def test_01_inspection_queue_aggregates_targets_and_citizen_complaints(self):
        """Screen 1: GET /api/inspections/queue/ returns risk-sorted targets + citizen complaints."""
        self.client.force_authenticate(user=self.officer_user)

        # Create an InspectionTarget
        InspectionTarget.objects.create(
            product=self.product_first_time,
            assigned_to=self.officer_user,
            source="risk_engine",
            priority_score=85.0,
            status="pending",
        )

        # Create an open citizen complaint
        Complaint.objects.create(
            filed_by=self.citizen_user,
            product=self.product_repeat,
            description="Missing Net Quantity and overcharging observed in store",
            location="Connaught Place, New Delhi",
            risk_score=92.0,
            routed_to_state="Delhi",
            status="open",
        )

        response = self.client.get("/api/inspections/queue/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()

        self.assertGreaterEqual(len(data), 2)
        # Should be sorted by priority score descending (92.0 complaint first, then 85.0 target)
        self.assertEqual(data[0]["priority_score"], 92.0)
        self.assertEqual(data[0]["source"], "complaint")
        self.assertEqual(data[1]["priority_score"], 85.0)

    def test_02_guided_capture_scan_creation(self):
        """Screen 2: POST /api/scans/ accepts multi-image guided capture from officer."""
        self.client.force_authenticate(user=self.officer_user)

        payload = {
            "barcode": "8901111222233",
            "category": "food",
            "capture_method": "guided_capture",
            "image_urls": [
                "http://localhost:8000/media/front_panel.jpg",
                "http://localhost:8000/media/declaration_panel.jpg",
                "http://localhost:8000/media/mrp_closeup.jpg",
            ],
            "location": "Central Delhi Supermarket",
        }

        response = self.client.post("/api/scans/", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = response.json()
        self.assertEqual(data["product"], self.product_first_time.id)
        self.assertEqual(data["role_context"], "officer")
        self.assertEqual(data["capture_method"], "guided_capture")

    def test_03_processing_result_detail(self):
        """Screen 3: GET /api/scans/{id}/processing-result/ returns extracted fields and verdict."""
        self.client.force_authenticate(user=self.officer_user)

        # Create extracted field
        ExtractedField.objects.create(
            scan=self.scan1,
            field_type="mrp",
            extracted_value="₹150.00",
            confidence_score=0.96,
            font_size_mm=2.5,
            placement_zone="declaration_panel",
        )

        response = self.client.get(f"/api/scans/{self.scan1.id}/processing-result/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()

        self.assertEqual(data["id"], self.scan1.id)
        self.assertEqual(data["status"], "processed")
        self.assertGreaterEqual(len(data["extracted_fields"]), 1)
        self.assertEqual(data["extracted_fields"][0]["field_type"], "mrp")
        self.assertIsNotNone(data["compliance_check"])

    def test_04_review_findings_confirm_and_override(self):
        """Screen 4: POST /api/compliance-checks/{id}/confirm|override/ updates officer review."""
        self.client.force_authenticate(user=self.officer_user)

        # Test Confirm
        confirm_resp = self.client.post(f"/api/compliance-checks/{self.check1.id}/confirm/")
        self.assertEqual(confirm_resp.status_code, status.HTTP_200_OK)
        self.check1.refresh_from_db()
        self.assertEqual(self.check1.reviewed_by_officer, self.officer_user)

        # Test Override
        override_resp = self.client.post(
            f"/api/compliance-checks/{self.check1.id}/override/",
            {"verdict": "compliant", "notes": "Declaration verified under secondary label."},
            format="json",
        )
        self.assertEqual(override_resp.status_code, status.HTTP_200_OK)
        self.check1.refresh_from_db()
        self.assertEqual(self.check1.verdict, "compliant")
        self.assertEqual(self.check1.reviewed_by_officer, self.officer_user)

    def test_05_product_violation_history_timeline(self):
        """Screen 5: GET /api/products/{id}/violation-history/ returns product timeline."""
        self.client.force_authenticate(user=self.officer_user)

        response = self.client.get(f"/api/products/{self.product_repeat.id}/violation-history/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()

        self.assertEqual(data["product_id"], self.product_repeat.id)
        self.assertTrue(data["has_repeat_offenses"])
        self.assertGreaterEqual(data["total_violations"], 1)
        self.assertEqual(data["history"][0]["is_first_time"], False)

    def test_06_case_creation_first_time_creates_improvement_notice_without_double_write(self):
        """Screen 6: First-time offense automatically spawns Section 29 Improvement Notice."""
        self.client.force_authenticate(user=self.officer_user)

        initial_history_count = ProductComplianceHistory.objects.count()

        payload = {
            "product": self.product_first_time.id,
            "violation": self.viol1.id,
            "rectification_days": 30,
        }

        response = self.client.post("/api/cases/", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = response.json()

        self.assertEqual(data["classification"], "first_time")
        self.assertEqual(data["status"], "notice_sent")
        self.assertIsNotNone(data["improvement_notice"])
        self.assertIsNone(data["penalty_case"])
        self.assertEqual(data["opened_by_username"], self.officer_user.username)

        # CONFIRMATION: classify_and_record() was NOT called again — history table count unchanged!
        self.assertEqual(ProductComplianceHistory.objects.count(), initial_history_count)

        # Confirm case was linked to the existing history entry
        self.history1.refresh_from_db()
        self.assertEqual(self.history1.case_id, data["id"])

    def test_07_case_creation_repeat_offense_creates_penalty_case(self):
        """Screen 6: Repeat offense automatically spawns Section 39 Penalty Case."""
        self.client.force_authenticate(user=self.officer_user)

        payload = {
            "product": self.product_repeat.id,
            "violation": self.viol2.id,
        }

        response = self.client.post("/api/cases/", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = response.json()

        self.assertEqual(data["classification"], "repeat")
        self.assertEqual(data["status"], "escalated")
        self.assertIsNotNone(data["penalty_case"])
        self.assertIsNone(data["improvement_notice"])
        self.assertEqual(data["penalty_case"]["payment_status"], "pending")

    def test_08_citizen_cannot_open_enforcement_cases_gets_403(self):
        """Permission boundary: Citizen user gets 403 Forbidden on POST /api/cases/."""
        self.client.force_authenticate(user=self.citizen_user)

        payload = {
            "product": self.product_first_time.id,
            "violation": self.viol1.id,
        }

        response = self.client.post("/api/cases/", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_09_multi_violation_check_creates_distinct_cases(self):
        """Multi-violation check: ComplianceCheck with 2+ violations produces 2+ distinct Case rows."""
        self.client.force_authenticate(user=self.officer_user)

        # Create a second rule
        rule_mrp = Rule.objects.create(
            rule_id_code="PCR-OFFICER-MRP",
            section_ref="Rule 6(1)(e)",
            category="general",
            condition={"type": "required_field", "field": "mrp"},
            effective_from=date(2022, 1, 1),
            status="in_force",
            source=self.source,
        )

        # Single check with 2 distinct violations on product_first_time
        viol_a = Violation.objects.create(
            compliance_check=self.check1,
            rule=self.rule_mfg,
            description="Violation A: Missing Mfg Date",
        )
        hist_a = ProductComplianceHistory.objects.create(
            product=self.product_first_time,
            violation=viol_a,
            is_first_time=True,
        )

        viol_b = Violation.objects.create(
            compliance_check=self.check1,
            rule=rule_mrp,
            description="Violation B: Missing MRP declaration",
        )
        hist_b = ProductComplianceHistory.objects.create(
            product=self.product_first_time,
            violation=viol_b,
            is_first_time=True,
        )

        # Create Case for Violation A
        resp_a = self.client.post("/api/cases/", {
            "product": self.product_first_time.id,
            "violation": viol_a.id,
            "rectification_days": 30,
        }, format="json")
        self.assertEqual(resp_a.status_code, status.HTTP_201_CREATED)
        case_a_id = resp_a.json()["id"]

        # Create Case for Violation B
        resp_b = self.client.post("/api/cases/", {
            "product": self.product_first_time.id,
            "violation": viol_b.id,
            "rectification_days": 30,
        }, format="json")
        self.assertEqual(resp_b.status_code, status.HTTP_201_CREATED)
        case_b_id = resp_b.json()["id"]

        # Assert two distinct case rows were created
        self.assertNotEqual(case_a_id, case_b_id)
        
        hist_a.refresh_from_db()
        hist_b.refresh_from_db()
        self.assertEqual(hist_a.case_id, case_a_id)
        self.assertEqual(hist_b.case_id, case_b_id)

