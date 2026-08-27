"""
Evaluator module for Legal Metrology Rule Engine.
Pure evaluation function: inputs (extracted_fields, product, scan_date, channel) -> list of violations.
"""
from datetime import date
from django.db.models import Q
from .models import Rule
from .checks import DISPATCH


def evaluate_scan(extracted_fields, product, scan_date=None, channel=None):
    """
    Evaluates extracted fields against all active Legal Metrology rules applicable
    to the product category and scan date.

    Args:
        extracted_fields (list): List of dicts or ExtractedField model instances.
        product (Product): Product model instance.
        scan_date (date, optional): Date of scan. Defaults to date.today().
        channel (str, optional): Scan channel ('physical' or 'ecommerce').

    Returns:
        list: List of dicts containing violation dict + matching Rule object.
    """
    if scan_date is None:
        scan_date = date.today()

    prod_cat = getattr(product, "category", "general")

    # Filter applicable rules by category and temporal validity window (effective_from <= scan_date < effective_to)
    applicable_rules = Rule.objects.filter(
        category__in=[prod_cat, "general", "ecommerce"],
        effective_from__lte=scan_date,
    ).filter(
        Q(effective_to__isnull=True) | Q(effective_to__gt=scan_date)
    )

    violations = []
    for rule in applicable_rules:
        cond = rule.condition
        cond_type = cond.get("type")
        checker = DISPATCH.get(cond_type)

        if not checker:
            continue  # Skip unhandled condition types gracefully

        res = checker(cond, extracted_fields, product, channel=channel)
        if res:
            violations.append({
                "rule": rule,
                "violation_type": res["violation_type"],
                "field": res["field"],
                "message": res["message"],
                "severity_score": res.get("severity_score", 1.0),
            })

    return violations
