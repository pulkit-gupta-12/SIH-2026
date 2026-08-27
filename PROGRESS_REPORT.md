# PROGRESS REPORT — Phase 3: Rule Engine & Compliance Core

## What was built this session

### Rule Engine Core (`apps/rules_engine/`)
- **Condition Checkers** (`apps/rules_engine/checks.py`): Implemented all 5 condition checkers dispatched by `condition['type']`:
  1. `check_required_field`: Validates mandatory field presence; handles category and `"all"` exemptions (e.g. spare parts, medical devices PDP).
  2. `check_format`: Validates string formats (`month_year`, `standard_metric_units`, `currency_inr_incl_taxes`).
  3. `check_font_size`: Validates font height minimums; applies pack size thresholds (`pack_size_threshold_g: 1000`) for large packages.
  4. `check_placement`: Validates declaration zone constraints (e.g. `declaration_panel`).
  5. `check_conditional_required`: Evaluates conditional mandatory fields based on category (`food`, `import`) or channel (`ecommerce`).
- **Evaluator** (`apps/rules_engine/evaluate.py`): Implemented pure `evaluate_scan()` function that filters active rules by temporal validity window (`effective_from <= scan_date < effective_to`) and category, dispatches to checkers, and returns structured violation outputs.
- **Rule Dataset Fixes**: Updated `PCR2026-ECOMM-COO-FILTER` in `seed_rules.json` to explicitly mandate `channel: "ecommerce"` in `applies_if`, differentiating digital listing screening from physical import scans (`PCR2011-R6-1-G-COO-IMPORT`).

### Compliance History & Classification (`apps/compliance/`)
- **First-time vs. Repeat Offense Classification** (`apps/compliance/history.py`): Implemented `classify_and_record()` function querying prior violations for product + rule. Returns `'improvement_notice'` on first offense and `'penalty_case'` on repeat offenses, persisting to `ProductComplianceHistory`.

### OCR Stub Service (`ml_services/ocr_stub/`)
- **FastAPI OCR Stub** (`ml_services/ocr_stub/main.py`): Built and deployed FastAPI service running on port `8001`. Implements fixed JSON contract (`POST /process`), returning structured `extracted_fields`, `confidence_score`, `font_size_mm`, `placement_zone`, `barcode`, and `quality_flags`.

### End-to-End Scan Pipeline (`apps/scans/`)
- **Pipeline Integration** (`apps/scans/services.py`): Connected `POST /api/scans/` to call OCR Stub service over HTTP, save `ExtractedField` rows, run `evaluate_scan()`, and persist `ComplianceCheck` and `Violation` records in PostgreSQL.

### Verified End-to-End & Automated Unit Tests
- **Automated Unit Tests** (`tests/test_rule_engine.py`): All 5 test cases passing cleanly (`python manage.py test tests`):
  1. `test_missing_mfg_date_flagged`: PASSED
  2. `test_exempted_category_not_flagged`: PASSED
  3. `test_rule_versioning_respected`: PASSED (pre-2024 scan evaluates repealed V1 rule; post-2024 scan evaluates V2 in-force rule)
  4. `test_font_size_large_pack_threshold`: PASSED (>1000g threshold requires 6.0mm font)
  5. `test_first_time_vs_repeat_classification`: PASSED (1st offense = improvement notice, 2nd offense = penalty case)
- **Live HTTP Pipeline Verification**: Tested `POST /api/scans/` via JWT-authenticated API call. Successfully called OCR Stub service, extracted 10 fields, evaluated rules, and created DB-persisted `ComplianceCheck` & `Violation` records.

## What is stubbed or mocked (and why)

| Stub | Location | Why | Real implementation TODO |
|------|----------|-----|--------------------------|
| OCR/CV accuracy | `ml_services/ocr_stub/` | Stub service returns realistic extracted fields | Future: replace stub service backend with trained Yolov8/EasyOCR model |
| Manual Rule Drafting AI | `apps/rules_engine/` | Rule ingestion uses structured form / JSON | Future: LLM-assisted draft parser from raw Gazette PDF text |
| E-commerce Scraping | `apps/ecommerce_integration/` | Static listing rows in DB | Phase 4/Future: live marketplace scraper |

## What's left before this phase is complete

**Phase 3 is complete.** All exit criteria met:
- ✅ `POST /api/scans/` with a seeded image returns a DB-persisted compliance verdict citing real rule IDs.
- ✅ Unit tests pass (`python manage.py test tests` ran 5/5 OK).
- ✅ OCR Stub service running with fixed API contract.
- ✅ First-time vs repeat classification working.

## Known issues / risks

1. **OCR Port Dependency**: Django pipeline calls `http://localhost:8001/process`; fallback inline mock is present if FastAPI service is stopped.

## Suggested next prompt

Proceed with Phase 4 (Dashboards): Build the 7 dashboards row-by-row in the order specified in `06_Dashboard_Specs_All7.md`: (4.1) Citizen App -> (4.2) Field Officer Console -> (4.3) State Controller Dashboard -> (4.4) National Admin Dashboard -> (4.5) Business Portal -> (4.6) E-commerce Integration -> (4.7) Rule Engine Admin Console.
