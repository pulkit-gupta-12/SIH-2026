# 09 — MASTER PROMPT FOR ANTIGRAVITY

Paste this as your opening prompt, with the other 8 documents attached/available in the same workspace.

---

You are building the backend and frontend for a national Legal Metrology compliance platform. I'm giving you 8 supporting documents in this workspace — read them in this order before writing any code:

1. `00_Overview_and_Instructions.md`
2. `07_User_Flow_Reference.md`
3. `01_PRD_Phase2_Dashboards.md`
4. `05_Database_Schema.md`
5. `08_Rule_Engine_Dataset_Build_Instructions.md`
6. `03_Backend_Specification.md`
7. `04_Frontend_Specification.md`
8. `06_Dashboard_Specs_All7.md`
9. `02_Implementation_Phases_Dashboards.md`

**Your task:** implement Phases 1 through 6 exactly as sequenced in `02_Implementation_Phases_Dashboards.md`. Build the backend in Django + Django REST Framework + PostgreSQL, exactly matching the folder structure and app breakdown in `03_Backend_Specification.md`. Build the frontend in React + Tailwind CSS, mobile-first, exactly matching the folder structure in `04_Frontend_Specification.md`.

**Hard constraints — do not deviate from these:**

1. Every dashboard screen must be backed by a real API call to a real PostgreSQL-persisted table. Never hardcode dashboard data in the frontend, even temporarily — if a piece of logic isn't ready, build it as a stub *service* with a fixed API contract (see the OCR Stub Contract in `03_Backend_Specification.md` as the pattern to replicate for e-commerce screening and cross-regulator checks), not as fake frontend data.
2. Follow the folder structures in the backend/frontend spec docs exactly. A new module must always be addable as a new folder, never by editing unrelated existing folders.
3. Mobile-first CSS everywhere — base Tailwind classes target a ~375px viewport, desktop styles layered on top with `md:`/`lg:` prefixes.
4. Build the rule engine and seed the rule dataset (`08_Rule_Engine_Dataset_Build_Instructions.md`) before building any screen that displays a compliance verdict — this is a hard dependency, not a suggestion.
5. Implement the seven dashboards in this exact order: Citizen → Field Officer → State Controller → National Admin → Business Portal → E-commerce Integration → Rule Engine Admin. Each dashboard's screens are listed row-by-row in `06_Dashboard_Specs_All7.md` — build every row.
6. After wiring all seven dashboards individually, work through the "Cross-flow wiring checklist" at the end of `06_Dashboard_Specs_All7.md` and verify each item actually works across two logged-in sessions.
7. Explicitly out of scope for this phase (build as documented stubs, do not attempt the real thing): production-accuracy OCR/CV models, live e-commerce platform API partnerships, real FSSAI/BIS/CDSCO integrations, payment gateway, real digital signature/PKI, Elasticsearch, and the e-Gazette/PIB regulatory-change watcher scrapers.

**What I need back from you after every work session:** update a file at the repo root, `PROGRESS_REPORT.md`, with exactly these sections — What was built this session / What is stubbed or mocked (and why) / What's left before this phase is complete / Known issues or risks / Suggested next prompt. Keep this file accurate at all times; I will read it before giving you the next instruction, so don't let it go stale or overstate what's actually working.

Start with Phase 1 (Foundation) now. Confirm the folder structure you've created and the auth/RBAC placeholder pages are working before moving to Phase 2, and update `PROGRESS_REPORT.md` at the end of this phase.
