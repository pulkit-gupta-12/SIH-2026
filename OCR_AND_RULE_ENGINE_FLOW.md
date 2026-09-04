# Legal Metrology OCR & Rule Engine Architecture

## Overview
This document details the production-ready real OCR pipeline using **PaddleOCR** for packaged commodity compliance under the Legal Metrology (Packaged Commodities) Rules, 2011.

---

## 1. Pipeline Architecture Flow

```
[ Frontend: React ]
  │
  ├── Citizen: Single image file upload
  └── Officer: Guided multi-panel image upload (PDP, Declaration Panel, MRP Closeup)
        │
        ▼ (Multipart/Form-Data with actual image bytes)
[ Django DRF Backend: Port 8000 ]
  │
  ├── 1. `POST /api/v1/scans/` (views.py -> serializers.py)
  ├── 2. Persist `Scan` & `ScanImage` records in DB
  ├── 3. `process_scan_pipeline()` (services.py)
  │      - Resolves local file paths, uploaded bytes, data URIs, or remote URLs
  │      - Streams multipart/form-data payload with actual image binary bytes
  │
  ▼ (POST http://localhost:8001/process)
[ FastAPI PaddleOCR Microservice: Port 8001 ]
  │
  ├── 1. Model caching: Loads `PP-OCRv6_medium_det` and `PP-OCRv6_medium_rec` once at lifespan startup
  ├── 2. Barcode & Physical Scale Calibration: OpenCV BarcodeDetector & pyzbar fallback
  ├── 3. Text Detection & Recognition: PaddleOCR text detection (DBNet) and recognition (SVTR)
  ├── 4. Deterministic Field Extraction: Regex and proximity heuristics for Legal Metrology:
  │      - `mrp`
  │      - `net_quantity`
  │      - `mfg_date`, `expiry_date`, `best_before_date`
  │      - `manufacturer_name`, `manufacturer_address`
  │      - `consumer_care_details`
  │      - `unit_sale_price`
  │      - `fssai_license_no`
  │      - `country_of_origin`
  │      - `batch_number`
  │      - `commodity_name`
  │
  ▼ (Returns ProcessResponse: extracted_fields, bbox_px, font_size_mm, warnings)
[ Django DRF Backend: Port 8000 ]
  │
  ├── 4. Persistence: Populates `ExtractedField` table with actual detected values
  ├── 5. Rule Engine: Invokes `evaluate_scan()` against legal metrology rules
  └── 6. Compliance Checks: Creates `ComplianceCheck` and `Violation` records
```

---

## 2. Service Endpoints

### PaddleOCR Microservice (`http://localhost:8001`)

| Endpoint | Method | Input | Description |
|---|---|---|---|
| `/health` | GET | None | Microservice status, loaded models, execution device |
| `/process` | POST | Multipart (`images`, `scan_id`, `category`) or JSON fallback | Primary OCR pipeline endpoint |
| `/extract` | POST | JSON (`image_base64`, `scan_id`, `category`) | Backward-compatible JSON endpoint |

---

## 3. Strict Real Processing (No Demo Fallback)

1. **Production Default**: `OCR_USE_MOCK=False`. Hardcoded mock strings (Heritage Foods Ltd., ₹349.00, 500 ml) have been removed from the real scan execution path.
2. **Offline OCR Handling**: If the OCR service at `http://localhost:8001` is unavailable, `services.py` raises `OCRServiceError`, sets `scan.status = 'failed'`, records an explicit error in `scan.processing_errors`, and does **NOT** create fake `ExtractedField` or `ComplianceCheck` records.
3. **Empty Text Detection**: If OCR detects no text on the uploaded image, it returns an empty field list `[]` and a warning `"No text detected in uploaded image(s)."`. The system never fabricates demo data.

---

## 4. Physical Scale & Placement Zone Analysis

- **Scale Calibration**: When a 1D barcode is visible, module width is calibrated against standard EAN/UPC nominal widths (`STANDARD_MODULE_WIDTH_MM = 0.33mm`) to derive `scale_factor_mm_per_px` and compute `font_size_mm`.
- **Limitation**: If no barcode is detected or if the image angle is skewed, `font_size_mm` is returned as `null` with a clear warning. Physical dimensions are never invented.
- **Placement Zones**: Bounding box geometry is mapped to `principal_display_panel` (bottom 30% / center), `declaration_panel` (clustered side panels), or `unknown`.
