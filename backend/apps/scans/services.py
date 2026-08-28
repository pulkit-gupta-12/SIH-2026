"""
Scans processing service.
Calls OCR stub, persists ExtractedFields, runs evaluate_scan(), and persists ComplianceCheck + Violations.
"""
import logging
import requests
from django.conf import settings
from datetime import date
from .models import Scan, ScanImage, ExtractedField
from apps.product_master.models import Product
from apps.rules_engine.evaluate import evaluate_scan
from apps.compliance.models import ComplianceCheck, Violation
from apps.compliance.history import classify_and_record

logger = logging.getLogger(__name__)


def resolve_product_from_barcode(barcode, category=None, name_hint=None):
    """
    Looks up a Product by barcode/GTIN. If it doesn't exist yet, creates a
    minimal placeholder record so the scan can proceed.
    """
    if not barcode:
        return None

    product, created = Product.objects.get_or_create(
        gtin_barcode=barcode,
        defaults={
            "product_name": name_hint or f"Unregistered product ({barcode})",
            "brand_name": "Generic / Unregistered",
            "category": category or "general",
            "manufacturer_name": "Unspecified Manufacturer",
            "manufacturer_address": "Unspecified Address",
        },
    )
    if created:
        logger.info("Auto-created Product %s from barcode %s", product.id, barcode)
    return product


def get_existing_compliance_result(product):
    """
    Returns the latest ComplianceCheck for this product if it has ever been
    scanned before (by any role), else None.
    """
    if product is None:
        return None
    return (
        ComplianceCheck.objects.filter(scan__product=product)
        .order_by("-created_at")
        .first()
    )


def process_scan_pipeline(scan, image_urls=None, category="general", is_citizen_scan=False):
    """
    Executes complete scan pipeline:
    1. Call OCR Stub service (http://localhost:8001/process or fallback)
    2. Save extracted fields to DB
    3. Run Rule Engine evaluate_scan()
    4. Save ComplianceCheck and Violation objects
    5. Call classify_and_record (case=None if citizen)
    6. Update scan status to 'processed'
    """
    if image_urls:
        for url in image_urls:
            ScanImage.objects.create(
                scan=scan,
                image_url=url,
                angle_type="declaration_panel",
                quality_check_passed=True,
            )

    ocr_url = f"{getattr(settings, 'OCR_SERVICE_URL', 'http://localhost:8001')}/process"
    payload = {
        "scan_id": str(scan.id),
        "image_urls": image_urls or [],
        "category": category,
    }

    extracted_items = []
    try:
        resp = requests.post(ocr_url, json=payload, timeout=3.0)
        if resp.status_code == 200:
            print("OCR: called live stub")
            data = resp.json()
            extracted_items = data.get("extracted_fields", [])
        else:
            print(f"OCR: live stub returned status {resp.status_code}, using fallback")
            raise Exception(f"Non-200 status {resp.status_code}")
    except Exception as e:
        # Fallback to direct OCR mock generator if FastAPI process isn't running
        print(f"OCR: used fallback mock (Reason: {str(e)})")
        from ml_services.ocr_stub.main import process_scan, ProcessRequest
        stub_res = process_scan(ProcessRequest(scan_id=str(scan.id), image_urls=image_urls or [], category=category))
        extracted_items = [f.model_dump() if hasattr(f, 'model_dump') else f.dict() for f in stub_res.extracted_fields]

    # Save ExtractedField records in DB
    for item in extracted_items:
        ExtractedField.objects.create(
            scan=scan,
            field_type=item["field_type"],
            extracted_value=item["value"],
            confidence_score=item.get("confidence", 0.90),
            font_size_mm=item.get("font_size_mm"),
            placement_zone=item.get("placement_zone"),
        )

    # Evaluate Rules Engine
    product = scan.product
    scan_date = scan.created_at.date() if scan.created_at else date.today()
    violations_detected = evaluate_scan(
        extracted_fields=extracted_items,
        product=product,
        scan_date=scan_date,
        channel="physical",
    )

    verdict = "non_compliant" if violations_detected else "compliant"
    avg_conf = (
        sum(item.get("confidence", 0.9) for item in extracted_items) / len(extracted_items)
        if extracted_items else 0.90
    )

    # Create ComplianceCheck in DB
    check = ComplianceCheck.objects.create(
        scan=scan,
        verdict=verdict,
        overall_confidence=avg_conf,
        evaluated_against_rule_set_date=scan_date,
    )

    # Create Violations in DB & classify first-time vs repeat
    for v in violations_detected:
        viol = Violation.objects.create(
            compliance_check=check,
            rule=v["rule"],
            description=v["message"],
        )
        if product:
            # For citizen scans, case is strictly None (no case auto-created)
            classify_and_record(product, viol, case=None if is_citizen_scan else None)

    scan.status = "processed"
    scan.save()

    return check
