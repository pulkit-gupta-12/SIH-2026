"""
Compliance models: ComplianceCheck, Violation, ProductComplianceHistory.
Matches schema from 05_Database_Schema.md.
"""
from django.conf import settings
from django.db import models


class ComplianceCheck(models.Model):
    """
    Compliance Checks table.
    Fields: id, scan_id (FK/OneToOne), verdict (compliant/non_compliant/needs_review),
    overall_confidence, evaluated_against_rule_set_date, reviewed_by_officer (FK users, nullable), created_at.
    """
    VERDICT_CHOICES = [
        ("compliant", "Compliant"),
        ("non_compliant", "Non-Compliant"),
        ("needs_review", "Needs Review"),
    ]

    scan = models.OneToOneField(
        "scans.Scan",
        on_delete=models.CASCADE,
        related_name="compliance_check",
    )
    verdict = models.CharField(max_length=30, choices=VERDICT_CHOICES)
    overall_confidence = models.FloatField(default=0.0)
    evaluated_against_rule_set_date = models.DateField()
    reviewed_by_officer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_compliance_checks",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "compliance_checks"
        ordering = ["-created_at"]

    def __str__(self):
        return f"ComplianceCheck #{self.id} for Scan #{self.scan_id}: {self.verdict} ({self.overall_confidence * 100:.0f}%)"


class Violation(models.Model):
    """
    Violations table.
    Fields: id, compliance_check_id (FK), rule_id (FK), description,
    evidence_image_id (FK scan_images, nullable), created_at.
    """
    compliance_check = models.ForeignKey(
        ComplianceCheck,
        on_delete=models.CASCADE,
        related_name="violations",
    )
    rule = models.ForeignKey(
        "rules_engine.Rule",
        on_delete=models.CASCADE,
        related_name="violations",
    )
    description = models.TextField()
    evidence_image = models.ForeignKey(
        "scans.ScanImage",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="violations",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "violations"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Violation #{self.id} against {self.rule.rule_id_code}"


class ProductComplianceHistory(models.Model):
    """
    Product Compliance History table.
    Fields: id, product_id (FK), violation_id (FK, nullable),
    is_first_time (bool, computed at write time), case_id (FK cases, nullable), created_at.
    """
    product = models.ForeignKey(
        "product_master.Product",
        on_delete=models.CASCADE,
        related_name="compliance_history",
    )
    violation = models.ForeignKey(
        Violation,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="history_entries",
    )
    is_first_time = models.BooleanField(default=True)
    case = models.ForeignKey(
        "cases.Case",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="compliance_history_entries",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "product_compliance_history"
        ordering = ["-created_at"]

    def __str__(self):
        history_type = "First-time" if self.is_first_time else "Repeat"
        return f"{history_type} history entry for {self.product.product_name} (#{self.id})"
