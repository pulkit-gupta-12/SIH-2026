# 01 — PRD: Phase 2 (All Dashboards, Backend + Frontend, Fully Dynamic)

## Objective

Build working, dynamic, database-backed backend + frontend for all seven dashboards defined in `07_User_Flow_Reference.md`, so the team has one reliable, demoable system before layering in remaining requirements (production-grade OCR accuracy, live e-commerce crawling, full cross-regulator API integrations).

## Definition of "done" for this phase

A dashboard is done when:
1. Every screen/node in its lane of `07_User_Flow_Reference.md` has a real backend endpoint and a real frontend view.
2. Data displayed comes from PostgreSQL via the API — no hardcoded frontend arrays.
3. Role-based auth gates access to the dashboard correctly.
4. Any not-yet-real business logic (OCR accuracy, live crawling, cross-regulator calls) sits behind a stub service with a fixed contract, documented in `PROGRESS_REPORT.md`.
5. The cross-flow arrows connecting this lane to others (see reference doc) are wired — e.g., an Officer's Improvement Notice actually appears in the Business Portal, not just in the Officer's own view.

## In scope this phase

- Auth & RBAC for all 7 roles (Citizen, Officer, Controller, National Admin, Business, E-commerce Partner, Rule Admin).
- Full CRUD + workflow endpoints for: Product Master, Scans, Compliance Checks, Cases (Improvement Notice / Penalty), Rules, Complaints, Inspection Targets.
- All 7 dashboard UIs, mobile-first, per `04_Frontend_Specification.md` and `06_Dashboard_Specs_All7.md`.
- Rule engine and seeded rule dataset per `08_Rule_Engine_Dataset_Build_Instructions.md`.
- Shared National Data & Services Layer (Product Master, Compliance History, Rules Repository, Evidence Repository, Notifications, Audit Log) as shared Django apps, not per-dashboard duplicates.
- Stub services (fixed API contract, dummy/simplified internal logic) for: OCR/CV extraction, e-commerce crawler, cross-regulator checks (FSSAI/BIS/CDSCO).

## Out of scope this phase (tracked, not built yet)

- Production-accuracy OCR/CV models (stub returns plausible structured data instead).
- Real e-commerce platform API partnerships (stub screening runs against seeded listing rows).
- Real FSSAI/BIS/CDSCO integrations (stub returns a mock verification result).
- Payment gateway integration for penalties (stub "mark as paid" action).
- Real digital signature/PKI signing (watermark/stub signature block on generated PDFs).
- Elasticsearch (use PostgreSQL full-text/filter search for now).

## Functional requirements (see `06_Dashboard_Specs_All7.md` for full screen-by-screen detail)

- FR1: Every dashboard's data must reflect real state changes made from other dashboards within seconds (e.g., Officer issues Improvement Notice → Business Portal shows it on next load).
- FR2: Every compliance determination must show which rule(s), by exact section reference, were evaluated and why the verdict was reached.
- FR3: First-time vs. repeat violation classification must be computed from real Product/Brand compliance history, not hardcoded.
- FR4: All list/table screens (violation history, case lists, rule repository) must support filter and search.
- FR5: All generated reports/notices must be downloadable as PDF.
- FR6: Every state-changing action must be captured in the audit log.

## Success criteria for this phase

- A single seeded demo dataset can be walked through end-to-end across all 7 dashboards without any screen showing fake/static data.
- `PROGRESS_REPORT.md` accurately reflects stub vs. real components at all times.
- Adding an 8th future dashboard requires no changes to the existing 7 dashboards' code.
