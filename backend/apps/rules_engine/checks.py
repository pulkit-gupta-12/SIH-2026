"""
Condition Checkers for Legal Metrology Rule Engine.
Dispatched by condition['type'].
"""
import re


def find_field(extracted_fields, field_name):
    """
    Helper to extract a field dict or object from extracted_fields list.
    Handles both dicts (API inputs) and object representations.
    """
    for item in extracted_fields:
        if isinstance(item, dict):
            if item.get("field_type") == field_name:
                return item
        elif getattr(item, "field_type", None) == field_name:
            return item
    return None


def violation(violation_type, field, message, score=1.0):
    """Return structured violation result."""
    return {
        "violation_type": violation_type,
        "field": field,
        "message": message,
        "severity_score": score,
    }


def check_required_field(condition, extracted_fields, product, channel=None):
    """
    Checks presence of a required field.
    Handles category exemptions and 'all' exemptions.
    """
    exemptions = condition.get("exemptions", [])
    if "all" in exemptions or getattr(product, "category", None) in exemptions:
        return None

    field_name = condition.get("field")
    found = find_field(extracted_fields, field_name)
    if not found or not found.get("value") if isinstance(found, dict) else (not found or not getattr(found, "extracted_value", None)):
        return violation(
            violation_type="missing_declaration",
            field=field_name,
            message=f"Mandatory declaration field '{field_name}' is missing.",
            score=1.0,
        )
    return None


def check_format(condition, extracted_fields, product, channel=None):
    """
    Validates field format against standard pattern requirements.
    Supported formats: month_year, standard_metric_units, currency_inr_incl_taxes.
    """
    field_name = condition.get("field")
    found = find_field(extracted_fields, field_name)
    if not found:
        return None  # Missing field handled by required_field check

    val = found.get("value") if isinstance(found, dict) else getattr(found, "extracted_value", "")
    val_str = str(val or "").strip()

    fmt_type = condition.get("format")

    if fmt_type == "month_year":
        # Format MM/YYYY or Mon YYYY or YYYY-MM
        pattern = r"^(\d{2}/\d{4}|\d{4}-\d{2}|[A-Za-z]{3}\s+\d{4}|\d{2}-\d{4})$"
        if not re.match(pattern, val_str):
            return violation(
                violation_type="incorrect_format",
                field=field_name,
                message=f"Field '{field_name}' value '{val_str}' does not match required format Month/Year.",
                score=0.8,
            )

    elif fmt_type == "standard_metric_units":
        # Must contain standard metric unit (g, kg, ml, l, m, cm, mm, N, u)
        pattern = r"^[\d\.]+\s*(g|kg|ml|l|L|m|cm|mm|N|u|pack|units)$"
        if not re.match(pattern, val_str, re.IGNORECASE):
            return violation(
                violation_type="incorrect_format",
                field=field_name,
                message=f"Field '{field_name}' value '{val_str}' must use standard metric units (g, kg, ml, L).",
                score=0.8,
            )

    elif fmt_type == "currency_inr_incl_taxes":
        # Must specify INR / ₹ / Rs and mention inclusive of all taxes
        has_currency = bool(re.search(r"(₹|rs\.?|inr)", val_str, re.IGNORECASE))
        has_taxes = bool(re.search(r"incl.*tax|inclusive", val_str, re.IGNORECASE))
        if not (has_currency and has_taxes):
            return violation(
                violation_type="incorrect_format",
                field=field_name,
                message=f"MRP declaration '{val_str}' must state INR (₹/Rs) and 'inclusive of all taxes'.",
                score=0.8,
            )

    return None


def check_font_size(condition, extracted_fields, product, channel=None):
    """
    Checks height minimums of mandatory declarations.
    Respects pack size thresholds for large packages.
    """
    field_name = condition.get("field")
    found = find_field(extracted_fields, field_name)

    if not found:
        return None

    font_size_mm = found.get("font_size_mm") if isinstance(found, dict) else getattr(found, "font_size_mm", None)
    if font_size_mm is None:
        return None  # Cannot determine font size from scan image

    # Determine threshold based on product size/weight
    threshold_g = condition.get("pack_size_threshold_g", 1000)
    net_qty_g = getattr(product, "net_qty_g", 0) or 0

    if net_qty_g > threshold_g and "min_height_mm_large_pack" in condition:
        required_min = condition["min_height_mm_large_pack"]
    else:
        required_min = condition.get("min_height_mm", 2.0)

    if float(font_size_mm) < float(required_min):
        return violation(
            violation_type="font_too_small",
            field=field_name,
            message=f"Font height for '{field_name}' is {font_size_mm}mm, below minimum required {required_min}mm.",
            score=0.7,
        )
    return None


def check_placement(condition, extracted_fields, product, channel=None):
    """
    Validates placement zone of field (e.g. declaration_panel).
    """
    field_name = condition.get("field")
    found = find_field(extracted_fields, field_name)
    if not found:
        return None

    zone = found.get("placement_zone") if isinstance(found, dict) else getattr(found, "placement_zone", None)
    required_zone = condition.get("must_appear_in_zone")

    if required_zone and zone and zone != required_zone:
        return violation(
            violation_type="wrong_placement",
            field=field_name,
            message=f"Field '{field_name}' placed in '{zone}', must appear in '{required_zone}'.",
            score=0.6,
        )
    return None


def check_conditional_required(condition, extracted_fields, product, channel=None):
    """
    Checks field requirement conditional on category or channel (e.g., import, food, e-commerce).
    """
    applies_if = condition.get("applies_if", {})

    req_category = applies_if.get("category")
    prod_category = getattr(product, "category", None)
    if req_category and prod_category != req_category:
        return None

    req_channel = applies_if.get("channel")
    if req_channel:
        current_channel = channel or "physical"
        if req_channel != current_channel:
            return None

    # Delegate to required field check
    return check_required_field(condition, extracted_fields, product, channel=channel)


# Dispatch map
DISPATCH = {
    "required_field": check_required_field,
    "format_check": check_format,
    "font_size_check": check_font_size,
    "placement_check": check_placement,
    "conditional_required_field": check_conditional_required,
}
