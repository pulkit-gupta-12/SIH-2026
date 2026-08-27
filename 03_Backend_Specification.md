# 03 — Backend Specification (Django + DRF + PostgreSQL)

## Folder structure

```
backend/
├── config/
│   ├── settings/
│   │   ├── base.py
│   │   ├── dev.py
│   │   └── prod.py
│   ├── urls.py
│   ├── celery.py
│   └── asgi.py / wsgi.py
├── apps/
│   ├── accounts/            # users, roles, role_assignments, auth
│   ├── product_master/       # products, GTIN resolution, fuzzy match
│   ├── scans/                 # scans, scan_images, extracted_fields
│   ├── rules_engine/          # rule_sources, rules, evaluation logic, admin ingestion workflow
│   ├── compliance/            # compliance_checks, violations, product_compliance_history
│   ├── cases/                 # cases, improvement_notices, penalty_cases
│   ├── complaints/            # citizen complaints, risk scoring
│   ├── inspections/           # inspection_targets, risk-based prioritization
│   ├── reports/               # PDF/DOCX generation
│   ├── ecommerce_integration/  # ecommerce_listings, screening stub
│   ├── notifications/         # notifications, audit_logs
│   ├── dashboards/             # read-only aggregation endpoints per dashboard (no new tables)
│   └── common/                 # shared permissions, pagination, base serializers, JSONB helpers
├── ml_services/
│   └── ocr_stub/               # separate FastAPI service, fixed contract (see below)
├── tests/
├── requirements/
│   ├── base.txt
│   ├── dev.txt
│   └── prod.txt
├── manage.py
└── docker-compose.yml
```

**Rule:** a new module (e.g., a future 8th dashboard, or a real OCR pipeline replacing the stub) is a new folder under `apps/` or `ml_services/`. No existing app's internals should need to change to add one.

## App responsibilities → dashboard mapping

| App | Owns tables | Feeds dashboard(s) |
|---|---|---|
| `accounts` | users, roles, role_assignments | all (auth gate) |
| `product_master` | products | Citizen, Officer, Business, National |
| `scans` | scans, scan_images, extracted_fields | Officer, Citizen |
| `rules_engine` | rule_sources, rules | Rule Admin, feeds Compliance |
| `compliance` | compliance_checks, violations, product_compliance_history | Officer, Business, National |
| `cases` | cases, improvement_notices, penalty_cases | Officer, Controller, Business |
| `complaints` | complaints | Citizen, Controller |
| `inspections` | inspection_targets | Officer, Controller |
| `reports` | reports | Officer, Business, Controller |
| `ecommerce_integration` | ecommerce_listings | E-commerce dashboard, feeds Inspections |
| `notifications` | notifications, audit_logs | all |
| `dashboards` | (none — aggregation only) | Controller, National Admin |

## Key endpoints by dashboard

### Citizen
- `POST /api/scans/` (barcode or image) → returns product + compliance snapshot
- `GET /api/products/{id}/compliance-snapshot/`
- `POST /api/complaints/`
- `GET /api/complaints/mine/`

### Field Officer
- `GET /api/inspections/queue/` (risk-sorted, assigned to me)
- `POST /api/scans/` (6-image guided capture)
- `GET /api/scans/{id}/processing-result/` (calls OCR stub, returns extracted fields + rule evaluation)
- `POST /api/compliance-checks/{id}/confirm/` or `/override/`
- `POST /api/cases/` (auto-classifies first_time/repeat via `product_compliance_history`)
- `POST /api/cases/{id}/improvement-notice/`
- `POST /api/cases/{id}/escalate/`
- `GET /api/products/{id}/violation-history/`

### State Controller
- `GET /api/dashboards/state/{state_id}/summary/` (heatmap, counts)
- `POST /api/inspections/assign/` (bulk-assign risk-ranked targets)
- `GET /api/cases/pending-escalation-approval/`
- `POST /api/cases/{id}/approve-escalation/` or `/return-for-correction/`

### National Admin
- `GET /api/dashboards/national/summary/`
- `GET /api/dashboards/national/top-violators/`
- `POST /api/rules/{id}/simulate/` (proxies to Rule Admin's sandbox — read-only view here)
- `GET /api/dashboards/national/ecommerce-scorecards/`

### Business Portal
- `POST /api/products/pre-check/` (draft label compliance check, no case created)
- `GET /api/cases/mine/` (as the business entity)
- `POST /api/cases/{id}/corrective-action/`
- `GET /api/compliance-history/mine/`

### E-commerce Integration
- `POST /api/ecommerce/listings/bulk/` (bulk submit)
- `GET /api/ecommerce/listings/flagged/`
- `POST /api/ecommerce/listings/{id}/send-to-officer/` → creates `inspection_target`

### Rule Engine Admin
- `GET /api/rules/` (filter by status/category)
- `POST /api/rules/draft/` (from notification text, AI-assisted stub or manual entry)
- `POST /api/rules/{id}/simulate/` (runs against last N days of `compliance_checks`)
- `POST /api/rules/{id}/publish/` (sets `effective_from`, flips status, archives superseded rule)

## OCR/CV Stub Contract (build this even before real OCR exists)

Endpoint: `POST /process` on the `ml_services/ocr_stub` FastAPI service.

Request:
```json
{ "scan_id": "uuid", "image_urls": ["...", "..."], "category": "food|electronics|general" }
```

Response (fixed shape — real implementation must return exactly this shape later):
```json
{
  "extracted_fields": [
    { "field_type": "mrp", "value": "₹149", "confidence": 0.92, "font_size_mm": 3.1, "placement_zone": "declaration_panel" },
    { "field_type": "net_quantity", "value": "200g", "confidence": 0.88 }
  ],
  "barcode": "8901234567890",
  "quality_flags": []
}
```

Build the stub to return semi-randomized but plausible values seeded from the uploaded image's category, so demo runs look real without needing a trained model yet. Django's `scans` app calls this over HTTP exactly as it will call the real service later — no code changes needed on swap.

## Auth & RBAC

- JWT-based auth (`djangorestframework-simplejwt`).
- Permission classes in `apps/common/permissions.py`, one per role, composed on each viewset (e.g., `IsFieldOfficer`, `IsStateController`).
- Every state-changing viewset action writes to `audit_logs` via a shared mixin (`apps/common/mixins.py::AuditLoggedMixin`) — don't reimplement logging per-app.
