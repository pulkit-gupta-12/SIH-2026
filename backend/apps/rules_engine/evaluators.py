"""
Deterministic Compliance Evaluators for Legal Metrology (Packaged Commodities) Rules.

Every evaluator produces a structured result:
{
    "rule_id": str,
    "status": "PASS" | "FAIL" | "WARNING" | "REVIEW" | "NOT_APPLICABLE",
    "severity": "LOW" | "MEDIUM" | "HIGH" | "CRITICAL",
    "confidence": float,
    "evidence": {
        "field": str,
        "raw_value": str or None,
        "normalized_value": dict or any,
    },
    "reason": str,
    "requires_human_review": bool
}

CRITICAL:
The engine strictly distinguishes:
1. NOT_DETECTED_BY_OCR -> status: "REVIEW", requires_human_review: True
2. DEFINITELY_ABSENT -> status: "FAIL", requires_human_review: False
3. PRESENT -> status: "PASS" (or "FAIL" if non-compliant format/value)
4. UNCERTAIN (low confidence < 0.6 or ambiguous) -> status: "REVIEW", requires_human_review: True
"""

import re
from typing import Any, Dict, List, Optional, Tuple


# Thresholds for OCR confidence
OCR_CONFIDENCE_RELIABLE = 0.60
USP_ROUNDING_TOLERANCE = 0.05  # 5 paise / unit tolerance for rounding differences


def build_result(
    rule_id: str,
    status: str,
    severity: str,
    confidence: float,
    field: str,
    raw_val: Optional[str],
    norm_val: Any,
    reason: str,
    requires_human_review: bool = False,
) -> Dict[str, Any]:
    """Helper to construct standard structured rule evaluation result."""
    return {
        "rule_id": rule_id,
        "status": status,
        "severity": severity,
        "confidence": round(confidence, 2),
        "evidence": {
            "field": field,
            "raw_value": raw_val,
            "normalized_value": norm_val,
        },
        "reason": reason,
        "requires_human_review": requires_human_review,
    }


def evaluate_required_field(
    rule: Dict[str, Any],
    field_key: str,
    field_data: Dict[str, Any],
    product: Any = None,
    context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Evaluates required field presence according to Legal Metrology mandates.
    Checks exemptions, detection state, and OCR confidence.
    """
    rule_id = rule.get("rule_id_code", "UNKNOWN_RULE")
    cond = rule.get("condition") or {}
    exemptions = cond.get("exemptions", [])
    prod_cat = str(getattr(product, "category", None) or (context.get("category") if context else None) or "general").lower()

    # 1. Exemption checks
    if "all" in exemptions:
        return build_result(
            rule_id=rule_id,
            status="NOT_APPLICABLE",
            severity="LOW",
            confidence=1.0,
            field=field_key,
            raw_val=None,
            norm_val=None,
            reason=f"Exempt from required declaration under statutory exemption clause.",
            requires_human_review=False,
        )

    # Check category exemptions (e.g. food articles exempt from Rule 6(1)(a) / 6(1)(d))
    for ex in exemptions:
        if isinstance(ex, str) and prod_cat in ex.lower():
            return build_result(
                rule_id=rule_id,
                status="NOT_APPLICABLE",
                severity="LOW",
                confidence=1.0,
                field=field_key,
                raw_val=None,
                norm_val=None,
                reason=f"Category '{prod_cat}' is exempt under: {ex}",
                requires_human_review=False,
            )

    # Context override: definitely confirmed absent by officer inspection
    is_confirmed_absent = bool(context and context.get("confirmed_absent_fields", {}).get(field_key))

    # 2. Check presence in canonical field data
    detected = field_data.get("detected", False)
    raw_val = field_data.get("raw")
    norm_val = field_data.get("normalized")
    norm_status = field_data.get("normalization_status", "not_detected")
    conf = field_data.get("confidence") or 0.0

    if not detected or norm_status == "not_detected":
        if is_confirmed_absent:
            return build_result(
                rule_id=rule_id,
                status="FAIL",
                severity="HIGH",
                confidence=1.0,
                field=field_key,
                raw_val=None,
                norm_val=None,
                reason=f"Mandatory declaration '{field_key}' is confirmed absent from package.",
                requires_human_review=False,
            )
        # Safe handling: NOT_DETECTED_BY_OCR -> REVIEW (never falsely claim violation)
        return build_result(
            rule_id=rule_id,
            status="REVIEW",
            severity="HIGH",
            confidence=0.5,
            field=field_key,
            raw_val=None,
            norm_val=None,
            reason=f"REVIEW — Mandatory declaration '{field_key}' was not reliably detected by OCR. Visual confirmation required.",
            requires_human_review=True,
        )

    # 3. Check uncertain OCR state
    if conf < OCR_CONFIDENCE_RELIABLE or norm_status == "ambiguous":
        return build_result(
            rule_id=rule_id,
            status="REVIEW",
            severity="MEDIUM",
            confidence=conf,
            field=field_key,
            raw_val=raw_val,
            norm_val=norm_val,
            reason=f"Declaration '{field_key}' was detected with low confidence ({conf*100:.0f}%) or ambiguity ('{field_data.get('ambiguity')}'). Officer review recommended.",
            requires_human_review=True,
        )

    # 4. Field is cleanly present
    return build_result(
        rule_id=rule_id,
        status="PASS",
        severity="HIGH",
        confidence=conf or 0.95,
        field=field_key,
        raw_val=raw_val,
        norm_val=norm_val,
        reason=f"Mandatory declaration '{field_key}' is clearly present.",
        requires_human_review=False,
    )


def evaluate_format(
    rule: Dict[str, Any],
    field_key: str,
    field_data: Dict[str, Any],
    product: Any = None,
    context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Evaluates format requirements:
    - currency_inr_incl_taxes / retail sale price format (PCR2011-R2-M-MRP-FORMAT)
    - month_year (PCR2011-R6-1-D-MFGDATE-FMT)
    - standard_metric_units (PCR2011-R6-1-C-NETQTY-FMT)
    - no 'when packed' expressions (PCR2011-R11-2-NOWHENPACKED)
    - no exaggerated/misleading impressions (PCR2011-R12-6-NOEXAGGERATION)
    """
    rule_id = rule.get("rule_id_code", "UNKNOWN_RULE")
    cond = rule.get("condition") or {}
    fmt_spec = cond.get("format", "")

    if not field_data.get("detected", False):
        return build_result(
            rule_id=rule_id,
            status="REVIEW",
            severity="HIGH",
            confidence=0.5,
            field=field_key,
            raw_val=None,
            norm_val=None,
            reason=f"Cannot verify format because '{field_key}' was not detected by OCR.",
            requires_human_review=True,
        )

    raw_val = str(field_data.get("raw") or "").strip()
    norm_val = field_data.get("normalized")
    conf = field_data.get("confidence") or 0.90

    # 1. Currency & Inclusive of All Taxes Format
    if fmt_spec == "currency_inr_incl_taxes" or "inclusive of all taxes" in fmt_spec.lower():
        has_currency = bool(re.search(r"(₹|rs\.?|inr)", raw_val, re.IGNORECASE))
        has_taxes = bool(re.search(r"incl.*tax|inclusive", raw_val, re.IGNORECASE))

        if has_currency and has_taxes:
            return build_result(
                rule_id=rule_id,
                status="PASS",
                severity="HIGH",
                confidence=conf,
                field=field_key,
                raw_val=raw_val,
                norm_val=norm_val,
                reason="MRP declaration correctly states currency and 'inclusive of all taxes'.",
                requires_human_review=False,
            )
        elif has_currency and not has_taxes:
            return build_result(
                rule_id=rule_id,
                status="FAIL",
                severity="HIGH",
                confidence=conf,
                field=field_key,
                raw_val=raw_val,
                norm_val=norm_val,
                reason=f"MRP statement '{raw_val}' states currency but lacks mandatory 'inclusive of all taxes' declaration.",
                requires_human_review=False,
            )
        else:
            return build_result(
                rule_id=rule_id,
                status="FAIL",
                severity="HIGH",
                confidence=conf,
                field=field_key,
                raw_val=raw_val,
                norm_val=norm_val,
                reason=f"Retail price declaration '{raw_val}' does not comply with Rule 2(m) format.",
                requires_human_review=False,
            )

    # 2. Month / Year Format
    if fmt_spec == "month_year" or "month and year" in fmt_spec.lower():
        if isinstance(norm_val, dict) and norm_val.get("month") and norm_val.get("year"):
            return build_result(
                rule_id=rule_id,
                status="PASS",
                severity="HIGH",
                confidence=conf,
                field=field_key,
                raw_val=raw_val,
                norm_val=norm_val,
                reason=f"Date conforms to standard Month/Year format ({norm_val.get('date_iso')}).",
                requires_human_review=False,
            )
        # Fallback to pattern on raw
        pattern = r"^(\d{2}/\d{4}|\d{4}-\d{2}|[A-Za-z]{3}\s+\d{4}|\d{2}-\d{4})$"
        cleaned = re.sub(r"^(?:MFG|MFD|EXP|PKD|DATE)[\:\.\s\-]*", "", raw_val, flags=re.IGNORECASE).strip()
        if re.match(pattern, cleaned):
            return build_result(
                rule_id=rule_id,
                status="PASS",
                severity="HIGH",
                confidence=conf,
                field=field_key,
                raw_val=raw_val,
                norm_val=norm_val,
                reason=f"Date '{raw_val}' matches valid Month/Year pattern.",
                requires_human_review=False,
            )
        return build_result(
            rule_id=rule_id,
            status="FAIL",
            severity="HIGH",
            confidence=conf,
            field=field_key,
            raw_val=raw_val,
            norm_val=norm_val,
            reason=f"Date '{raw_val}' does not match required Month/Year format (MM/YYYY).",
            requires_human_review=False,
        )

    # 3. Standard Metric Units Format
    if fmt_spec == "standard_metric_units":
        if isinstance(norm_val, dict) and norm_val.get("unit"):
            unit = str(norm_val.get("unit")).lower()
            if unit in ["g", "kg", "ml", "l", "m", "cm", "mm", "n", "units", "pieces", "pack"]:
                return build_result(
                    rule_id=rule_id,
                    status="PASS",
                    severity="HIGH",
                    confidence=conf,
                    field=field_key,
                    raw_val=raw_val,
                    norm_val=norm_val,
                    reason=f"Net quantity uses approved standard metric unit ('{unit}').",
                    requires_human_review=False,
                )
        return build_result(
            rule_id=rule_id,
            status="FAIL",
            severity="HIGH",
            confidence=conf,
            field=field_key,
            raw_val=raw_val,
            norm_val=norm_val,
            reason=f"Net quantity '{raw_val}' must use standard metric units (g, kg, ml, l, N).",
            requires_human_review=False,
        )

    # 4. Prohibited 'when packed' expression (Rule 11(2))
    if "when packed" in fmt_spec.lower() and "not be qualified" in fmt_spec.lower():
        if re.search(r"\bwhen\s+packed\b", raw_val, re.IGNORECASE):
            return build_result(
                rule_id=rule_id,
                status="FAIL",
                severity="HIGH",
                confidence=conf,
                field=field_key,
                raw_val=raw_val,
                norm_val=norm_val,
                reason=f"Declaration contains prohibited qualification 'when packed' under Rule 11(2).",
                requires_human_review=False,
            )
        return build_result(
            rule_id=rule_id,
            status="PASS",
            severity="MEDIUM",
            confidence=conf,
            field=field_key,
            raw_val=raw_val,
            norm_val=norm_val,
            reason="Net quantity is not improperly qualified by 'when packed'.",
            requires_human_review=False,
        )

    # 5. Prohibited exaggerated/misleading impressions (Rule 12(6))
    if "exaggerated" in fmt_spec.lower() or "misleading" in fmt_spec.lower():
        prohibited_words = ["minimum", "not less than", "approx", "approximate", "average"]
        found_words = [w for w in prohibited_words if re.search(rf"\b{re.escape(w)}\b", raw_val, re.IGNORECASE)]
        if found_words:
            return build_result(
                rule_id=rule_id,
                status="FAIL",
                severity="HIGH",
                confidence=conf,
                field=field_key,
                raw_val=raw_val,
                norm_val=norm_val,
                reason=f"Net quantity contains misleading expression '{found_words[0]}' prohibited under Rule 12(6).",
                requires_human_review=False,
            )
        return build_result(
            rule_id=rule_id,
            status="PASS",
            severity="MEDIUM",
            confidence=conf,
            field=field_key,
            raw_val=raw_val,
            norm_val=norm_val,
            reason="Net quantity contains no prohibited exaggerated terms.",
            requires_human_review=False,
        )

    # Generic pass if no failure condition hit
    return build_result(
        rule_id=rule_id,
        status="PASS",
        severity="LOW",
        confidence=conf,
        field=field_key,
        raw_val=raw_val,
        norm_val=norm_val,
        reason=f"Field format complies with specification: {fmt_spec[:60]}.",
        requires_human_review=False,
    )


def evaluate_numeric(
    rule: Dict[str, Any],
    field_key: str,
    field_data: Dict[str, Any],
    product: Any = None,
    context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Evaluates numeric rules (e.g. price > 0, quantity > 0).
    """
    rule_id = rule.get("rule_id_code", "UNKNOWN_RULE")
    if not field_data.get("detected", False):
        return build_result(
            rule_id=rule_id,
            status="REVIEW",
            severity="HIGH",
            confidence=0.5,
            field=field_key,
            raw_val=None,
            norm_val=None,
            reason=f"Cannot verify numeric value: '{field_key}' not detected by OCR.",
            requires_human_review=True,
        )

    norm_val = field_data.get("normalized")
    raw_val = field_data.get("raw")
    conf = field_data.get("confidence") or 0.90

    # MRP Numeric Check
    if field_key == "mrp" and isinstance(norm_val, dict):
        amt = norm_val.get("amount", 0)
        if amt <= 0:
            return build_result(
                rule_id=rule_id,
                status="FAIL",
                severity="CRITICAL",
                confidence=conf,
                field=field_key,
                raw_val=raw_val,
                norm_val=norm_val,
                reason=f"MRP must be a positive number, found {amt}.",
                requires_human_review=False,
            )
        return build_result(
            rule_id=rule_id,
            status="PASS",
            severity="HIGH",
            confidence=conf,
            field=field_key,
            raw_val=raw_val,
            norm_val=norm_val,
            reason=f"MRP amount {amt} is a valid positive value.",
            requires_human_review=False,
        )

    # Net Quantity Numeric Check
    if field_key == "net_quantity" and isinstance(norm_val, dict):
        qty = norm_val.get("quantity", 0)
        if qty <= 0:
            return build_result(
                rule_id=rule_id,
                status="FAIL",
                severity="HIGH",
                confidence=conf,
                field=field_key,
                raw_val=raw_val,
                norm_val=norm_val,
                reason=f"Net quantity must be greater than zero, found {qty}.",
                requires_human_review=False,
            )
        return build_result(
            rule_id=rule_id,
            status="PASS",
            severity="HIGH",
            confidence=conf,
            field=field_key,
            raw_val=raw_val,
            norm_val=norm_val,
            reason=f"Net quantity {qty} {norm_val.get('unit')} is a valid positive quantity.",
            requires_human_review=False,
        )

    return build_result(
        rule_id=rule_id,
        status="PASS",
        severity="LOW",
        confidence=conf,
        field=field_key,
        raw_val=raw_val,
        norm_val=norm_val,
        reason="Numeric validation passed.",
        requires_human_review=False,
    )


def evaluate_date(
    rule: Dict[str, Any],
    canonical_data: Dict[str, Any],
    product: Any = None,
    context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Evaluates chronological consistency (e.g. expiry_date >= mfg_date).
    """
    rule_id = rule.get("rule_id_code", "UNKNOWN_RULE")
    mfg = canonical_data.get("mfg_date", {})
    exp = canonical_data.get("expiry_date", {})

    if not mfg.get("detected") or not exp.get("detected"):
        return build_result(
            rule_id=rule_id,
            status="NOT_APPLICABLE",
            severity="MEDIUM",
            confidence=1.0,
            field="dates",
            raw_val=None,
            norm_val=None,
            reason="Date sequence check requires both manufacturing and expiry dates to be present.",
            requires_human_review=False,
        )

    mfg_norm = mfg.get("normalized") or {}
    exp_norm = exp.get("normalized") or {}

    m_year = mfg_norm.get("year")
    m_month = mfg_norm.get("month", 1)
    e_year = exp_norm.get("year")
    e_month = exp_norm.get("month", 1)

    if m_year and e_year:
        if (e_year, e_month) < (m_year, m_month):
            return build_result(
                rule_id=rule_id,
                status="FAIL",
                severity="CRITICAL",
                confidence=0.95,
                field="expiry_date",
                raw_val=f"Mfg: {mfg.get('raw')} | Exp: {exp.get('raw')}",
                norm_val={"mfg": mfg_norm, "expiry": exp_norm},
                reason=f"Expiry date ({e_year}-{e_month:02d}) precedes manufacturing date ({m_year}-{m_month:02d}).",
                requires_human_review=False,
            )
        return build_result(
            rule_id=rule_id,
            status="PASS",
            severity="HIGH",
            confidence=0.95,
            field="expiry_date",
            raw_val=f"Mfg: {mfg.get('raw')} | Exp: {exp.get('raw')}",
            norm_val={"mfg": mfg_norm, "expiry": exp_norm},
            reason=f"Expiry date chronologically follows manufacturing date.",
            requires_human_review=False,
        )

    return build_result(
        rule_id=rule_id,
        status="REVIEW",
        severity="MEDIUM",
        confidence=0.5,
        field="expiry_date",
        raw_val=f"Mfg: {mfg.get('raw')} | Exp: {exp.get('raw')}",
        norm_val=None,
        reason="Unable to compare dates due to incomplete date components.",
        requires_human_review=True,
    )


def evaluate_calculation(
    rule: Dict[str, Any],
    canonical_data: Dict[str, Any],
    product: Any = None,
    context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Evaluates calculation consistency:
    Unit Sale Price (USP) = Total MRP / Total Net Quantity
    """
    rule_id = rule.get("rule_id_code", "PCR-USP-CALCULATION")
    mrp_field = canonical_data.get("mrp", {})
    qty_field = canonical_data.get("net_quantity", {})
    usp_field = canonical_data.get("unit_sale_price", {})

    if not usp_field.get("detected"):
        return build_result(
            rule_id=rule_id,
            status="NOT_APPLICABLE",
            severity="MEDIUM",
            confidence=1.0,
            field="unit_sale_price",
            raw_val=None,
            norm_val=None,
            reason="Unit Sale Price was not declared, calculation check not applicable.",
            requires_human_review=False,
        )

    if not mrp_field.get("detected") or not qty_field.get("detected"):
        return build_result(
            rule_id=rule_id,
            status="REVIEW",
            severity="MEDIUM",
            confidence=0.6,
            field="unit_sale_price",
            raw_val=usp_field.get("raw"),
            norm_val=usp_field.get("normalized"),
            reason="Cannot verify Unit Sale Price calculation because MRP or Net Quantity is missing.",
            requires_human_review=True,
        )

    mrp_norm = mrp_field.get("normalized") or {}
    qty_norm = qty_field.get("normalized") or {}
    usp_norm = usp_field.get("normalized") or {}

    total_mrp = mrp_norm.get("amount")
    total_qty = qty_norm.get("quantity")
    declared_usp = usp_norm.get("amount")

    if not total_mrp or not total_qty or not declared_usp or total_qty <= 0:
        return build_result(
            rule_id=rule_id,
            status="REVIEW",
            severity="LOW",
            confidence=0.6,
            field="unit_sale_price",
            raw_val=usp_field.get("raw"),
            norm_val=usp_norm,
            reason="Non-numeric or zero components prevent Unit Sale Price verification.",
            requires_human_review=True,
        )

    expected_usp = total_mrp / total_qty
    diff = abs(expected_usp - declared_usp)

    if diff <= USP_ROUNDING_TOLERANCE:
        return build_result(
            rule_id=rule_id,
            status="PASS",
            severity="HIGH",
            confidence=0.95,
            field="unit_sale_price",
            raw_val=usp_field.get("raw"),
            norm_val={"declared_usp": declared_usp, "calculated_usp": round(expected_usp, 4)},
            reason=f"Declared Unit Sale Price ({declared_usp}) matches calculated value ({expected_usp:.2f}).",
            requires_human_review=False,
        )

    return build_result(
        rule_id=rule_id,
        status="WARNING",
        severity="HIGH",
        confidence=0.90,
        field="unit_sale_price",
        raw_val=usp_field.get("raw"),
        norm_val={"declared_usp": declared_usp, "calculated_usp": round(expected_usp, 4)},
        reason=f"Unit Sale Price mismatch: declared {declared_usp}, calculated {expected_usp:.2f} (MRP {total_mrp} / Qty {total_qty}).",
        requires_human_review=True,
    )


def evaluate_conditional(
    rule: Dict[str, Any],
    field_key: str,
    field_data: Dict[str, Any],
    product: Any = None,
    context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Evaluates conditional required field rules (e.g. food -> FSSAI, import -> Country of Origin).
    """
    rule_id = rule.get("rule_id_code", "UNKNOWN_RULE")
    cond = rule.get("condition") or {}
    applies_if = cond.get("applies_if", {})

    prod_cat = getattr(product, "category", None) or (context.get("category") if context else "general")
    channel = (context.get("channel") if context else None) or "physical"

    # Verify precondition
    req_cat = applies_if.get("category")
    if req_cat and prod_cat != req_cat:
        return build_result(
            rule_id=rule_id,
            status="NOT_APPLICABLE",
            severity="LOW",
            confidence=1.0,
            field=field_key,
            raw_val=None,
            norm_val=None,
            reason=f"Rule conditionally applies only to '{req_cat}' (current product category: '{prod_cat}').",
            requires_human_review=False,
        )

    req_channel = applies_if.get("channel")
    if req_channel and channel != req_channel:
        return build_result(
            rule_id=rule_id,
            status="NOT_APPLICABLE",
            severity="LOW",
            confidence=1.0,
            field=field_key,
            raw_val=None,
            norm_val=None,
            reason=f"Rule conditionally applies only to '{req_channel}' channel (current: '{channel}').",
            requires_human_review=False,
        )

    # Condition applies -> evaluate field presence
    return evaluate_required_field(rule, field_key, field_data, product=product, context=context)


def evaluate_placement(
    rule: Dict[str, Any],
    field_key: str,
    field_data: Dict[str, Any],
    product: Any = None,
    context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Evaluates placement zone compliance (e.g. declaration_panel vs principal_display_panel).
    """
    rule_id = rule.get("rule_id_code", "UNKNOWN_RULE")
    cond = rule.get("condition") or {}
    required_zone = cond.get("must_appear_in_zone")

    if not field_data.get("detected"):
        return build_result(
            rule_id=rule_id,
            status="REVIEW",
            severity="MEDIUM",
            confidence=0.5,
            field=field_key,
            raw_val=None,
            norm_val=None,
            reason=f"Cannot verify placement zone: '{field_key}' not detected by OCR.",
            requires_human_review=True,
        )

    actual_zone = field_data.get("source_panel") or "unknown"
    conf = field_data.get("confidence") or 0.85

    if required_zone and actual_zone != "unknown" and actual_zone != required_zone:
        # Check if placement in different panel violates rule
        return build_result(
            rule_id=rule_id,
            status="FAIL",
            severity="MEDIUM",
            confidence=conf,
            field=field_key,
            raw_val=field_data.get("raw"),
            norm_val=field_data.get("normalized"),
            reason=f"Field '{field_key}' appeared in '{actual_zone}', but must appear in '{required_zone}'.",
            requires_human_review=False,
        )

    return build_result(
        rule_id=rule_id,
        status="PASS",
        severity="LOW",
        confidence=conf,
        field=field_key,
        raw_val=field_data.get("raw"),
        norm_val=field_data.get("normalized"),
        reason=f"Placement complies with required zone ('{required_zone}').",
        requires_human_review=False,
    )


def evaluate_font_size(
    rule: Dict[str, Any],
    field_key: str,
    field_data: Dict[str, Any],
    product: Any = None,
    context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Evaluates numeral / letter font height in millimeters against Rule 18 minimums.
    """
    rule_id = rule.get("rule_id_code", "UNKNOWN_RULE")
    cond = rule.get("condition") or {}

    font_size = field_data.get("font_size_mm")
    if font_size is None and field_data.get("bbox"):
        # Bbox present but physical scale factor unavailable
        return build_result(
            rule_id=rule_id,
            status="REVIEW",
            severity="LOW",
            confidence=0.5,
            field=field_key,
            raw_val=field_data.get("raw"),
            norm_val=None,
            reason="Physical scale factor unavailable from scan image; font size in mm cannot be measured automatically.",
            requires_human_review=True,
        )

    if font_size is None:
        return build_result(
            rule_id=rule_id,
            status="REVIEW",
            severity="LOW",
            confidence=0.5,
            field=field_key,
            raw_val=field_data.get("raw"),
            norm_val=None,
            reason="Font size cannot be determined from current image resolution.",
            requires_human_review=True,
        )

    required_min = cond.get("min_height_mm", 2.0)
    conf = field_data.get("confidence") or 0.90

    if float(font_size) < float(required_min):
        return build_result(
            rule_id=rule_id,
            status="FAIL",
            severity="MEDIUM",
            confidence=conf,
            field=field_key,
            raw_val=f"{font_size} mm",
            norm_val={"font_size_mm": font_size, "required_min_mm": required_min},
            reason=f"Font height ({font_size} mm) is below statutory minimum ({required_min} mm).",
            requires_human_review=False,
        )

    return build_result(
        rule_id=rule_id,
        status="PASS",
        severity="MEDIUM",
        confidence=conf,
        field=field_key,
        raw_val=f"{font_size} mm",
        norm_val={"font_size_mm": font_size, "required_min_mm": required_min},
        reason=f"Font height ({font_size} mm) meets statutory minimum ({required_min} mm).",
        requires_human_review=False,
    )


def evaluate_qualitative_manual(
    rule: Dict[str, Any],
    canonical_data: Dict[str, Any],
    product: Any = None,
    context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Evaluates qualitative statutory rules that lack deterministic regex conditions
    (e.g., deceptive packaging, color contrast, advertisements, inspection clauses).
    Deterministically flags them for human officer review without fabricating a violation.
    """
    rule_id = rule.get("rule_id_code", "UNKNOWN_RULE")
    section_ref = rule.get("section_ref", "")
    raw_clause = rule.get("raw_text", "")

    return build_result(
        rule_id=rule_id,
        status="REVIEW",
        severity="LOW",
        confidence=1.0,
        field="general_compliance",
        raw_val=raw_clause[:100] if raw_clause else None,
        norm_val=None,
        reason=f"Statutory clause ({section_ref}) requires physical verification or qualitative judgment.",
        requires_human_review=True,
    )
