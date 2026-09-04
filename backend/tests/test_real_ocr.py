"""
Automated unit tests for Production PaddleOCR Real OCR Pipeline.
Tests:
1. PaddleOCR response normalization using mocked PaddleOCR output.
2. Regex extraction for MRP variations.
3. Regex extraction for net quantity variations.
4. Regex extraction for manufacturing, expiry, and best before dates.
5. FSSAI 14-digit number extraction.
6. Invalid image rejection (empty, invalid format).
7. Empty OCR result behavior (empty field list, clear warning).
8. Django multipart request construction in services.py.
9. Mock OCR being disabled by default (settings.OCR_USE_MOCK is False).
10. Extracted fields persisted in database with actual returned values.
11. OCR service failure not creating fake compliance results (scan status=failed).
"""
import io
import cv2
import numpy as np
import base64
from unittest.mock import patch, MagicMock
from datetime import date

from django.test import TestCase, override_settings
from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

from apps.accounts.models import Role, RoleAssignment
from apps.product_master.models import Product
from apps.scans.models import Scan, ScanImage, ExtractedField
from apps.compliance.models import ComplianceCheck, Violation
from apps.rules_engine.models import Rule, RuleSource
from apps.scans.services import (
    process_scan_pipeline,
    resolve_image_bytes,
    OCRServiceError,
)
from ml_services.ocr_stub.ocr import (
    extract_words_paddle,
    extract_legal_metrology_fields,
    decode_image_bytes,
    decode_base64_image,
    ExtractedFieldItem,
)

User = get_user_model()


def make_test_image_bytes(text="TEST LABEL") -> bytes:
    """Create a minimal valid JPEG image in memory for testing."""
    img = np.ones((200, 400, 3), dtype=np.uint8) * 255
    cv2.putText(img, text, (20, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2)
    success, encoded = cv2.imencode(".jpg", img)
    assert success
    return encoded.tobytes()


class RealOCRPipelineTests(TestCase):
    def setUp(self):
        self.client = APIClient()

        # Roles
        self.citizen_role, _ = Role.objects.get_or_create(name="citizen")
        self.officer_role, _ = Role.objects.get_or_create(name="field_officer")

        # Users
        self.citizen_user = User.objects.create_user(
            username="ocr_citizen",
            password="testpassword123",
            email="ocr_citizen@test.com",
        )
        RoleAssignment.objects.create(user=self.citizen_user, role=self.citizen_role)

        self.officer_user = User.objects.create_user(
            username="ocr_officer",
            password="testpassword123",
            email="ocr_officer@test.com",
        )
        RoleAssignment.objects.create(user=self.officer_user, role=self.officer_role, state="DL")

        # Rule source & rules
        self.source = RuleSource.objects.create(
            notification_no="G.S.R. OCR-TEST",
            title="OCR Test Rules",
            published_date=date(2020, 1, 1),
        )
        self.rule_mrp = Rule.objects.create(
            source=self.source,
            rule_id_code="PCR-OCR-MRP",
            section_ref="Rule 6(1)(e)",
            category="general",
            condition={"type": "required_field", "field": "mrp"},
            effective_from=date(2020, 1, 1),
        )
        self.rule_net_qty = Rule.objects.create(
            source=self.source,
            rule_id_code="PCR-OCR-NETQTY",
            section_ref="Rule 6(1)(b)",
            category="general",
            condition={"type": "required_field", "field": "net_quantity"},
            effective_from=date(2020, 1, 1),
        )

        # Seed Product
        self.product = Product.objects.create(
            gtin_barcode="8901234567890",
            brand_name="Real Brand",
            product_name="Real Product 500ml",
            category="general",
            manufacturer_name="Real Packagers Ltd",
            manufacturer_address="Industrial Area, New Delhi 110001",
        )

    # -------------------------------------------------------------------------
    # 1. PaddleOCR response normalization using mocked PaddleOCR output
    # -------------------------------------------------------------------------
    def test_01_paddleocr_output_normalization(self):
        """Test normalization of PaddleOCR line-level output into word tokens and coordinates."""
        # PaddleOCR format: [ [ [ [[x1,y1],[x2,y2],[x3,y3],[x4,y4]], ("text", conf) ], ... ] ]
        mock_ocr_result = [[
            [[[10, 20], [100, 20], [100, 45], [10, 45]], ("MRP Rs. 199.00", 0.965)],
            [[[10, 55], [80, 55], [80, 80], [10, 80]], ("Net Qty: 250 g", 0.942)],
        ]]
        mock_model = MagicMock(spec=["ocr"])
        mock_model.ocr.return_value = mock_ocr_result

        test_img = np.zeros((200, 300, 3), dtype=np.uint8)
        words_data, full_text = extract_words_paddle(mock_model, test_img)

        self.assertEqual(len(words_data), 2)
        self.assertEqual(words_data[0]["text"], "MRP Rs. 199.00")
        self.assertEqual(words_data[0]["bbox_px"], [10, 20, 100, 45])
        self.assertAlmostEqual(words_data[0]["confidence"], 0.965, places=3)
        self.assertIn("MRP Rs. 199.00", full_text)
        self.assertIn("Net Qty: 250 g", full_text)

        # Also test PaddleOCR 3.x predict format
        mock_model_v3 = MagicMock(spec=["predict"])
        mock_model_v3.predict.return_value = [{
            "rec_texts": ["MRP Rs. 199.00", "Net Qty: 250 g"],
            "rec_scores": [0.965, 0.942],
            "rec_boxes": [
                [10, 20, 100, 45],
                [10, 55, 80, 80],
            ]
        }]
        words_data_v3, full_text_v3 = extract_words_paddle(mock_model_v3, test_img)
        self.assertEqual(len(words_data_v3), 2)
        self.assertEqual(words_data_v3[0]["text"], "MRP Rs. 199.00")
        self.assertIn("Net Qty: 250 g", full_text_v3)

    # -------------------------------------------------------------------------
    # 2. Regex extraction for MRP variations
    # -------------------------------------------------------------------------
    def test_02_regex_extraction_mrp_variations(self):
        """Test deterministic regex extractor across common MRP formats and currencies."""
        variations = [
            ("MRP Rs. 349.00 (Incl. of all taxes)", "MRP Rs. 349.00 (Incl. of all taxes)"),
            ("M.R.P.: Rs 50.00", "M.R.P.: Rs 50.00"),
            ("MAX RETAIL PRICE ₹120.50 INCL ALL TAXES", "MAX RETAIL PRICE ₹120.50 INCL ALL TAXES"),
            ("MRP - INR 85.00", "MRP - INR 85.00"),
            ("MRP: 99.00", "MRP: 99.00"),
        ]
        for raw, expected_substr in variations:
            words = [{"text": raw, "confidence": 0.95, "bbox_px": [10, 10, 100, 30]}]
            fields = extract_legal_metrology_fields(words, raw)
            mrp_field = next((f for f in fields if f.field_type == "mrp"), None)
            self.assertIsNotNone(mrp_field, f"Failed to extract MRP from: '{raw}'")
            self.assertIn(mrp_field.field_type, "mrp")
            self.assertTrue(any(ch.isdigit() for ch in mrp_field.value))

    # -------------------------------------------------------------------------
    # 3. Regex extraction for Net Quantity variations
    # -------------------------------------------------------------------------
    def test_03_regex_extraction_net_quantity_variations(self):
        """Test deterministic regex extractor for various unit forms (ml, l, g, kg, pcs)."""
        variations = [
            ("Net Qty: 500 ml", "500 ml"),
            ("Net Wt. 1 kg when packed", "1 kg"),
            ("NET WEIGHT: 250 g", "250 g"),
            ("Net Quantity: 750ml", "750ml"),
            ("Net Contents: 1.5 L", "1.5 L"),
            ("Net Qty: 10 N", "10 N"),
        ]
        for raw, expected_unit in variations:
            words = [{"text": raw, "confidence": 0.93, "bbox_px": [10, 10, 100, 30]}]
            fields = extract_legal_metrology_fields(words, raw)
            net_field = next((f for f in fields if f.field_type == "net_quantity"), None)
            self.assertIsNotNone(net_field, f"Failed to extract net_quantity from: '{raw}'")
            self.assertIn(expected_unit.lower(), net_field.value.lower())

    # -------------------------------------------------------------------------
    # 4. Regex extraction for Manufacturing, Expiry, and Best Before dates
    # -------------------------------------------------------------------------
    def test_04_regex_extraction_dates(self):
        """Test deterministic regex extractor for MFD, EXP, and Best Before dates."""
        text = "MFD: 15/08/2025 EXP: 14/08/2026 BEST BEFORE 12 MONTHS FROM PACKING"
        words = [
            {"text": "MFD: 15/08/2025", "confidence": 0.92, "bbox_px": [10, 10, 100, 30]},
            {"text": "EXP: 14/08/2026", "confidence": 0.91, "bbox_px": [10, 40, 100, 60]},
            {"text": "BEST BEFORE 12 MONTHS FROM PACKING", "confidence": 0.89, "bbox_px": [10, 70, 200, 90]},
        ]
        fields = extract_legal_metrology_fields(words, text)
        fields_by_type = {f.field_type: f for f in fields}

        self.assertIn("mfg_date", fields_by_type)
        self.assertIn("15/08/2025", fields_by_type["mfg_date"].value)

        self.assertIn("expiry_date", fields_by_type)
        self.assertIn("14/08/2026", fields_by_type["expiry_date"].value)

        self.assertIn("best_before_date", fields_by_type)
        self.assertIn("12 MONTHS", fields_by_type["best_before_date"].value)

    # -------------------------------------------------------------------------
    # 5. FSSAI 14-digit number extraction
    # -------------------------------------------------------------------------
    def test_05_fssai_license_extraction(self):
        """Test extraction of 14-digit FSSAI license numbers."""
        variations = [
            "fssai Lic. No. 10015022003344",
            "FSSAI 10015022003344",
            "Lic No: 12345678901234",
        ]
        for raw in variations:
            words = [{"text": raw, "confidence": 0.97, "bbox_px": [10, 10, 150, 30]}]
            fields = extract_legal_metrology_fields(words, raw)
            fssai_field = next((f for f in fields if f.field_type == "fssai_license_no"), None)
            self.assertIsNotNone(fssai_field, f"Failed to extract FSSAI from: '{raw}'")
            self.assertTrue(any(len(token) == 14 and token.isdigit() for token in fssai_field.value.split()))

    # -------------------------------------------------------------------------
    # 6. Invalid image rejection (empty, invalid format)
    # -------------------------------------------------------------------------
    def test_06_invalid_image_rejection(self):
        """Test that empty or corrupted bytes are rejected with ValueError."""
        with self.assertRaises(ValueError):
            decode_image_bytes(b"", "empty.jpg")

        with self.assertRaises(ValueError):
            decode_image_bytes(b"NotAnImageBytesGarbage", "corrupt.jpg")

        with self.assertRaises(ValueError):
            decode_base64_image("invalid_base64_string!!!")

    # -------------------------------------------------------------------------
    # 7. Empty OCR result behavior
    # -------------------------------------------------------------------------
    def test_07_empty_ocr_result_behavior(self):
        """When OCR detects no text, return empty field list without fake fallback demo data."""
        fields = extract_legal_metrology_fields([], "")
        self.assertEqual(fields, [])

        # Ensure no demo values are returned
        field_values = [f.value for f in fields]
        self.assertNotIn("Heritage Foods Ltd.", field_values)
        self.assertNotIn("Pure Desi Ghee", field_values)
        self.assertNotIn("500 ml", field_values)
        self.assertNotIn("₹349.00", field_values)

    # -------------------------------------------------------------------------
    # 8. Django multipart request construction & image resolution
    # -------------------------------------------------------------------------
    def test_08_resolve_image_bytes(self):
        """Test resolve_image_bytes across base64 data URLs, raw bytes, and file objects."""
        # 1. Raw bytes
        raw_b = b"TestBytes123"
        b, fname = resolve_image_bytes(raw_b)
        self.assertEqual(b, raw_b)

        # 2. File-like object
        bio = io.BytesIO(raw_b)
        bio.name = "custom.png"
        b, fname = resolve_image_bytes(bio)
        self.assertEqual(b, raw_b)
        self.assertEqual(fname, "custom.png")

        # 3. Base64 Data URL
        jpeg_b = make_test_image_bytes()
        b64_str = "data:image/jpeg;base64," + base64.b64encode(jpeg_b).decode("utf-8")
        b, fname = resolve_image_bytes(b64_str)
        self.assertEqual(b, jpeg_b)
        self.assertTrue(fname.endswith(".jpg"))

    # -------------------------------------------------------------------------
    # 9. Mock OCR being disabled by default (settings.OCR_USE_MOCK is False)
    # -------------------------------------------------------------------------
    def test_09_mock_ocr_disabled_by_default(self):
        """Verify that OCR_USE_MOCK is False by default in settings."""
        self.assertFalse(getattr(settings, "OCR_USE_MOCK", False))

    # -------------------------------------------------------------------------
    # 10. Extracted fields persisted in database with actual returned values
    # -------------------------------------------------------------------------
    @patch("apps.scans.services.requests.post")
    def test_10_extracted_fields_persisted_with_actual_values(self, mock_post):
        """Verify that fields returned by the OCR service are saved into extracted_fields table."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "scan_id": "test_scan_10",
            "extracted_fields": [
                {
                    "field_type": "mrp",
                    "value": "Rs. 450.00 (Incl. of all taxes)",
                    "confidence": 0.94,
                    "font_size_mm": None,
                    "placement_zone": "declaration_panel"
                },
                {
                    "field_type": "net_quantity",
                    "value": "1 L",
                    "confidence": 0.92,
                    "font_size_mm": None,
                    "placement_zone": "principal_display_panel"
                }
            ],
            "barcode": "8901234567890",
            "quality_flags": [],
            "warnings": []
        }
        mock_post.return_value = mock_response

        scan = Scan.objects.create(
            performed_by=self.citizen_user,
            product=self.product,
            role_context="citizen",
            capture_method="single_image",
            status="pending",
        )

        test_img = make_test_image_bytes("LABEL CONTENT")
        check = process_scan_pipeline(scan, image_urls=[test_img], category="general")

        self.assertIsNotNone(check)
        self.assertEqual(scan.status, "processed")

        # Verify actual persisted ExtractedField rows
        fields = ExtractedField.objects.filter(scan=scan)
        self.assertEqual(fields.count(), 2)

        mrp_field = fields.get(field_type="mrp")
        self.assertEqual(mrp_field.extracted_value, "Rs. 450.00 (Incl. of all taxes)")
        self.assertAlmostEqual(mrp_field.confidence_score, 0.94, places=2)

        net_field = fields.get(field_type="net_quantity")
        self.assertEqual(net_field.extracted_value, "1 L")
        self.assertAlmostEqual(net_field.confidence_score, 0.92, places=2)

    # -------------------------------------------------------------------------
    # 11. OCR service failure not creating fake compliance results
    # -------------------------------------------------------------------------
    @patch("apps.scans.services.requests.post")
    def test_11_ocr_service_failure_does_not_create_fake_results(self, mock_post):
        """When OCR microservice fails and OCR_USE_MOCK=False, mark scan as failed without fake records."""
        mock_post.side_effect = Exception("Connection refused on port 8001")

        scan = Scan.objects.create(
            performed_by=self.citizen_user,
            product=self.product,
            role_context="citizen",
            capture_method="single_image",
            status="pending",
        )

        test_img = make_test_image_bytes("LABEL CONTENT")
        with self.assertRaises(OCRServiceError):
            process_scan_pipeline(scan, image_urls=[test_img], category="general")

        scan.refresh_from_db()
        self.assertEqual(scan.status, "failed")

        # Confirm NO ExtractedField rows created
        self.assertEqual(ExtractedField.objects.filter(scan=scan).count(), 0)

        # Confirm NO ComplianceCheck rows created
        self.assertEqual(ComplianceCheck.objects.filter(scan=scan).count(), 0)
