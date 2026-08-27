# 04 — Frontend Specification (React + Tailwind, Mobile-First)

## Folder structure (feature-sliced)

```
frontend/
├── src/
│   ├── app/
│   │   ├── App.tsx
│   │   ├── routes.tsx           # role-based route guards
│   │   └── providers/           # auth context, query client, theme
│   ├── components/
│   │   ├── ui/                  # Button, Card, Badge, StatusPill, Modal, Table, Input
│   │   └── layout/              # AppShell, BottomNav (mobile), Sidebar (desktop), Header
│   ├── features/
│   │   ├── citizen/
│   │   │   ├── pages/           # ScanPage, ComplianceSnapshotPage, ComplaintFormPage
│   │   │   ├── components/
│   │   │   ├── api.ts
│   │   │   ├── hooks.ts
│   │   │   └── types.ts
│   │   ├── officer/
│   │   │   ├── pages/           # QueuePage, CapturePage, ReviewFindingsPage, CaseCreationPage
│   │   │   ├── components/      # GuidedCaptureFlow, ConfidenceScoreCard
│   │   │   ├── api.ts / hooks.ts / types.ts
│   │   ├── controller/
│   │   │   ├── pages/           # StateDashboardPage, HeatmapPage, EscalationApprovalPage
│   │   ├── national-admin/
│   │   │   ├── pages/           # CommandDashboardPage, TrendsPage, EcommerceScorecardPage
│   │   ├── business-portal/
│   │   │   ├── pages/           # PreCheckPage, ViolationHistoryPage, NoticeResponsePage
│   │   ├── ecommerce-integration/
│   │   │   ├── pages/           # BulkUploadPage, ReviewQueuePage
│   │   └── rule-admin/
│   │       ├── pages/           # RuleRepositoryPage, DraftReviewPage, SandboxSimulationPage
│   ├── hooks/                    # shared cross-feature hooks
│   ├── services/                 # apiClient.ts (axios/fetch wrapper), authService.ts
│   ├── store/                    # Zustand stores: authStore, notificationStore
│   ├── styles/                   # tailwind.config.js tokens, globals.css
│   ├── utils/
│   └── routes/
├── public/
├── package.json
└── tailwind.config.js
```

**Rule:** each `features/<role>` folder is self-contained — its own pages, components, API calls, types. Adding an 8th dashboard = adding an 8th `features/` folder. Never import one feature's internals directly into another; shared UI goes through `components/ui`.

## State & data-fetching

- **Server state**: React Query (`@tanstack/react-query`) for every API call — handles caching, refetch-on-focus, loading/error states uniformly across all 7 dashboards.
- **Client/UI state**: Zustand for auth session, active role, notification badges — avoid Redux boilerplate for a team this size.
- **Never** store fetched dashboard data in component state as a substitute for a query — that's how "looks dynamic but silently goes stale" bugs happen.

## Mobile-first rules

- Write every component's base (unprefixed) Tailwind classes for a ~375px viewport first; layer `md:`/`lg:` on top for desktop dashboards. Never write desktop-first and cram a mobile override in later.
- Citizen App & Officer Console: single-column layouts, bottom tab navigation (`components/layout/BottomNav.tsx`), large touch targets, camera-first primary actions.
- Controller / National / Business / Rule Admin: sidebar nav on desktop, collapsing to a bottom nav or hamburger drawer on mobile — same routes, same data, responsive layout only.

## Design system tokens (Tailwind config)

- Color-code by lane, matching the approved flow diagram's legend: Citizen = green, Officer = blue, Enforcement/shared = amber, Controller = purple, National = indigo, Business = teal/green, E-commerce = pink/red, Rule Admin = orange.
- Shared primitives in `components/ui`: `<StatusPill status="compliant|non_compliant|needs_review" />`, `<ConfidenceBadge score={0.92} />`, `<ViolationCard rule="..." evidence="..." />` — build these once, reuse across every dashboard that shows compliance data.

## Per-dashboard page → API mapping

See `06_Dashboard_Specs_All7.md` for the full screen list; each page component's `api.ts` should call exactly the endpoints listed there under `03_Backend_Specification.md`'s endpoint list — one-to-one, no ad hoc extra calls invented at the frontend layer.

## Routing & guards

`routes.tsx` defines one route tree per role, each wrapped in a `RequireRole` guard reading from `authStore`. A user hitting a route outside their role is redirected to their own dashboard's home, not shown a generic 403 page — keeps the demo smooth.
