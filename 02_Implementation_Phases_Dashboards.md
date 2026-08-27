# 02 — Implementation Phases (Dashboards-First Approach)

This sequencing exists because dashboards share a data layer — building them out of order causes rework (e.g., building the Officer Console before Rules exist means faking rule evaluation, then redoing it).

## Phase 1 — Foundation
- Repo scaffolding: `backend/` and `frontend/` folder structures exactly as in `03_Backend_Specification.md` / `04_Frontend_Specification.md`.
- Django project + apps created (empty), PostgreSQL running via Docker Compose, `.env` config.
- React project scaffolded with routing shell, Tailwind configured with design tokens.
- Auth & RBAC: `accounts` app, JWT login, 7 roles seeded, `RequireRole` route guard working end-to-end with a placeholder "hello, {role}" page per dashboard.

**Exit check:** logging in as each of the 7 roles lands on a distinct, correctly-gated placeholder page.

## Phase 2 — Data Layer
- Implement every table in `05_Database_Schema.md` as Django models + migrations.
- Seed fixtures: rules dataset (per `08_Rule_Engine_Dataset_Build_Instructions.md`), ~20–30 demo products, 2–3 demo businesses, 2–3 demo officers/controllers.

**Exit check:** Django admin shows all tables populated with seed data; ERD in the schema doc matches actual migrations.

## Phase 3 — Rule Engine & Compliance Core
- Build the rule engine evaluation function (`apps/rules_engine`) and the OCR stub service (`ml_services/ocr_stub`) per the fixed contract.
- Wire `scans` → stub OCR call → `compliance` app's evaluation → `violations`/`compliance_checks` written.
- Build `product_compliance_history` first-time/repeat computation logic — this gates everything in Phase 5's case workflow.

**Exit check:** posting a seeded image through `/api/scans/` returns a real, DB-persisted compliance verdict citing real rule IDs.

## Phase 4 — Dashboards (build in this order)
1. **Citizen** — simplest, no auth complexity beyond basic login, validates the scan→snapshot pipeline end-to-end.
2. **Field Officer** — the most feature-dense; validates rule engine + case creation.
3. **State Controller** — depends on Officer's cases/targets existing.
4. **National Admin** — depends on Controller-level data existing to aggregate.
5. **Business Portal** — depends on Officer's Improvement Notices existing to display.
6. **E-commerce Integration** — depends on Inspection Targets existing to feed into.
7. **Rule Engine Admin** — build last functionally, but note: a *minimal* version (just enough to publish the seed rule set) must exist as of Phase 2 — this phase is where the full workflow (draft/review/sandbox/publish UI) gets built.

**Exit check per dashboard:** every row in that dashboard's table in `06_Dashboard_Specs_All7.md` is a working screen with a real API call.

## Phase 5 — Cross-Flow Integration Wiring
- Work through the "Cross-flow wiring checklist" at the bottom of `06_Dashboard_Specs_All7.md` — one item at a time, verify end-to-end by performing the action in one dashboard and confirming it appears in the other, using two logged-in sessions.

**Exit check:** all six checklist items pass.

## Phase 6 — Hardening & Report
- Add missing empty-state UI, loading states, and error boundaries across all dashboards (React Query already gives you the states — just render them).
- Audit log completeness check: every state-changing action in the checklist above appears in `audit_logs`.
- Generate the final `PROGRESS_REPORT.md` per the format in `00_Overview_and_Instructions.md`, explicitly listing every stub (OCR, e-commerce, cross-regulator, payment, digital signature) and what real-world work remains for each.

**Exit check:** a cold demo run — log in as each of the 7 roles in sequence, perform one action each, and confirm the state changes ripple correctly across dashboards — completes with zero manual data edits in Django admin.
