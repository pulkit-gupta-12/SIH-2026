# 06 — Dashboard Specs: Screen-by-Screen (All 7)

Each row = one screen. "Node ref" points to the step in `07_User_Flow_Reference.md`. Build in this exact order within each dashboard — later screens often depend on earlier ones existing.

## 1. Citizen App

| Screen | Node ref | Backend call | Key UI elements |
|---|---|---|---|
| Scan/Search | A1–A2 | `POST /api/scans/` | Camera/barcode scanner, manual search fallback |
| Compliance Snapshot | A3–A4 | `GET /api/products/{id}/compliance-snapshot/` | Product card, `<StatusPill>`, brand info |
| Product/Brand Info | A6 | `GET /api/products/{id}/` | Read-only detail view |
| File Complaint | A8–A9 | `POST /api/complaints/` | Photo upload, location picker, description field |
| Complaint Status | A10–A11 | `GET /api/complaints/mine/` | List with routed-authority + status |

## 2. Field Officer Console

| Screen | Node ref | Backend call | Key UI elements |
|---|---|---|---|
| Inspection Queue | B1 | `GET /api/inspections/queue/` | Risk-sorted list, offline-cache indicator |
| Guided Capture | B2–B4 | `POST /api/scans/` (multi-image) | 6-step capture wizard, live quality-check feedback |
| Processing Result | B5–B8 | `GET /api/scans/{id}/processing-result/` | Extracted fields table, rule-by-rule verdict, confidence badges |
| Review Findings | B9–B11 | `POST /api/compliance-checks/{id}/confirm|override/` | Confirm/override toggle per field, notes field |
| Violation History Check | B12 | `GET /api/products/{id}/violation-history/` | Timeline view, first-time/repeat indicator |
| Case Creation | (→ Lane 3) | `POST /api/cases/` | Auto-shows Improvement Notice vs. Penalty path based on history |

## 3. State Controller Dashboard

| Screen | Node ref | Backend call | Key UI elements |
|---|---|---|---|
| State Dashboard Home | D1 | `GET /api/dashboards/state/{id}/summary/` | KPI cards |
| Heatmap/Complaints View | D2 | `GET /api/dashboards/state/{id}/summary/` | District heatmap, complaint/violation list, filters |
| Assign Targets | D3 | `POST /api/inspections/assign/` | Officer picker, risk-ranked product list, bulk-assign |
| SLA Monitor | D4 | `GET /api/cases/?status=notice_sent` | Countdown timers on rectification windows |
| Escalation Review | D5 / C10-C11 | `POST /api/cases/{id}/approve-escalation|return-for-correction/` | Case detail, evidence viewer, approve/return buttons |

## 4. National Admin Dashboard

| Screen | Node ref | Backend call | Key UI elements |
|---|---|---|---|
| National Command Home | E1 | `GET /api/dashboards/national/summary/` | Cross-state KPI cards, trend chart |
| Cross-State Analytics | E2 | `GET /api/dashboards/national/summary/?breakdown=state` | Map/bar chart by state |
| Top Violators | E3 | `GET /api/dashboards/national/top-violators/` | Ranked table: category/brand/platform |
| Policy Simulation View | E4 | `GET /api/rules/{id}/simulate/` (read-only proxy) | Impact chart, links to Rule Admin for action |
| Enforcement Strategy | E5 | `GET /api/dashboards/national/summary/` | Resource-allocation summary view |
| Public Transparency Reports | E6 | `GET /api/dashboards/national/public-reports/` | Exportable summary (feeds Citizen public view) |

## 5. Business Portal

| Screen | Node ref | Backend call | Key UI elements |
|---|---|---|---|
| Register/Login | F1 | `POST /api/auth/register/` | Standard form |
| Pre-Market Check | F2–F3 | `POST /api/products/pre-check/` | Draft label upload, category picker |
| Findings & Corrections | F4/F6 | Response of pre-check call | Rule-by-rule feedback, "fix and resubmit" loop |
| Compliance Record | F5 | `GET /api/compliance-history/mine/` | Certificate-style confirmation |
| Violation History | F7 | `GET /api/compliance-history/mine/` | Timeline, linked cases |
| Notice Response | F8–F9 | `GET /api/cases/mine/`, `POST /api/cases/{id}/corrective-action/` | Notice detail, deadline countdown, evidence upload |
| Verification Status | F10–F11 | `GET /api/cases/{id}/` | Status pill: pending/accepted/rejected |

## 6. E-commerce Integration Dashboard

| Screen | Node ref | Backend call | Key UI elements |
|---|---|---|---|
| Bulk Upload / API Status | G1 | `POST /api/ecommerce/listings/bulk/` | Upload widget, ingestion status log |
| Screening Results | G2–G4 | `GET /api/ecommerce/listings/?screening_result=compliant` | Compliant listings summary |
| Flagged Review Queue | G3/G5 | `GET /api/ecommerce/listings/flagged/` | Flagged list, reason shown per listing |
| Send to Officer | G6 | `POST /api/ecommerce/listings/{id}/send-to-officer/` | Action button, creates inspection target |

## 7. Rule Engine Admin Console

| Screen | Node ref | Backend call | Key UI elements |
|---|---|---|---|
| Notification Monitor | H1 | `GET /api/rules/incoming-notifications/` (stub feed) | List of detected/seeded notifications |
| Draft Review | H2–H3 | `POST /api/rules/draft/`, `GET /api/rules/{id}/` | Diff view: old clause vs. new clause |
| Approval Action | H4/H5 | `POST /api/rules/{id}/approve|revise/` | Approve/revise buttons, comment field |
| Sandbox Simulation | H6–H7 | `POST /api/rules/{id}/simulate/` | Before/after compliance-rate chart |
| Publish Rule | H8–H9 | `POST /api/rules/{id}/publish/` | Effective-date picker, confirmation modal |
| Rule Repository | (base view) | `GET /api/rules/` | Filterable table: status, category, effective dates |

## Cross-flow wiring checklist (build after all 7 dashboards individually work)

- [ ] Officer's Improvement Notice (`C5`) appears in Business Portal's Notice Response screen (`F8`)
- [ ] Business's corrective action (`F9`) appears in Officer/Controller's Verify Rectification screen (`C8`)
- [ ] Controller's inspection-target assignment (`D3`) appears in Officer's Queue (`B1`)
- [ ] E-commerce flagged listing (`G6`) appears in Officer's Queue (`B1`) as an inspection target
- [ ] Rule Admin's published rule (`H9`) is what Officer's Processing Result (`B7`) actually evaluates against
- [ ] National Admin's Public Transparency Reports (`E6`) feed Citizen's Compliance Snapshot (`A4`)
