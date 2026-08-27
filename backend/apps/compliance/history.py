"""
History & Violation Classification Module.
Calculates first-time vs repeat violation status and records history.
"""
from .models import ProductComplianceHistory


def classify_and_record(product, violation, case=None):
    """
    Classifies a violation as first-time vs repeat offense for a product and rule,
    persists a ProductComplianceHistory row, and determines recommended enforcement outcome.

    Args:
        product (Product): The product under check.
        violation (Violation): The Violation instance.
        case (Case, optional): Related enforcement Case.

    Returns:
        str: 'improvement_notice' if first-time, 'penalty_case' if repeat offense.
    """
    rule = getattr(violation, "rule", None)

    # Check prior violations recorded for this exact product and rule
    prior_count = ProductComplianceHistory.objects.filter(
        product=product,
        violation__rule=rule,
    ).exclude(
        violation=violation
    ).count()

    is_first_time = (prior_count == 0)

    # Create history entry
    ProductComplianceHistory.objects.create(
        product=product,
        violation=violation,
        is_first_time=is_first_time,
        case=case,
    )

    return "improvement_notice" if is_first_time else "penalty_case"
