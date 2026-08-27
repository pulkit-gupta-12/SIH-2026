# National Legal Metrology Compliance Platform — Implementation Plan

Build the complete backend (Django + DRF + PostgreSQL) and frontend (React + Tailwind) for all 7 dashboards, following the 6-phase sequence from [`02_Implementation_Phases_Dashboards.md`](file:///c:/Users/PULKIT/OneDrive/Desktop/SIH-2026/02_Implementation_Phases_Dashboards.md).

## User Review Required

> [!IMPORTANT]
> **Tech stack**: Django 5.x + DRF + PostgreSQL (backend), React 18 + Vite + Tailwind CSS 3.x + TypeScript (frontend). The docs say "React + Tailwind" — I'll use **Vite** as the bundler (not CRA) and **TypeScript** for type safety. Confirm this is acceptable.

> [!IMPORTANT]
> **PostgreSQL**: The plan assumes PostgreSQL is available via Docker Compose. I'll include a `docker-compose.yml` for the database. You'll need Docker installed to run it.

> [!WARNING]
> **Scale of work**: This is a 6-phase project spanning ~35 screens, ~18 database tables, ~50+ API endpoints, and a rule engine with seeded dataset. I'll build phase-by-phase with `PROGRESS_REPORT.md` updates after each. Phase 1 (Foundation) will be built first, then I'll pause for your review before continuing.

## Open Questions

> [!IMPORTANT]
> 1. **Python version**: Should I target Python 3.11+ or 3.12+?
> 2. **Node version**: Should I target Node 18 LTS or Node 20 LTS?
> 3. **Docker**: Do you have Docker Desktop installed? The database runs in a container.
> 4. **Ports**: Backend on `localhost:8000`, Frontend on `localhost:5173`, PostgreSQL on `5432` — any conflicts?

---

## Phase 1 — Foundation

### Backend Scaffolding

#### [NEW] `backend/` — Django project with exact folder structure from [`03_Backend_Specification.md`](file:///c:/Users/PULKIT/OneDrive/Desktop/SIH-2026/03_Backend_Specification.md)

```
backend/
├── config/
│   ├── settings/
│   │   ├── __init__.py
│   │   ├── base.py          # shared settings: INSTALLED_APPS, middleware, DB, REST_FRAMEWORK, JWT
│   │   ├── dev.py           # DEBUG=True, CORS allow-all, console email backend
│   │   └── prod.py          # (placeholder)
│   ├── urls.py               # root URL conf, includes per-app URL files
│   ├── celery.py             # (placeholder for future async tasks)
│   └── wsgi.py / asgi.py
├── apps/
│   ├── accounts/              # Users, Roles, RoleAssignments, JWT auth
│   ├── product_master/        # (empty app, models in Phase 2)
│   ├── scans/                 # (empty app)
│   ├── rules_engine/          # (empty app, full build in Phase 3)
│   ├── compliance/            # (empty app)
│   ├── cases/                 # (empty app)
│   ├── complaints/            # (empty app)
│   ├── inspections/           # (empty app)
│   ├── reports/               # (empty app)
│   ├── ecommerce_integration/ # (empty app)
│   ├── notifications/         # (empty app)
│   ├── dashboards/            # (empty app)
│   └── common/                # Shared permissions, pagination, base serializers, AuditLoggedMixin
├── ml_services/
│   └── ocr_stub/              # (built in Phase 3, separate FastAPI service)
├── tests/
├── requirements/
│   ├── base.txt
│   ├── dev.txt
│   └── prod.txt
├── manage.py
└── docker-compose.yml         # PostgreSQL 16, Redis (for Celery later)
```

**Key decisions for Phase 1:**
- All 12 Django apps created as empty apps (with `__init__.py`, `apps.py`, empty `models.py`, empty `urls.py`)
- Only `accounts` and `common` get real code in Phase 1
- `accounts` app: `User` model (custom, extending AbstractUser), `Role` model (7 predefined roles), `RoleAssignment` model
- JWT auth via `djangorestframework-simplejwt`: login endpoint returns access + refresh tokens
- `common` app: `IsFieldOfficer`, `IsStateController`, `IsNationalAdmin`, `IsCitizen`, `IsBusiness`, `IsEcommercePartner`, `IsRuleAdmin` permission classes + `AuditLoggedMixin`
- Management command `seed_roles` to create the 7 roles + one superuser per role for testing

---

### Frontend Scaffolding

#### [NEW] `frontend/` — React + Vite + TypeScript + Tailwind, feature-sliced per [`04_Frontend_Specification.md`](file:///c:/Users/PULKIT/OneDrive/Desktop/SIH-2026/04_Frontend_Specification.md)

```
frontend/
├── src/
│   ├── app/
│   │   ├── App.tsx            # Root component with providers
│   │   ├── routes.tsx         # Role-based route guards, RequireRole component
│   │   └── providers/         # AuthProvider, QueryClientProvider, ThemeProvider
│   ├── components/
│   │   ├── ui/                # Button, Card, Badge, StatusPill, Modal, Table, Input (built progressively)
│   │   └── layout/            # AppShell, BottomNav, Sidebar, Header
│   ├── features/
│   │   ├── citizen/           # (placeholder pages)
│   │   ├── officer/           # (placeholder pages)
│   │   ├── controller/        # (placeholder pages)
│   │   ├── national-admin/    # (placeholder pages)
│   │   ├── business-portal/   # (placeholder pages)
│   │   ├── ecommerce-integration/ # (placeholder pages)
│   │   └── rule-admin/        # (placeholder pages)
│   ├── hooks/
│   ├── services/              # apiClient.ts (axios wrapper), authService.ts
│   ├── store/                 # authStore.ts (Zustand)
│   ├── styles/                # globals.css with Tailwind directives
│   └── utils/
├── public/
├── package.json
├── tailwind.config.js         # Design tokens: lane colors (citizen=green, officer=blue, etc.)
├── tsconfig.json
└── vite.config.ts
```

**Key decisions for Phase 1:**
- Vite + React 18 + TypeScript
- Tailwind CSS 3 with custom color tokens matching the flow diagram legend
- Zustand for auth state (`authStore`: user, role, token, login/logout)
- React Query (`@tanstack/react-query`) configured globally
- Axios client with JWT interceptor (auto-attach token, auto-refresh)
- `RequireRole` route guard — redirects to the user's own dashboard home if they hit an unauthorized route
- 7 placeholder dashboard pages (one per role), each showing "Welcome, {role}" with the role's lane color
- Login page with role selector for easy demo switching
- Mobile-first base styles, responsive sidebar/bottom-nav shell

---

### Phase 1 Exit Check
> Logging in as each of the 7 roles lands on a distinct, correctly-gated placeholder page with the role's lane color.

---

## Phase 2 — Data Layer

### Database Models

#### [MODIFY] All apps under `backend/apps/` — implement Django models per [`05_Database_Schema.md`](file:///c:/Users/PULKIT/OneDrive/Desktop/SIH-2026/05_Database_Schema.md)

- `accounts`: `User`, `Role`, `RoleAssignment` (already from Phase 1, refine if needed)
- `product_master`: `Product` (with GTIN, category enum, manufacturer info)
- `scans`: `Scan`, `ScanImage`, `ExtractedField`
- `rules_engine`: `RuleSource`, `Rule` (with JSONB `condition` field)
- `compliance`: `ComplianceCheck`, `Violation`, `ProductComplianceHistory`
- `cases`: `Case`, `ImprovementNotice`, `PenaltyCase`
- `complaints`: `Complaint`
- `inspections`: `InspectionTarget`
- `reports`: `Report`
- `ecommerce_integration`: `EcommerceListing` (with JSONB `raw_listing_data`)
- `notifications`: `AuditLog`, `Notification`

### Seed Fixtures
- Rules dataset: `seed_rules.json` with ~15-20 real obligations per [`08_Rule_Engine_Dataset_Build_Instructions.md`](file:///c:/Users/PULKIT/OneDrive/Desktop/SIH-2026/08_Rule_Engine_Dataset_Build_Instructions.md)
- `seed_rules` management command
- Demo products fixture: ~20-30 products across food/electronics/general/import categories
- Demo users: 2-3 officers, 2-3 controllers, demo businesses
- `seed_demo_data` management command

### Phase 2 Exit Check
> Django admin shows all tables populated with seed data; migrations match the ERD.

---

## Phase 3 — Rule Engine & Compliance Core

### Rule Engine

#### [MODIFY] `backend/apps/rules_engine/` — full implementation per [`08_Rule_Engine_Dataset_Build_Instructions.md`](file:///c:/Users/PULKIT/OneDrive/Desktop/SIH-2026/08_Rule_Engine_Dataset_Build_Instructions.md)

- `checks.py`: 5 checker functions dispatched by condition type (`required_field`, `format_check`, `font_size_check`, `placement_check`, `conditional_required_field`)
- `evaluate.py`: `evaluate_scan()` — pure function, data in → violations out
- Unit tests (Steps 5 in the doc): missing mfg date, exempted category, rule versioning, font-size large-pack threshold

### OCR Stub

#### [NEW] `backend/ml_services/ocr_stub/` — FastAPI service matching the contract in [`03_Backend_Specification.md`](file:///c:/Users/PULKIT/OneDrive/Desktop/SIH-2026/03_Backend_Specification.md)

- `POST /process` endpoint returning semi-randomized but plausible extracted fields
- Returns the exact response shape the real OCR service will return later

### Compliance Pipeline

#### [MODIFY] `backend/apps/compliance/`

- `history.py`: `classify_and_record()` — first-time vs. repeat classification
- Wire: scan → OCR stub call → rule engine evaluation → violations + compliance_checks persisted

### Phase 3 Exit Check
> `POST /api/scans/` with a seeded image returns a DB-persisted compliance verdict citing real rule IDs. Unit tests pass.

---

## Phase 4 — Dashboards (7 dashboards, in order)

Build every screen listed in [`06_Dashboard_Specs_All7.md`](file:///c:/Users/PULKIT/OneDrive/Desktop/SIH-2026/06_Dashboard_Specs_All7.md), backend endpoints + frontend views.

### 4.1 Citizen App (5 screens)
- Scan/Search, Compliance Snapshot, Product/Brand Info, File Complaint, Complaint Status
- Mobile-first, bottom-nav, camera-first

### 4.2 Field Officer Console (6 screens)
- Inspection Queue, Guided Capture, Processing Result, Review Findings, Violation History Check, Case Creation
- Most feature-dense dashboard; validates rule engine + case creation end-to-end

### 4.3 State Controller Dashboard (5 screens)
- State Dashboard Home, Heatmap/Complaints View, Assign Targets, SLA Monitor, Escalation Review
- Desktop-primary with responsive tablet layout

### 4.4 National Admin Dashboard (6 screens)
- National Command Home, Cross-State Analytics, Top Violators, Policy Simulation View, Enforcement Strategy, Public Transparency Reports

### 4.5 Business Portal (7 screens)
- Register/Login, Pre-Market Check, Findings & Corrections, Compliance Record, Violation History, Notice Response, Verification Status

### 4.6 E-commerce Integration Dashboard (4 screens)
- Bulk Upload / API Status, Screening Results, Flagged Review Queue, Send to Officer

### 4.7 Rule Engine Admin Console (6 screens)
- Notification Monitor, Draft Review, Approval Action, Sandbox Simulation, Publish Rule, Rule Repository

### Phase 4 Exit Check (per dashboard)
> Every row in that dashboard's table in `06_Dashboard_Specs_All7.md` is a working screen with a real API call.

---

## Phase 5 — Cross-Flow Integration Wiring

Work through the 6-item checklist from [`06_Dashboard_Specs_All7.md`](file:///c:/Users/PULKIT/OneDrive/Desktop/SIH-2026/06_Dashboard_Specs_All7.md):

1. Officer's Improvement Notice → Business Portal's Notice Response
2. Business's corrective action → Officer/Controller's Verify Rectification
3. Controller's inspection-target assignment → Officer's Queue
4. E-commerce flagged listing → Officer's Queue as inspection target
5. Rule Admin's published rule → Officer's Processing Result evaluates against it
6. National Admin's Public Transparency Reports → Citizen's Compliance Snapshot

### Phase 5 Exit Check
> All 6 checklist items verified across two logged-in sessions.

---

## Phase 6 — Hardening & Report

- Empty-state UI, loading states, error boundaries across all dashboards
- Audit log completeness check
- Final `PROGRESS_REPORT.md` with all stubs documented

### Phase 6 Exit Check
> Cold demo run — log in as each of 7 roles, perform one action each, state changes ripple correctly across dashboards with zero manual data edits.

---

## Verification Plan

### Automated Tests
- `python manage.py test` — rule engine unit tests (Phase 3)
- Each phase's exit check criteria verified before moving to next phase

### Manual Verification
- Login as each role → correct dashboard displayed (Phase 1)
- Django admin shows all seeded data (Phase 2)
- `POST /api/scans/` returns real compliance verdict (Phase 3)
- Each dashboard screen loads with real API data (Phase 4)
- Cross-flow actions visible across dashboards (Phase 5)
- End-to-end demo run across all 7 roles (Phase 6)

---

## Execution Approach

I will build **Phase 1 first**, update `PROGRESS_REPORT.md`, and pause for your confirmation that the foundation is working before continuing to Phase 2. Each subsequent phase follows the same pattern: build → verify exit check → update progress report → proceed.

Given the sheer size of this project (~35 screens, ~50 endpoints, 18 tables, rule engine, OCR stub), each phase will be a substantial work session. The cross-cutting concerns (mobile-first CSS, audit logging, error states) are baked into every phase rather than deferred.
