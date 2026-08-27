# 08 — Rule Engine & Dataset: Build Instructions (v2)

Build this in Phase 2/3, before any screen that displays a compliance verdict. This is the one module the team lead should build/review personally rather than fully delegating — getting the schema wrong here breaks everything downstream.

## Step 1 — Condition-type schema (decide this before any model/migration)

A rule is not one type of check. Every rule's `condition` JSONB column stores one of these five reusable shapes, tagged by `type`:

```json
// 1. Presence
{ "type": "required_field", "field": "mfg_date", "exemptions": ["spare_parts_with_warranty"] }

// 2. Format
{ "type": "format_check", "field": "mfg_date", "format": "month_year" }

// 3. Font size / geometry
{ "type": "font_size_check", "field": "net_quantity", "min_height_mm": 2.0,
  "min_height_mm_large_pack": 6.0, "pack_size_threshold_g": 1000 }

// 4. Placement
{ "type": "placement_check", "field": "consumer_care_details",
  "must_appear_in_zone": "declaration_panel" }

// 5. Conditional applicability (category/import-specific)
{ "type": "conditional_required_field", "field": "country_of_origin",
  "applies_if": {"category": "import"} }
```

This is the single most important design decision in the whole module: adding a new legal obligation later means writing a new JSON object, not new Python code. A genuinely new condition *type* is rare — if one appears, it's one new function + one new dispatch entry, nothing else changes.

## Step 2 — Seed dataset (do this by hand, not via a scraper)

Create `backend/apps/rules_engine/fixtures/seed_rules.json` with ~15–20 **real** obligations for your 1–2 demo categories (food + electronics), each using one of the five condition types above. Don't write placeholder rules — actually encode:

- Net quantity (required + format)
- MRP (required + format)
- Manufacturer/packer/importer name & address (required)
- Month/year of manufacture (required + format, versioned pre/post the relevant amendment)
- Consumer care details (required + placement)
- Country of origin (conditional, import only)
- Net-quantity font-size minimums, including the large-pack threshold (font_size_check — this is a real distinct rule, don't flatten it to one number)
- FSSAI license number (conditional, food only)
- Best-before/use-by date (conditional, food only)

Sample entries (real, verifiable — use as your first batch):

```json
[
  {
    "rule_id_code": "PCR2011-R6-1-D-MFGDATE",
    "section_ref": "PC Rules 2011, Rule 6(1)(d)",
    "category": "general",
    "condition": {
      "type": "required_field", "field": "mfg_date",
      "exemptions": ["spare_parts_with_warranty_not_for_end_sale"]
    },
    "effective_from": "2011-01-01", "effective_to": "2024-01-01",
    "superseded_by": "PCR2023-R6-1-D-MFGDATE-V2", "status": "repealed"
  },
  {
    "rule_id_code": "PCR2023-R6-1-D-MFGDATE-V2",
    "section_ref": "PC (Amendment) Rules 2023, Rule 6(1)(d)",
    "category": "general",
    "condition": {
      "type": "required_field", "field": "mfg_date",
      "exemptions": ["spare_parts_with_warranty_not_for_end_sale"]
    },
    "effective_from": "2024-01-01", "effective_to": null, "status": "in_force"
  },
  {
    "rule_id_code": "PCR-NETQTY-FONTSIZE",
    "section_ref": "PC Rules 2011, Rule 18",
    "category": "general",
    "condition": {
      "type": "font_size_check", "field": "net_quantity",
      "min_height_mm": 2.0, "min_height_mm_large_pack": 6.0,
      "pack_size_threshold_g": 1000
    },
    "effective_from": "2011-01-01", "effective_to": null, "status": "in_force"
  },
  {
    "rule_id_code": "PCR2025-MEDDEV-PDP-EXEMPT",
    "section_ref": "PC (Packaged Commodities) Amendment Rules 2025",
    "category": "medical_device",
    "condition": {
      "type": "required_field", "field": "principal_display_panel_declaration",
      "exemptions": ["all"], "note": "Medical Devices Rules 2017 governs display instead"
    },
    "effective_from": "2025-01-01", "effective_to": null, "status": "in_force"
  },
  {
    "rule_id_code": "PCR2026-ECOMM-COO-FILTER",
    "section_ref": "PC (Packaged Commodities) Amendment Rules 2026, Rule 6(10)",
    "category": "ecommerce",
    "condition": {
      "type": "conditional_required_field", "field": "country_of_origin",
      "applies_if": {"category": "import"}
    },
    "effective_from": "2027-07-01", "effective_to": null, "status": "in_force"
  }
]
```

Write a Django management command `seed_rules.py` (`python manage.py seed_rules`) that loads this fixture, creating a matching `RuleSource` row per unique `section_ref` prefix if one doesn't exist.

## Step 3 — Checkers, dispatched by condition type

`apps/rules_engine/checks.py`:

```python
def check_required_field(condition, extracted_fields, product):
    if product.category in condition.get("exemptions", []):
        return None
    value = find_field(extracted_fields, condition["field"])
    if not value:
        return violation("missing_declaration", condition["field"])
    return None

def check_format(condition, extracted_fields, product):
    value = find_field(extracted_fields, condition["field"])
    if value and not matches_format(value, condition["format"]):
        return violation("incorrect_format", condition["field"])
    return None

def check_font_size(condition, extracted_fields, product):
    field = find_field(extracted_fields, condition["field"])
    if not field or field.font_size_mm is None:
        return None  # can't evaluate confidently — route to manual review, don't silently pass
    threshold = (condition["min_height_mm_large_pack"]
                 if product.net_qty_g > condition["pack_size_threshold_g"]
                 else condition["min_height_mm"])
    if field.font_size_mm < threshold:
        return violation("font_too_small", condition["field"])
    return None

def check_placement(condition, extracted_fields, product):
    field = find_field(extracted_fields, condition["field"])
    if field and field.placement_zone != condition["must_appear_in_zone"]:
        return violation("wrong_placement", condition["field"])
    return None

def check_conditional_required(condition, extracted_fields, product):
    if product.category != condition["applies_if"].get("category"):
        return None
    return check_required_field(condition, extracted_fields, product)

DISPATCH = {
    "required_field": check_required_field,
    "format_check": check_format,
    "font_size_check": check_font_size,
    "placement_check": check_placement,
    "conditional_required_field": check_conditional_required,
}
```

## Step 4 — Evaluator

`apps/rules_engine/evaluate.py`:

```python
def evaluate_scan(extracted_fields, product, scan_date):
    applicable_rules = Rule.objects.filter(
        category__in=[product.category, "general"],
        effective_from__lte=scan_date,
        status="in_force",
    ).filter(Q(effective_to__isnull=True) | Q(effective_to__gt=scan_date))

    violations = []
    for rule in applicable_rules:
        checker = DISPATCH.get(rule.condition["type"])
        if not checker:
            continue  # unknown condition type — log it, don't crash
        result = checker(rule.condition, extracted_fields, product)
        if result:
            violations.append({**result, "rule": rule})
    return violations
```

Keep this pure and testable — data in, violations out, no side effects. `apps/compliance` handles persistence.

## Step 5 — Unit tests (write and pass these *before* connecting to OCR stub or any dashboard)

```python
def test_missing_mfg_date_flagged():
    fields = [{"field_type": "mrp", "value": "₹149"}]  # mfg_date missing
    product = make_product(category="food")
    violations = evaluate_scan(fields, product, scan_date=date(2026, 1, 1))
    assert any(v["field"] == "mfg_date" for v in violations)

def test_exempted_category_not_flagged():
    fields = []
    product = make_product(category="spare_parts_with_warranty")
    violations = evaluate_scan(fields, product, scan_date=date(2026, 1, 1))
    assert not any(v["field"] == "mfg_date" for v in violations)

def test_rule_versioning_respected():
    # a scan dated before the 2023 amendment should evaluate against the
    # pre-amendment rule, not the post-amendment one
    ...

def test_font_size_large_pack_threshold():
    fields = [{"field_type": "net_quantity", "value": "1500g", "font_size_mm": 3.0}]
    product = make_product(category="general", net_qty_g=1500)
    violations = evaluate_scan(fields, product, scan_date=date(2026, 1, 1))
    assert any(v["field"] == "net_quantity" for v in violations)  # 3.0mm < 6.0mm large-pack min
```

If these pass against your hand-seeded data, the engine is done. Nothing built afterward (OCR stub, dashboards) should require touching this code — they only call `evaluate_scan()`.

## Step 6 — First-time vs. repeat classification

`apps/compliance/history.py`, on every new violation:

```python
def classify_and_record(product, violation):
    prior_count = ProductComplianceHistory.objects.filter(
        product=product, violation__rule=violation.rule
    ).count()
    is_first_time = prior_count == 0
    ProductComplianceHistory.objects.create(
        product=product, violation=violation, is_first_time=is_first_time
    )
    return "improvement_notice" if is_first_time else "penalty_case"
```

This is what the Officer Console's Case Creation screen calls to decide which workflow branch to show (`C1` in `07_User_Flow_Reference.md`). Test it too: same product, same rule violated a second time → must return `"penalty_case"`, not `"improvement_notice"`.

## Step 7 — Rule Admin actions (build only after Steps 1–6 pass their tests)

- `POST /api/rules/draft/` — accepts `{ notification_text, section_ref, proposed_condition }`, creates a `Rule` with `status="draft"`. The `proposed_condition` must already be in the Step 1 schema — for this phase, a legal-admin fills this via a structured form; the "AI-assisted diff from raw text" step is a real future enhancement, not built now.
- `POST /api/rules/{id}/simulate/` — reruns `evaluate_scan()` against stored historical `extracted_fields`, using the draft rule instead of the live one, and diffs the violation count.
- `POST /api/rules/{id}/publish/` — sets `effective_from`, flips `status="in_force"`, and if `superseded_by` is set on an older rule, sets that older rule's `effective_to`. No new evaluation logic — reuses Steps 3–4.

## What to tell Antigravity explicitly

"Build Steps 1–7 exactly as specified, in the `rules_engine` and `compliance` Django apps, in this order — do not skip the unit tests in Step 5 or wire this to the OCR stub/dashboards before they pass. Do not build the e-Gazette/PIB scrapers or the AI-assisted rule-drafting step yet — those are documented future enhancements, not stubs with fixed contracts like OCR is. Report in `PROGRESS_REPORT.md` that rule ingestion is manual-entry-only for now."
