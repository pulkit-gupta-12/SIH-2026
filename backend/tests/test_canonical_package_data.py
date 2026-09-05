"""
Tests for Canonical Normalized Package-Data Representation.
Verifies deterministic normalizers, schema validation, missing field handling,
ambiguity detection, and DRF serialization.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from apps.scans.canonical import (
    normalize_mrp,
    normalize_net_quantity,
    normalize_unit_sale_price,
    normalize_date,
    normalize_best_before,
    normalize_fssai,
    normalize_consumer_care,
    normalize_country_of_origin,
    normalize_manufacturer_address,
    normalize_batch_number,
    build_canonical_package_data,
    empty_canonical_field,
)
from apps.scans.models import Scan
from apps.scans.serializers import ScanDetailSerializer
from apps.product_master.models import Product

User = get_user_model()


class CanonicalNormalizersTestCase(TestCase):
    """Unit tests for individual field normalizers."""

    def test_normalize_mrp_various_formats(self):
        # Format: Rs.349
        norm, status, amb = normalize_mrp("MRP: Rs.349")
        self.assertEqual(status, "success")
        self.assertEqual(norm["amount"], 349.0)
        self.assertEqual(norm["currency"], "INR")
        self.assertIsNone(amb)

        # Format: ₹349 with inclusive taxes
        norm, status, amb = normalize_mrp("₹349.00 (Incl. of all taxes)")
        self.assertEqual(status, "success")
        self.assertEqual(norm["amount"], 349.0)
        self.assertEqual(norm["currency"], "INR")
        self.assertTrue(norm["inclusive_of_taxes"])

        # Format: 1,299 with comma
        norm, status, amb = normalize_mrp("MRP Rs. 1,299")
        self.assertEqual(status, "success")
        self.assertEqual(norm["amount"], 1299.0)

        # Ambiguous multiple amounts
        norm, status, amb = normalize_mrp("MRP Rs. 300 / Rs. 400")
        self.assertEqual(status, "ambiguous")
        self.assertIsNotNone(amb)

        # Non-numeric unparseable
        norm, status, amb = normalize_mrp("MRP Not Mentioned")
        self.assertEqual(status, "failed")
        self.assertIsNone(norm)

    def test_normalize_net_quantity(self):
        # Format: 500 ml
        norm, status, amb = normalize_net_quantity("500 ml")
        self.assertEqual(status, "success")
        self.assertEqual(norm["quantity"], 500.0)
        self.assertEqual(norm["unit"], "ml")

        # Format: 1 kg
        norm, status, amb = normalize_net_quantity("1 kg")
        self.assertEqual(status, "success")
        self.assertEqual(norm["quantity"], 1.0)
        self.assertEqual(norm["unit"], "kg")

        # Format: Net Wt. 750g
        norm, status, amb = normalize_net_quantity("Net Wt. 750g")
        self.assertEqual(status, "success")
        self.assertEqual(norm["quantity"], 750.0)
        self.assertEqual(norm["unit"], "g")

        # Format: 2 L
        norm, status, amb = normalize_net_quantity("2 L")
        self.assertEqual(status, "success")
        self.assertEqual(norm["quantity"], 2.0)
        self.assertEqual(norm["unit"], "l")

        # Format: 100 N
        norm, status, amb = normalize_net_quantity("100 N")
        self.assertEqual(status, "success")
        self.assertEqual(norm["quantity"], 100.0)
        self.assertEqual(norm["unit"], "N")

        # Missing unit
        norm, status, amb = normalize_net_quantity("just 500")
        self.assertEqual(status, "failed")
        self.assertIsNone(norm)

    def test_normalize_unit_sale_price(self):
        norm, status, amb = normalize_unit_sale_price("₹0.70 / ml")
        self.assertEqual(status, "success")
        self.assertEqual(norm["amount"], 0.70)
        self.assertEqual(norm["currency"], "INR")
        self.assertEqual(norm["unit"], "ml")

        norm, status, amb = normalize_unit_sale_price("Rs. 1.25 per g")
        self.assertEqual(status, "success")
        self.assertEqual(norm["amount"], 1.25)
        self.assertEqual(norm["unit"], "g")

    def test_normalize_dates(self):
        # Month/Year: 01/2026
        norm, status, amb = normalize_date("MFG: 01/2026")
        self.assertEqual(status, "success")
        self.assertEqual(norm["year"], 2026)
        self.assertEqual(norm["month"], 1)
        self.assertIsNone(norm["day"])
        self.assertEqual(norm["date_iso"], "2026-01")

        # Month/Year: 12-2027
        norm, status, amb = normalize_date("EXP: 12-2027")
        self.assertEqual(status, "success")
        self.assertEqual(norm["year"], 2027)
        self.assertEqual(norm["month"], 12)
        self.assertEqual(norm["date_iso"], "2027-12")

        # Full Date: 15/01/2026
        norm, status, amb = normalize_date("15/01/2026")
        self.assertEqual(status, "success")
        self.assertEqual(norm["year"], 2026)
        self.assertEqual(norm["month"], 1)
        self.assertEqual(norm["day"], 15)
        self.assertEqual(norm["date_iso"], "2026-01-15")

        # Textual Month: Jan 2026
        norm, status, amb = normalize_date("Jan 2026")
        self.assertEqual(status, "success")
        self.assertEqual(norm["year"], 2026)
        self.assertEqual(norm["month"], 1)

    def test_normalize_best_before(self):
        # Duration: 6 months
        norm, status, amb = normalize_best_before("Best Before: 6 months")
        self.assertEqual(status, "success")
        self.assertEqual(norm["duration_value"], 6)
        self.assertEqual(norm["duration_unit"], "months")

        # Duration: 24 months
        norm, status, amb = normalize_best_before("Best before 24 months from manufacture")
        self.assertEqual(status, "success")
        self.assertEqual(norm["duration_value"], 24)

    def test_normalize_fssai_license(self):
        # Valid 14 digits
        norm, status, amb = normalize_fssai("Lic. No. 10015022003344")
        self.assertEqual(status, "success")
        self.assertEqual(norm["license_number"], "10015022003344")
        self.assertTrue(norm["is_valid_format"])

        # Invalid length (10 digits)
        norm, status, amb = normalize_fssai("1234567890")
        self.assertEqual(status, "failed")
        self.assertFalse(norm["is_valid_format"])

    def test_normalize_consumer_care(self):
        norm, status, amb = normalize_consumer_care("Careline: 1800-111-222, email: care@heritage.com")
        self.assertEqual(status, "success")
        self.assertEqual(norm["phone"], "1800-111-222")
        self.assertEqual(norm["email"], "care@heritage.com")

    def test_normalize_country_of_origin(self):
        norm, status, amb = normalize_country_of_origin("Made in Japan")
        self.assertEqual(status, "success")
        self.assertEqual(norm["country"], "Japan")
        self.assertEqual(norm["iso_code"], "JP")

        norm, status, amb = normalize_country_of_origin("Country of Origin: India")
        self.assertEqual(status, "success")
        self.assertEqual(norm["country"], "India")
        self.assertEqual(norm["iso_code"], "IN")

    def test_normalize_manufacturer_address(self):
        addr_text = "Plot 12, Industrial Area, Pune, Maharashtra 411018"
        norm, status, amb = normalize_manufacturer_address(addr_text)
        self.assertEqual(status, "success")
        self.assertEqual(norm["pin_code"], "411018")
        self.assertEqual(norm["state"], "Maharashtra")
        self.assertEqual(norm["city"], "Pune")

    def test_normalize_batch_number(self):
        norm, status, amb = normalize_batch_number("Batch No: B-2026-03")
        self.assertEqual(status, "success")
        self.assertEqual(norm["batch_number"], "B-2026-03")


class CanonicalPackageDataBuilderTestCase(TestCase):
    """Tests for build_canonical_package_data orchestration."""

    def test_all_eight_properties_preserved(self):
        sample_extracted = [
            {
                "field_type": "mrp",
                "value": "MRP: Rs.349",
                "confidence": 0.96,
                "bbox_px": [10, 20, 100, 40],
                "placement_zone": "declaration_panel",
            }
        ]

        canonical = build_canonical_package_data(
            extracted_fields=sample_extracted,
            raw_text="Sample package raw text",
            barcode="8901234567890",
        )

        mrp_field = canonical["mrp"]
        # Verify all 8 properties
        self.assertEqual(mrp_field["raw"], "MRP: Rs.349")
        self.assertEqual(mrp_field["normalized"], {"amount": 349.0, "currency": "INR", "inclusive_of_taxes": False})
        self.assertEqual(mrp_field["confidence"], 0.96)
        self.assertEqual(mrp_field["source_panel"], "declaration_panel")
        self.assertEqual(mrp_field["bbox"], [10, 20, 100, 40])
        self.assertTrue(mrp_field["detected"])
        self.assertEqual(mrp_field["normalization_status"], "success")
        self.assertIsNone(mrp_field["ambiguity"])

    def test_missing_fields_not_hallucinated(self):
        # Pass empty extracted fields
        canonical = build_canonical_package_data(extracted_fields=[])

        # Mandatory fields must be marked as not detected, not fabricated
        net_qty = canonical["net_quantity"]
        self.assertIsNone(net_qty["raw"])
        self.assertIsNone(net_qty["normalized"])
        self.assertFalse(net_qty["detected"])
        self.assertEqual(net_qty["normalization_status"], "not_detected")
        self.assertIsNone(net_qty["confidence"])
        self.assertIsNone(net_qty["bbox"])

        mfg = canonical["mfg_date"]
        self.assertFalse(mfg["detected"])
        self.assertEqual(mfg["normalization_status"], "not_detected")

    def test_raw_text_and_barcode_preserved(self):
        canonical = build_canonical_package_data(
            extracted_fields=[],
            raw_text="Pure Desi Ghee 500ml Heritage Foods",
            barcode="8901234567890",
        )
        self.assertEqual(canonical["raw_text"], "Pure Desi Ghee 500ml Heritage Foods")
        self.assertTrue(canonical["barcode"]["detected"])
        self.assertEqual(canonical["barcode"]["normalized"]["barcode"], "8901234567890")
        self.assertEqual(canonical["barcode"]["normalized"]["type"], "EAN-13")


class CanonicalSerializationTestCase(TestCase):
    """Test persistence and DRF serialization of canonical_data."""

    def setUp(self):
        self.user = User.objects.create_user(username="test_officer", password="password123")
        self.product = Product.objects.create(
            gtin_barcode="8901234567890",
            product_name="Pure Desi Ghee",
            brand_name="Heritage",
            category="food",
        )

    def test_scan_canonical_data_serialization(self):
        sample_extracted = [
            {"field_type": "mrp", "value": "₹349.00 (Incl. of all taxes)", "confidence": 0.95},
            {"field_type": "net_quantity", "value": "500 ml", "confidence": 0.92},
            {"field_type": "mfg_date", "value": "01/2026", "confidence": 0.90},
        ]

        canonical_data = build_canonical_package_data(
            extracted_fields=sample_extracted,
            raw_text="MRP ₹349.00 NET 500 ml MFG 01/2026",
            barcode="8901234567890",
        )

        scan = Scan.objects.create(
            performed_by=self.user,
            product=self.product,
            role_context="officer",
            capture_method="guided_capture",
            status="processed",
            canonical_data=canonical_data,
        )

        serializer = ScanDetailSerializer(scan)
        res_data = serializer.data

        self.assertIn("canonical_data", res_data)
        self.assertEqual(res_data["canonical_data"]["mrp"]["normalized"]["amount"], 349.0)
        self.assertEqual(res_data["canonical_data"]["net_quantity"]["normalized"]["quantity"], 500.0)
        self.assertEqual(res_data["canonical_data"]["mfg_date"]["normalized"]["year"], 2026)
        self.assertEqual(res_data["canonical_data"]["barcode"]["raw"], "8901234567890")
