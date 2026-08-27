# 07 — User Flow Reference (Canonical)

Transcribed from the approved user-flow diagram. This is the single source of truth for what each dashboard must actually do — every screen listed here needs a corresponding backend endpoint and frontend view. Legend from the diagram: solid arrows = happy path, red arrows = exception/no branch, dashed arrows = cross-flow/integration between lanes.

## Lane 1 — Citizen / Consumer

```mermaid
flowchart TD
    A1[Open App / Scan Product] --> A2[Capture Barcode / QR / Search]
    A2 --> A3[Retrieve Product Master & Compliance Snapshot]
    A3 --> A4[Show Public Compliance Snapshot]
    A4 --> A5{Issue Found?}
    A5 -- No --> A6[View Product / Brand Information]
    A6 --> A7[End / Continue Exploring]
    A5 -- Yes --> A8[File Complaint]
    A8 --> A9[Attach Photos / Location / Details]
    A9 --> A10[Complaint Risk Scoring & Routing]
    A10 --> A11[Route to State / District Authority]
```

## Lane 2 — Field Officer / Inspector

```mermaid
flowchart TD
    B1[Receive Inspection Target / Complaint] --> B2[Open Inspection App - Offline-First]
    B2 --> B3[Identify Product - Scan / Search]
    B3 --> B4[Guided Multi-Angle Capture - 6-Point SOP]
    B4 --> B5{Image Quality OK?}
    B5 -- No --> B4
    B5 -- Yes --> B6[AI Processing Pipeline:<br/>Panel Stitching, Layout-Aware OCR,<br/>Field Extraction/NER, Font & Placement Analysis]
    B6 --> B7[Load Rules In Force on Inspection Date]
    B7 --> B8[Rule Engine Evaluation]
    B8 --> B9[Review Findings & Confidence Score]
    B9 --> B10{Officer Confirms Violation?}
    B10 -- No --> B11[Mark Compliant / Override Finding]
    B10 -- Yes --> B12[Check Product / Brand Violation History]
```

`B12` feeds directly into Lane 3 (Enforcement Flow, center panel) at "First Procedural Violation?"

## Lane 3 — Enforcement Flow (shared: Officer + Controller)

```mermaid
flowchart TD
    C1{First Procedural Violation?} -- Yes/First Time --> C2[Draft Improvement Notice]
    C1 -- No/Repeat/Fraud/Serious --> C3[Escalate to Penalty / Prosecution]

    C2 --> C4[Officer Reviews & E-Signs]
    C4 --> C5[Serve Notice to Business]
    C5 --> C6[Start Rectification Window - e.g. 30/60 Days]
    C6 --> C7{Business Corrects Violation?}
    C7 -- Yes --> C8[Verify Rectification - Inspection/Evidence]
    C8 --> C9[Close Case]
    C7 -- No --> C3

    C3 --> C10[Supervisor / Controller Review]
    C10 --> C11{Approve Escalation?}
    C11 -- No --> C12[Return for Correction / More Evidence]
    C12 --> C4
    C11 -- Yes --> C13[Create Penalty / Prosecution Case]
    C13 --> C14[Generate Evidentiary Case Packet]
    C14 --> C15[Payment / Legal / Appeal Workflow]
    C15 --> C16[Case Closed / Appeal Tracked]
```

## Lane 4 — State Controller / Supervisory

```mermaid
flowchart TD
    D1[State Dashboard] --> D2[View Complaints, Inspections, Violations Heatmap]
    D2 --> D3[Assign Risk-Based Inspection Targets]
    D3 --> D4[Monitor SLAs & Rectification Windows]
    D4 --> D5[Review / Approve Escalations]
```

`D5` connects into Lane 3 at `C10/C11`. `D3` connects back into Lane 2 at `B1` (inspection target assignment).

## Lane 5 — National Admin / DoCA Ministry

```mermaid
flowchart TD
    E1[National Command Dashboard] --> E2[Cross-State Analytics & Trends]
    E2 --> E3[Top Violating Categories / Brands / Platforms]
    E3 --> E4[Policy Impact Simulation & Insights]
    E4 --> E5[Enforcement Strategy / Resource Allocation]
    E5 --> E6[Public Transparency Reports]
```

`E4` connects into Lane 7 (Rule Engine Admin) sandbox simulation. `E6` feeds Lane 1's public compliance snapshot.

## Lane 6 — Business Portal (Manufacturer / Importer / Seller)

```mermaid
flowchart TD
    F1[Register / Login] --> F2[Pre-Market Compliance Check]
    F2 --> F3[Upload Draft Label / Product Details]
    F3 --> F4{Compliant?}
    F4 -- Yes --> F5[Compliance Record Generated]
    F4 -- No --> F6[View Findings & Required Corrections]
    F6 --> F3
    F1 --> F7[View Violation History]
    F7 --> F8[Receive Improvement Notice]
    F8 --> F9[Submit Corrective Action & Evidence]
    F9 --> F10[Authority Verification]
    F10 --> F11{Accepted?}
    F11 -- Yes --> F12[Compliance Verified]
    F11 -- No --> F9
```

`F8` is populated from Lane 3's `C5` (Serve Notice to Business). `F9`→`F10` feeds back into Lane 3's `C8` (Verify Rectification).

## Lane 7 — E-commerce Platform (Integration Partner)

```mermaid
flowchart TD
    G1[API / Bulk Upload / Crawler Listings] --> G2[Automated Listing Screening]
    G2 --> G3{Potential Violation?}
    G3 -- No --> G4[Record Compliant Listing]
    G3 -- Yes --> G5[Create Review Queue]
    G5 --> G6[Send to Field Officer / Authority]
```

`G6` feeds into Lane 2 at `B1` (inspection target).

## Lane 8 — Rule Engine Admin (Legal / Regtech)

```mermaid
flowchart TD
    H1[Monitor Notifications - e-Gazette / PIB / DoCA Website] --> H2[AI-Assisted Rule Diff & Draft]
    H2 --> H3[Legal Officer Review & Approval]
    H3 --> H4{Approved?}
    H4 -- No --> H5[Revise Draft]
    H5 --> H3
    H4 -- Yes --> H6[Sandbox Simulation - Impact Analysis]
    H6 --> H7{Impact Acceptable?}
    H7 -- No --> H5
    H7 -- Yes --> H8[Publish Versioned Rule - with Effective Date]
    H8 --> H9[Activate on Effective Date]
```

`H9` feeds Lane 2's `B7` (Load Rules In Force on Inspection Date) and every other rule-evaluation point in the system.

## Shared National Data & Services Layer (footer — used by every lane)

- **Product Master** (GTIN / SKU / Brand)
- **Inspection & Compliance History** (versioned)
- **Rules & Amendments Repository** (versioned)
- **Document & Evidence Repository**
- **Analytics & Risk Engine** (insights)
- **Notifications & Communications**
- **Audit Logs & Digital Signatures**

Every dashboard's backend endpoints read from and write to this shared layer — never maintain a lane-local copy of Product Master, Rules, or Compliance History.

## Indirect Stakeholders / Integrations (not direct users, but data touchpoints)

- CCPA — dark-pattern / e-commerce escalations
- FSSAI — license / food compliance check
- BIS — certification verification
- CDSCO — medical device status
- National Consumer Helpline / Jagriti — grievance exchange
- Appellate Tribunal / Judiciary — receives case packets

These are integration points for Module 13 (Search/Retrieval & Cross-Regulator Checks) — build as stub API clients with the real contract, actual integration deferred per `06_Dashboard_Specs_All7.md`.
