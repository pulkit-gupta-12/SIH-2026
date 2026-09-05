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


def evaluate_canonical_package(
    canonical_package_data,
    product=None,
    scan_date=None,
    channel="physical",
    rules_filepath=None,
    use_db_rules=False,
    semantic_evaluator=None,
    raw_ocr_text=None,
):
    """
    Evaluates canonical package data using the LegalMetrologyRuleEngine.
    Produces structured compliance evaluation results for each rule.
    """
    from .engine import LegalMetrologyRuleEngine

    if use_db_rules:
        engine = LegalMetrologyRuleEngine.from_db(
            scan_date=scan_date,
            category=getattr(product, "category", None),
            semantic_evaluator=semantic_evaluator,
        )
    else:
        engine = LegalMetrologyRuleEngine.from_json_file(
            filepath=rules_filepath,
            semantic_evaluator=semantic_evaluator,
        )

    results = engine.evaluate(
        canonical_package_data=canonical_package_data,
        product=product,
        scan_date=scan_date,
        channel=channel,
        raw_ocr_text=raw_ocr_text,
    )
    summary = engine.summarize_results(results)

    return {
        "summary": summary,
        "results": results,
    }


