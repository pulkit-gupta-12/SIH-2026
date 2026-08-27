# 00 — Overview & Instructions for This Build Phase

## Where we are

The platform design (PRD, architecture, rule-engine plan, module breakdown, team split) is already finalized in prior documents. This document set covers **one specific phase**: build the backend + frontend for **all seven dashboards/portals**, fully dynamic and working, before completing the remaining requirements (advanced OCR/CV accuracy, live e-commerce crawling, full cross-regulator integrations).

## The seven dashboards this phase covers

1. Citizen / Consumer App
2. Field Officer / Inspector Console
3. State Controller / Supervisory Dashboard
4. National Admin / DoCA Ministry Dashboard
5. Business Portal (Manufacturer/Importer/Packer/Seller)
6. E-commerce Platform Integration Dashboard
7. Rule Engine Admin (Legal/Regtech) Console

These map exactly to the seven lanes in `07_User_Flow_Reference.md` — that document is the canonical, unambiguous spec of what each screen must do. Read it before writing any screen.

## Non-negotiables (apply to every document in this set)

1. **Everything must be dynamic.** Every screen reads/writes through a real API backed by PostgreSQL — no hardcoded arrays standing in for a dashboard's data, ever. Where a piece of business logic (e.g., real OCR accuracy, live e-commerce crawling) isn't built yet, it must sit behind a **stub service with a fixed, realistic API contract** (see `03_Backend_Specification.md` §OCR Stub Contract) — so the dashboard code never has to change when the real logic is swapped in later.
2. **Mobile-first.** Citizen App and Field Officer Console are mobile-first by definition (single-column, bottom-nav, touch targets ≥44px, camera-first flows). Controller/National/Business/Rule-Admin dashboards are desktop-primary but must remain usable on tablet — build mobile-first CSS (base styles for small screens, `md:`/`lg:` breakpoints layer up), never the reverse.
3. **Modular, feature-sliced code.** See `03_Backend_Specification.md` and `04_Frontend_Specification.md` for the exact folder structures. A new dashboard or module added later must only require adding a new folder — never editing unrelated existing folders.
4. **Django + DRF + PostgreSQL** backend, **React + Tailwind** frontend, per prior tech-stack decisions.
5. **Rule engine & dataset**: build exactly as specified in `08_Rule_Engine_Dataset_Build_Instructions.md`. This is not optional scaffolding — the Compliance Determination logic every dashboard displays depends on it existing first.

## Build order (also see `02_Implementation_Phases_Dashboards.md` for detail)

Foundation & auth → Database schema → Rule engine & dataset seeding → Core APIs (with OCR stub) → Dashboards one at a time, in this order: **Citizen → Field Officer → Controller → National Admin → Business Portal → E-commerce → Rule Admin** → Cross-flow wiring (the dashed integration arrows in the flow diagram) → Report.

## What I need back from you (Antigravity) after each work session

Generate/update a file at the repo root called **`PROGRESS_REPORT.md`** with these exact sections:

```markdown
## What was built this session
(list of features/screens/endpoints completed, with file paths)

## What is stubbed or mocked (and why)
(anything behind a fake/dummy implementation — name the exact stub and its real-implementation TODO)

## What's left before this phase is complete
(remaining screens/endpoints/tables, in priority order)

## Known issues / risks
(anything fragile, untested, or likely to break under real data)

## Suggested next prompt
(one paragraph telling the next session exactly what to ask you to build next)
```

Do not skip this file — it's how progress gets tracked across sessions without re-reading the whole codebase each time.

## Reading order for these documents

1. `00_Overview_and_Instructions_for_Antigravity.md` (this file)
2. `07_User_Flow_Reference.md` — the exact user journeys, transcribed from the approved diagram
3. `01_PRD_Phase2_Dashboards.md` — what "done" means for this phase
4. `05_Database_Schema.md` — the data model everything else depends on
5. `08_Rule_Engine_Dataset_Build_Instructions.md` — build this before any compliance-check screen
6. `03_Backend_Specification.md` — apps, models, endpoints, folder structure
7. `04_Frontend_Specification.md` — folder structure, design system, per-dashboard component maps
8. `06_Dashboard_Specs_All7.md` — screen-by-screen build checklist per dashboard
9. `02_Implementation_Phases_Dashboards.md` — the order to actually execute all of the above
10. `09_MASTER_PROMPT_FOR_ANTIGRAVITY.md` — paste this one first; it references everything else
