"""
Automated unit tests for Phase 4.1: Citizen App.
Tests all 5 endpoints, skip-rescan vs first-scan behavior, permission boundaries, and history recording.
"""
from datetime import date
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

from apps.accounts.models import Role, RoleAssignment
from apps.product_master.models import Product
from apps.scans.models import Scan, ScanImage
from apps.compliance.models import ComplianceCheck, Violation, ProductComplianceHistory
from apps.complaints.models import Complaint
from apps.cases.models import Case
from apps.rules_engine.models import Rule, RuleSource

User = get_user_model()


class CitizenAppTests(TestCase):
    def setUp(self):
        self.client = APIClient()

        # 1. Create Roles
        self.citizen_role, _ = Role.objects.get_or_create(name="citizen")
        self.officer_role, _ = Role.objects.get_or_create(name="field_officer")

        # 2. Create Users
        self.citizen_user = User.objects.create_user(
            username="citizen_test",
            password="testpassword123",
            email="citizen@test.com",
            first_name="Citizen",
            last_name="Tester",
        )
        RoleAssignment.objects.create(user=self.citizen_user, role=self.citizen_role)

        self.officer_user = User.objects.create_user(
            username="officer_test",
            password="testpassword123",
            email="officer@test.com",
            first_name="Officer",
            last_name="Tester",
        )
        RoleAssignment.objects.create(user=self.officer_user, role=self.officer_role, state="DL")

        # 3. Create Rule & Source
        self.source = RuleSource.objects.create(
            notification_no="G.S.R. CITIZEN-TEST",
            title="Test Rule Source",
            published_date=date(2020, 1, 1),
        )
        self.rule_mfg = Rule.objects.create(
            rule_id_code="PCR-CITIZEN-TEST-MFG",
            section_ref="Rule 6(1)",
            category="general",
            condition={"type": "required_field", "field": "mfg_date"},
            effective_from=date(2020, 1, 1),
            status="in_force",
            source=self.source,
        )

        # 4. Create Seed Product A (already scanned with compliance check)
        self.product_scanned = Product.objects.create(
            gtin_barcode="8901234567890",
            brand_name="Heritage Brand",
            product_name="Heritage Tea 500g",
            category="food",
            manufacturer_name="Heritage Foods Ltd",
            manufacturer_address="Plot 12, Industrial Area, New Delhi",
        )
        self.prior_scan = Scan.objects.create(
            product=self.product_scanned,
            performed_by=self.officer_user,
            role_context="officer",
            capture_method="guided_capture",
            status="processed",
        )
        self.prior_check = ComplianceCheck.objects.create(
            scan=self.prior_scan,
            verdict="non_compliant",
            overall_confidence=0.95,
            evaluated_against_rule_set_date=date.today(),
        )
        self.prior_violation = Violation.objects.create(
            compliance_check=self.prior_check,
            rule=self.rule_mfg,
            description="Mandatory declaration 'mfg_date' is missing",
        )
        ProductComplianceHistory.objects.create(
            product=self.product_scanned,
            violation=self.prior_violation,
            is_first_time=True,
            case=None,
        )

        # 5. Create Seed Product B (never scanned)
        self.product_unscanned = Product.objects.create(
            gtin_barcode="8909876543210",
            brand_name="New Brand",
            product_name="Organic Honey 250g",
            category="food",
            manufacturer_name="Natural Apiaries",
            manufacturer_address="Sector 4, Dehradun",
        )

    def test_01_skip_rescan_returns_stored_result_without_new_scan(self):
        """Screen 1: Barcode lookup on previously scanned product returns stored check instantly."""
        self.client.force_authenticate(user=self.citizen_user)
        initial_scan_count = Scan.objects.count()

        response = self.client.post(
            "/api/scans/",
            {"barcode": "8901234567890"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data["product_id"], self.product_scanned.id)
        self.assertEqual(data["has_been_scanned"], True)
        self.assertEqual(data["verdict"], "non_compliant")
        self.assertEqual(data["violation_count"], 1)
        self.assertEqual(data["violations"][0]["rule_code"], "PCR-CITIZEN-TEST-MFG")

        # Prove no new Scan row was created
        self.assertEqual(Scan.objects.count(), initial_scan_count)

    def test_02_first_scan_without_photo_prompts_for_photo(self):
        """Screen 1: First scan without photo returns 400 prompting citizen for image."""
        self.client.force_authenticate(user=self.citizen_user)

        response = self.client.post(
            "/api/scans/",
            {"barcode": "8909876543210"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = response.json()
        self.assertTrue(data.get("needs_photo"))

    def test_03_first_scan_with_photo_runs_pipeline_and_no_case_created(self):
        """Screen 1: First scan with photo runs OCR pipeline and records history without creating Case."""
        self.client.force_authenticate(user=self.citizen_user)
        initial_case_count = Case.objects.count()

        response = self.client.post(
            "/api/scans/",
            {
                "barcode": "8909876543210",
                "image_urls": ["http://localhost:8000/media/test_label.jpg"],
                "category": "food",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = response.json()
        self.assertEqual(data["product_id"], self.product_unscanned.id)
        self.assertEqual(data["has_been_scanned"], True)

        # Confirm DB objects created
        created_scan = Scan.objects.filter(product=self.product_unscanned, role_context="citizen").first()
        self.assertIsNotNone(created_scan)
        self.assertEqual(created_scan.performed_by, self.citizen_user)

        # Confirm citizen scans NEVER auto-create Cases
        self.assertEqual(Case.objects.count(), initial_case_count)

    def test_04_compliance_snapshot_read_only(self):
        """Screen 2: GET /api/products/{id}/compliance-snapshot/ returns stored snapshot without evaluation."""
        self.client.force_authenticate(user=self.citizen_user)

        response = self.client.get(f"/api/products/{self.product_scanned.id}/compliance-snapshot/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data["product_id"], self.product_scanned.id)
        self.assertEqual(data["verdict"], "non_compliant")
        self.assertEqual(data["violation_count"], 1)

    def test_05_product_brand_info_detail(self):
        """Screen 3: GET /api/products/{id}/ returns product master information."""
        self.client.force_authenticate(user=self.citizen_user)

        response = self.client.get(f"/api/products/{self.product_scanned.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data["gtin_barcode"], "8901234567890")
        self.assertEqual(data["brand_name"], "Heritage Brand")
        self.assertEqual(data["product_name"], "Heritage Tea 500g")
        self.assertEqual(data["manufacturer_name"], "Heritage Foods Ltd")

    def test_06_file_complaint(self):
        """Screen 4: POST /api/complaints/ files a complaint for the citizen."""
        self.client.force_authenticate(user=self.citizen_user)

        payload = {
            "product": self.product_scanned.id,
            "description": "The net weight printed is unclear and smudge-marked.",
            "photo_urls": ["http://localhost:8000/media/complaint_evidence.jpg"],
            "location": "New Delhi, Connaught Place",
        }
        response = self.client.post("/api/complaints/", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = response.json()
        self.assertEqual(data["product"], self.product_scanned.id)
        self.assertEqual(data["description"], payload["description"])
        self.assertEqual(data["status"], "open")
        self.assertEqual(data["filed_by_username"], self.citizen_user.username)
        self.assertGreater(data["risk_score"], 0.0)
        self.assertEqual(data["routed_to_state"], "Delhi")


    def test_07_complaint_status_mine_returns_own_complaints(self):
        """Screen 5: GET /api/complaints/mine/ returns citizen's own filed complaints."""
        self.client.force_authenticate(user=self.citizen_user)

        Complaint.objects.create(
            filed_by=self.citizen_user,
            product=self.product_scanned,
            description="Expired packaging found in store",
            status="open",
        )

        response = self.client.get("/api/complaints/mine/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertGreaterEqual(len(data), 1)
        self.assertEqual(data[0]["product"], self.product_scanned.id)

    def test_08_officer_cannot_access_citizen_complaints_mine_gets_403(self):
        """Permission boundary: Field officer gets 403 Forbidden on GET /api/complaints/mine/."""
        self.client.force_authenticate(user=self.officer_user)

        response = self.client.get("/api/complaints/mine/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_09_complaint_risk_scoring_and_routing(self):
        """Verify dynamic risk scoring and real state name extraction for fresh complaints."""
        self.client.force_authenticate(user=self.citizen_user)

        payload = {
            "product": self.product_scanned.id,  # category: "food", has prior violation history
            "description": "Retailer in Sector 62 charged ₹50 above printed MRP, and expiry date was illegible.",
            "photo_urls": ["http://localhost:8000/media/overcharge_receipt.jpg"],
            "location": "Noida Sector 62, Uttar Pradesh",
        }
        response = self.client.post("/api/complaints/", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = response.json()

        # Assert calculated non-placeholder risk score:
        # Base (40) + Food category (20) + Prior violation history (10) + Overcharging keyword (15) + Photo evidence (5) = 90.0
        self.assertGreater(data["risk_score"], 0.0)
        self.assertGreaterEqual(data["risk_score"], 80.0)

        # Assert state routing properly extracted "Uttar Pradesh"
        self.assertEqual(data["routed_to_state"], "Uttar Pradesh")
        self.assertEqual(data["status"], "open")

