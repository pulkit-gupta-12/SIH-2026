"""
Scans processing service.
Calls FastAPI PaddleOCR service with multipart image upload,
persists real ExtractedFields, runs evaluate_scan(), and persists ComplianceCheck + Violations.
"""
import os
import io
import base64
import logging
import requests
from datetime import date
from django.conf import settings
from .models import Scan, ScanImage, ExtractedField
from apps.product_master.models import Product
from apps.rules_engine.evaluate import evaluate_scan
from apps.compliance.models import ComplianceCheck, Violation
from apps.compliance.history import classify_and_record

logger = logging.getLogger(__name__)


class OCRServiceError(Exception):
    """Raised when the OCR microservice fails and mock mode is disabled."""
    pass


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


def resolve_image_bytes(image_ref) -> tuple[bytes, str]:
    """
    Resolves an image reference into raw bytes and a filename.
    Supports:
      - Raw bytes or bytearrays
      - UploadedFile or file-like objects (with .read())
      - Data URLs (data:image/jpeg;base64,...)
      - Filesystem paths (absolute or relative to MEDIA_ROOT / BASE_DIR)
      - Remote HTTP/HTTPS URLs
    """
    if not image_ref:
        return b"", "empty.jpg"

    if isinstance(image_ref, (bytes, bytearray)):
        return bytes(image_ref), "image.jpg"

    if hasattr(image_ref, "read"):
        filename = getattr(image_ref, "name", "upload.jpg")
        image_ref.seek(0)
        data = image_ref.read()
        return data, filename

    if isinstance(image_ref, str):
        # 1. Base64 Data URL
        if image_ref.startswith("data:image/"):
            try:
                header, b64_data = image_ref.split(",", 1)
                ext = "jpg"
                if "png" in header:
                    ext = "png"
                elif "webp" in header:
                    ext = "webp"
                data = base64.b64decode(b64_data)
                return data, f"captured.{ext}"
            except Exception as e:
                logger.error("Failed to decode base64 data URL: %s", e)
                raise ValueError(f"Invalid base64 image data: {e}")

        # 2. Local File Path
        if os.path.isabs(image_ref) and os.path.exists(image_ref):
            with open(image_ref, "rb") as f:
                return f.read(), os.path.basename(image_ref)

        # 3. Media URL path e.g. /media/file.jpg or media/file.jpg
        media_root = getattr(settings, "MEDIA_ROOT", None)
        if media_root:
            clean_rel = image_ref.lstrip("/")
            if clean_rel.startswith("media/"):
                clean_rel = clean_rel[len("media/"):]
            candidate = os.path.join(str(media_root), clean_rel)
            if os.path.exists(candidate):
                with open(candidate, "rb") as f:
                    return f.read(), os.path.basename(candidate)

        # 4. Check relative to BASE_DIR
        base_dir = getattr(settings, "BASE_DIR", None)
        if base_dir:
            candidate = os.path.join(str(base_dir), image_ref.lstrip("/"))
            if os.path.exists(candidate):
                with open(candidate, "rb") as f:
                    return f.read(), os.path.basename(candidate)

        # 5. Remote HTTP/HTTPS URL
        if image_ref.startswith(("http://", "https://")):
            try:
                resp = requests.get(image_ref, timeout=5.0)
                if resp.status_code == 200:
                    fname = os.path.basename(image_ref.split("?")[0]) or "remote_image.jpg"
                    return resp.content, fname
            except Exception as e:
                logger.warning("Failed to fetch remote image URL '%s': %s", image_ref, e)

    raise ValueError(f"Unable to resolve image reference: {image_ref[:60] if isinstance(image_ref, str) else type(image_ref)}")


def process_scan_pipeline(scan, image_urls=None, image_files=None, category="general", is_citizen_scan=False):
    """
    Executes complete production scan pipeline:
    1. Resolves real image bytes and stores ScanImage records.
    2. Sends multipart/form-data to PaddleOCR FastAPI microservice (http://localhost:8001/process).
    3. Persists detected ExtractedFields in DB (no hardcoded demo data).
    4. Evaluates Rule Engine: evaluate_scan().
    5. Persists ComplianceCheck and Violation objects.
    6. Classifies repeat offenses and updates scan status.
    """
    all_image_refs = []
    if image_urls:
        all_image_refs.extend(image_urls)
    if image_files:
        all_image_refs.extend(image_files)

    # Persist ScanImage rows
    for ref in all_image_refs:
        display_url = getattr(ref, "name", str(ref))
        if isinstance(ref, str) and ref.startswith("data:image/"):
            display_url = f"data:image/jpeg;base64,[{len(ref)} chars]"
        ScanImage.objects.create(
            scan=scan,
            image_url=display_url[:500],
            angle_type="declaration_panel",
            quality_check_passed=True,
        )

    ocr_url = f"{getattr(settings, 'OCR_SERVICE_URL', 'http://localhost:8001')}/process"
    timeout_sec = getattr(settings, "OCR_TIMEOUT_SECONDS", 30.0)
    use_mock = getattr(settings, "OCR_USE_MOCK", False)

    extracted_items = []
    detected_barcode = None

    # Resolve image bytes for multipart upload
    resolved_files = []
    for idx, ref in enumerate(all_image_refs):
        try:
            img_bytes, fname = resolve_image_bytes(ref)
            if img_bytes:
                content_type = "image/png" if fname.endswith(".png") else "image/jpeg"
                resolved_files.append(("images", (fname or f"image_{idx}.jpg", img_bytes, content_type)))
        except Exception as e:
            logger.warning("Image resolution failed for item %d: %s", idx, e)

    try:
        if resolved_files:
            logger.info("Sending %d image(s) to OCR service at %s", len(resolved_files), ocr_url)
            data_payload = {
                "scan_id": str(scan.id),
                "category": category or "general"
            }
            resp = requests.post(ocr_url, data=data_payload, files=resolved_files, timeout=timeout_sec)
            if resp.status_code == 200:
                result_data = resp.json()
                extracted_items = result_data.get("extracted_fields", [])
                detected_barcode = result_data.get("barcode")
                logger.info("OCR service returned %d extracted fields for scan %s", len(extracted_items), scan.id)
            else:
                err_detail = f"OCR microservice returned status {resp.status_code}: {resp.text[:200]}"
                logger.error(err_detail)
                raise OCRServiceError(err_detail)
        else:
            logger.warning("No image files could be resolved for OCR processing on scan %s", scan.id)

    except Exception as e:
        if use_mock:
            logger.warning("OCR service unavailable (%s); falling back to mock OCR (OCR_USE_MOCK=True)", e)
            from ml_services.ocr_stub.main import process_scan as mock_process_scan, ProcessRequest
            stub_res = mock_process_scan(ProcessRequest(scan_id=str(scan.id), image_urls=image_urls or [], category=category))
            extracted_items = [
                f.model_dump() if hasattr(f, "model_dump") else f.dict()
                for f in stub_res.extracted_fields
            ]
            detected_barcode = stub_res.barcode
        else:
            # Production path: Mark scan as failed and raise clear exception
            logger.error("OCR pipeline failed on scan %s: %s", scan.id, e)
            scan.status = "failed"
            scan.save(update_fields=["status"])
            raise OCRServiceError(f"OCR microservice failed: {e}") from e

    # If OCR detected a barcode and product is not yet associated, resolve it
    if detected_barcode and not scan.product:
        resolved_prod = resolve_product_from_barcode(detected_barcode, category=category)
        if resolved_prod:
            scan.product = resolved_prod
            scan.save(update_fields=["product"])

    # Persist ExtractedField records with actual OCR values
    for item in extracted_items:
        ExtractedField.objects.create(
            scan=scan,
            field_type=item["field_type"],
            extracted_value=item["value"],
            confidence_score=item.get("confidence", item.get("confidence_score", 0.90)),
            font_size_mm=item.get("font_size_mm"),
            placement_zone=item.get("placement_zone", "unknown"),
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
        sum(item.get("confidence", 0.90) for item in extracted_items) / len(extracted_items)
        if extracted_items else 0.0
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
            classify_and_record(product, viol, case=None if is_citizen_scan else None)

    scan.status = "processed"
    scan.save(update_fields=["status"])

    return check
