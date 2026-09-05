"""
Automated tests for Legal Metrology Officer Console PDF Report Generation.
Verifies report generation for violations, compliant zero-violation scans, and API endpoints.
"""
import os
import io
from datetime import date
from django.test import TestCase
from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
import pypdfium2 as pdfium

from apps.accounts.models import Role, RoleAssignment
from apps.product_master.models import Product
from apps.scans.models import Scan, ScanImage, ExtractedField
from apps.rules_engine.models import Rule, RuleSource
from apps.compliance.models import ComplianceCheck, Violation
from apps.cases.models import Case, ImprovementNotice
from apps.reports.models import Report

User = get_user_model()


class ReportGenerationTests(TestCase):
    def setUp(self):
        self.client = APIClient()

        # Create officer user with role
        self.officer = User.objects.create_user(
            username="officer_test",
            password="testpassword123",
            first_name="Ramesh",
            last_name="Kumar",
            email="ramesh.officer@example.gov.in",
        )
        self.officer_role = Role.objects.create(name="field_officer")
        RoleAssignment.objects.create(
            user=self.officer,
            role=self.officer_role,
            state="Delhi NCT",
        )
        self.client.force_authenticate(user=self.officer)

        # Rule Source and Rule
        self.source = RuleSource.objects.create(
            notification_no="GSR 426(E)",
            title="Legal Metrology (Packaged Commodities) Amendment Rules",
            published_date=date(2021, 1, 1),
        )
        self.rule_mrp = Rule.objects.create(
            rule_id_code="LMR-2011-R06-MRP",
            section_ref="Rule 6(1)(e)",
            category="food",
            condition={"type": "field_presence", "field": "mrp"},
            effective_from=date(2021, 1, 1),
            status="in_force",
            source=self.source,
        )

        # Product
        self.product = Product.objects.create(
            gtin_barcode="8901234567890",
            product_name="Heritage Pure Mustard Oil 1L",
            brand_name="Heritage Naturals",
            category="food",
            manufacturer_name="Heritage Foods Ltd",
            manufacturer_address="Plot 10, Okhla Industrial Area, New Delhi",
        )

    def test_generate_report_for_case_with_violations(self):
        """
        Asserts that generating a report for a Case with violations creates
        a real, non-empty PDF containing violation citations and outcome details.
        """
        scan = Scan.objects.create(
            product=self.product,
            performed_by=self.officer,
            role_context="officer",
            location="Connaught Place, New Delhi",
            capture_method="guided_capture",
            status="reviewed",
        )
        img1 = ScanImage.objects.create(
            scan=scan,
            image_url="http://localhost:8000/media/test_front.jpg",
            angle_type="front_panel",
            quality_check_passed=True,
        )
        ExtractedField.objects.create(
            scan=scan,
            field_type="net_quantity",
            extracted_value="1 Litre",
            confidence_score=0.95,
            font_size_mm=3.0,
            placement_zone="front_panel",
        )

        check = ComplianceCheck.objects.create(
            scan=scan,
            verdict="non_compliant",
            overall_confidence=0.92,
            evaluated_against_rule_set_date=date.today(),
            reviewed_by_officer=self.officer,
        )
        violation = Violation.objects.create(
            compliance_check=check,
            rule=self.rule_mrp,
            description="Maximum Retail Price (MRP) declaration missing from principal display panel.",
            evidence_image=img1,
        )

        case = Case.objects.create(
            product=self.product,
            violation=violation,
            classification="first_time",
            status="notice_sent",
            opened_by=self.officer,
        )
        ImprovementNotice.objects.create(
            case=case,
            issued_by=self.officer,
            rectification_deadline=date(2026, 10, 1),
            outcome="pending",
        )

        # Call POST /api/cases/{id}/generate-report/
        response = self.client.post(f"/api/cases/{case.id}/generate-report/", format="json")
        self.assertIn(response.status_code, [status.HTTP_201_CREATED, status.HTTP_200_OK])

        data = response.json()
        self.assertIn("file_url", data)
        self.assertTrue(data["file_url"].endswith(".pdf"))
        self.assertEqual(data["case_id"], case.id)

        # Assert physical file exists and is non-empty
        rel_path = data["file_url"].lstrip("/")
        full_path = os.path.join(settings.BASE_DIR, rel_path)
        self.assertTrue(os.path.exists(full_path), f"Report file {full_path} must exist on disk.")
        file_size = os.path.getsize(full_path)
        self.assertGreater(file_size, 1000, "PDF file must be non-empty and greater than 1KB.")

        # Parse text with pypdfium2 to confirm content sections
        pdf = pdfium.PdfDocument(full_path)
        self.assertGreaterEqual(len(pdf), 1)
        all_text = " ".join([page.get_textpage().get_text_range() for page in pdf])

        self.assertIn("LEGAL METROLOGY INSPECTION REPORT", all_text)
        self.assertIn("Ramesh Kumar", all_text)
        self.assertIn("Heritage Pure Mustard Oil 1L", all_text)
        self.assertIn("LMR-2011-R06-MRP", all_text)
        self.assertIn("Rule 6(1)(e)", all_text)
        self.assertIn("Section 29", all_text)
        self.assertIn("Officer confirmation on file", all_text)
        pdf.close()

    def test_generate_report_for_compliant_check_zero_violations(self):
        """
        Asserts that generating a report directly from a ComplianceCheck with 0 violations
        renders the 'No violations found' section correctly and does not crash on empty violations.
        """
        scan = Scan.objects.create(
            product=self.product,
            performed_by=self.officer,
            role_context="officer",
            location="Market Yard, Delhi",
            capture_method="single_image",
            status="processed",
        )
        ExtractedField.objects.create(
            scan=scan,
            field_type="mrp",
            extracted_value="Rs. 185.00 (Incl. of all taxes)",
            confidence_score=0.98,
            font_size_mm=4.0,
            placement_zone="declaration_panel",
        )

        check = ComplianceCheck.objects.create(
            scan=scan,
            verdict="compliant",
            overall_confidence=0.98,
            evaluated_against_rule_set_date=date.today(),
            reviewed_by_officer=self.officer,
        )

        # Call POST /api/compliance-checks/{id}/generate-report/
        response = self.client.post(f"/api/compliance-checks/{check.id}/generate-report/", format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        data = response.json()
        self.assertIn("file_url", data)
        self.assertEqual(data["compliance_check_id"], check.id)
        self.assertIsNone(data["case_id"])

        rel_path = data["file_url"].lstrip("/")
        full_path = os.path.join(settings.BASE_DIR, rel_path)
        self.assertTrue(os.path.exists(full_path))
        self.assertGreater(os.path.getsize(full_path), 1000)

        # Parse text and assert 'No violations found' is present
        pdf = pdfium.PdfDocument(full_path)
        all_text = " ".join([page.get_textpage().get_text_range() for page in pdf])
        self.assertIn("No violations found", all_text)
        self.assertIn("No formal enforcement case initiated", all_text)
        pdf.close()

    def test_idempotent_report_retrieval(self):
        """
        Asserts that calling generate-report repeatedly does not re-generate duplicate files
        unless regenerate=True is explicitly passed.
        """
        scan = Scan.objects.create(
            product=self.product,
            performed_by=self.officer,
            role_context="officer",
            status="processed",
        )
        check = ComplianceCheck.objects.create(
            scan=scan,
            verdict="compliant",
            overall_confidence=0.95,
            evaluated_against_rule_set_date=date.today(),
        )

        # First generation -> 201 Created
        resp1 = self.client.post(f"/api/compliance-checks/{check.id}/generate-report/", format="json")
        self.assertEqual(resp1.status_code, status.HTTP_201_CREATED)
        rep1_id = resp1.json()["id"]
        rep1_url = resp1.json()["file_url"]

        # Second call without regenerate -> 200 OK, same report returned
        resp2 = self.client.post(f"/api/compliance-checks/{check.id}/generate-report/", format="json")
        self.assertEqual(resp2.status_code, status.HTTP_200_OK)
        self.assertEqual(resp2.json()["id"], rep1_id)
        self.assertEqual(resp2.json()["file_url"], rep1_url)

        # Third call with regenerate=True -> 201 Created, new file URL
        resp3 = self.client.post(f"/api/compliance-checks/{check.id}/generate-report/", {"regenerate": True}, format="json")
        self.assertEqual(resp3.status_code, status.HTTP_201_CREATED)
        self.assertNotEqual(resp3.json()["id"], rep1_id)
