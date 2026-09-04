# SIH-2026: Legal Metrology Compliance Verification System

Production-ready Legal Metrology verification pipeline with a Django + DRF backend, FastAPI PaddleOCR microservice, and React frontend.

---

## 1. Installation Commands

### Prerequisites
- Python 3.10+ (tested on Python 3.13)
- Node.js 18+ and npm
- PostgreSQL 16+ or Docker Desktop

### Environment Setup

#### A. Backend Dependencies
```bash
cd backend
pip install -r requirements/base.txt
```

#### B. Dedicated OCR Microservice Dependencies
```bash
pip install -r ml_services/ocr_stub/requirements.txt
```
Key packages installed:
- `fastapi` & `uvicorn`
- `python-multipart`
- `pydantic`
- `opencv-python` & `numpy`
- `paddlepaddle` & `paddleocr`
- `pyzbar` & `requests`

#### C. Frontend Dependencies
```bash
cd frontend
npm install
```

---

## 2. How to Start PostgreSQL & Redis

### Option A: Docker (Recommended)
From the root repository directory:
```bash
docker compose up -d db redis
```
This starts:
- PostgreSQL 16 on `localhost:5432` (`legalmetro` / `legalmetro_dev`)
- Redis 7 on `localhost:6379`

### Option B: Local PostgreSQL Service
Ensure PostgreSQL is running on port 5432 with database `legalmetro`, user `legalmetro`, password `legalmetro_dev`.

---

## 3. How to Start the FastAPI OCR Service

The PaddleOCR service runs as a dedicated microservice on **port 8001**.

```bash
cd backend
python -m uvicorn ml_services.ocr_stub.ocr:app --host 0.0.0.0 --port 8001
```

- PaddleOCR models (`PP-OCRv6_medium_det` and `PP-OCRv6_medium_rec`) are loaded **once during startup** via FastAPI lifespan.
- Runs on CPU by default (`DEVICE=cpu`).
- Fast inference configuration: `engine_config={'run_mode': 'paddle'}` and `use_doc_unwarping=False`.

---

## 4. How to Start Django Backend

From the `backend` directory:

```bash
cd backend

# Run database migrations
python manage.py migrate

# Seed required Legal Metrology rules and admin accounts
python manage.py seed_rules

# Start the Django development server
python manage.py runserver 0.0.0.0:8000
```

---

## 5. How to Test `/health` Endpoint

Verify that the OCR microservice is running and models are loaded into memory:

```bash
curl http://localhost:8001/health
```

Expected JSON Response:
```json
{
  "status": "ok",
  "service": "paddleocr",
  "device": "cpu",
  "models": {
    "paddleocr_loaded": true,
    "pyzbar_available": true,
    "gliner_available": false
  }
}
```

---

## 6. How to Submit a Real Image

### Option A: Via the Standalone CLI Test Script
The test script submits an image via `multipart/form-data` to `/process`:

```bash
# Test with your own real product label image:
python scripts/test_real_ocr_cli.py path/to/product_label.jpg

# Or run without arguments to generate and test a synthetic label:
python scripts/test_real_ocr_cli.py
```

### Option B: Via Curl to FastAPI OCR Microservice
```bash
curl -X POST http://localhost:8001/process \
  -F "images=@path/to/product_label.jpg" \
  -F "scan_id=scan_test_001" \
  -F "category=food"
```

### Option C: Via Django DRF Scan API
Upload image directly to the Django API as multipart/form-data:
```bash
curl -X POST http://localhost:8000/api/v1/scans/ \
  -H "Authorization: Bearer <JWT_TOKEN>" \
  -F "scan_type=citizen" \
  -F "category=food" \
  -F "images=@path/to/product_label.jpg"
```

---

## 7. How to Verify Results in PostgreSQL / pgAdmin

Open pgAdmin or `psql` connected to `legalmetro`:

```sql
-- 1. Check Scan record and status
SELECT id, scan_type, status, error_message, created_at
FROM scans_scan
ORDER BY created_at DESC
LIMIT 5;

-- 2. Verify actual extracted OCR fields (NO hardcoded demo values)
SELECT id, scan_id, field_type, extracted_value, confidence_score, font_size_mm, placement_zone
FROM scans_extractedfield
ORDER BY id DESC
LIMIT 15;

-- 3. Check Rule Engine Compliance Results
SELECT id, scan_id, rule_id, status, severity, score
FROM compliance_compliancecheck
ORDER BY id DESC
LIMIT 10;

-- 4. Check Detected Violations
SELECT id, scan_id, rule_code, violation_type, description
FROM compliance_violation
ORDER BY id DESC;
```

---

## 8. Expected Behavior When No Text Is Detected

When an image containing no legible text (e.g. blank, blurry, or plain background) is submitted:
1. **Response**: HTTP 200 with an empty `extracted_fields: []` array.
2. **Warnings**: Contains `"No text detected in uploaded image(s)."`.
3. **Database**: No fake fields are inserted. Scan is evaluated against mandatory field rules and correctly flags missing declarations without fabricating demo values.

---

## 9. Expected Behavior When OCR Service Is Unavailable

When `http://localhost:8001` is stopped or offline:
1. **Strict Mock Disabled**: `OCR_USE_MOCK=False` by default. The system **never** silently falls back to fake demo strings (Heritage Foods Ltd., ₹349.00, 500 ml).
2. **Scan State**: `scan.status` is explicitly set to `"failed"`.
3. **Error Logging**: Detailed error logged in `scan.processing_errors` (e.g., `"Connection refused on port 8001"`).
4. **Database Integrity**: Zero fake `ExtractedField` or `ComplianceCheck` records are created.
5. **API Response**: Returns HTTP 502 Bad Gateway with:
```json
{
  "error": "OCR processing service is currently unavailable. Scan marked as failed."
}
```

---

## 10. Running Automated Tests

Run unit test suites covering the entire pipeline:

```bash
cd backend

# 1. Real OCR & Legal Metrology test suite (11 focused tests)
python manage.py test tests.test_real_ocr --settings=config.settings.test

# 2. Citizen App scan tests (9 tests)
python manage.py test tests.test_citizen_app --settings=config.settings.test

# 3. Officer Console guided scan tests (9 tests)
python manage.py test tests.test_officer_console --settings=config.settings.test
```
All 29 tests pass with zero errors.
