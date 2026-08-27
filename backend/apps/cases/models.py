"""
Cases models: Case, ImprovementNotice, PenaltyCase.
Matches schema from 05_Database_Schema.md.
"""
from django.conf import settings
from django.db import models


class Case(models.Model):
    """
    Cases table.
    Fields: id, violation_id (FK, nullable), complaint_id (FK, nullable),
    product_id (FK), classification (first_time/repeat/fraud),
    status (open/notice_sent/rectification_window/verified/escalated/closed/appealed),
    opened_by (FK users), created_at, closed_at (nullable).
    """
    CLASSIFICATION_CHOICES = [
        ("first_time", "First-Time Procedural"),
        ("repeat", "Repeat Violation"),
        ("fraud", "Fraud / Serious Violation"),
    ]
    STATUS_CHOICES = [
        ("open", "Open"),
        ("notice_sent", "Notice Sent"),
        ("rectification_window", "Rectification Window Active"),
        ("verified", "Rectification Verified"),
        ("escalated", "Escalated to Penalty"),
        ("closed", "Closed"),
        ("appealed", "Appealed"),
    ]

    violation = models.ForeignKey(
        "compliance.Violation",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="cases",
    )
    complaint = models.ForeignKey(
        "complaints.Complaint",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="cases",
    )
    product = models.ForeignKey(
        "product_master.Product",
        on_delete=models.CASCADE,
        related_name="cases",
    )
    classification = models.CharField(
        max_length=30,
        choices=CLASSIFICATION_CHOICES,
        default="first_time",
    )
    status = models.CharField(
        max_length=50,
        choices=STATUS_CHOICES,
        default="open",
        db_index=True,
    )
    opened_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="opened_cases",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    closed_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = "cases"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Case #{self.id}: {self.product.brand_name} [{self.classification}] — {self.status}"


class ImprovementNotice(models.Model):
    """
    Improvement Notices table.
    Fields: id, case_id (FK/OneToOne), issued_by (FK users), rectification_deadline,
    business_response (nullable), verified_by (FK users, nullable), outcome (pending/rectified/escalated).
    """
    OUTCOME_CHOICES = [
        ("pending", "Pending Response"),
        ("rectified", "Rectified / Compliant"),
        ("escalated", "Escalated to Penalty"),
    ]

    case = models.OneToOneField(
        Case,
        on_delete=models.CASCADE,
        related_name="improvement_notice",
    )
    issued_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="issued_notices",
    )
    rectification_deadline = models.DateField()
    business_response = models.TextField(blank=True, null=True)
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="verified_notices",
    )
    outcome = models.CharField(
        max_length=30,
        choices=OUTCOME_CHOICES,
        default="pending",
    )

    class Meta:
        db_table = "improvement_notices"

    def __str__(self):
        return f"ImprovementNotice for Case #{self.case_id} (Deadline: {self.rectification_deadline})"


class PenaltyCase(models.Model):
    """
    Penalty Cases table.
    Fields: id, case_id (FK/OneToOne), escalated_by (FK users),
    approved_by_controller (FK users, nullable), payment_status, appeal_status (none/filed/resolved).
    """
    PAYMENT_STATUS_CHOICES = [
        ("pending", "Pending Payment"),
        ("paid", "Paid"),
        ("waived", "Waived"),
        ("overdue", "Overdue"),
    ]
    APPEAL_STATUS_CHOICES = [
        ("none", "No Appeal"),
        ("filed", "Appeal Filed"),
        ("resolved", "Appeal Resolved"),
    ]

    case = models.OneToOneField(
        Case,
        on_delete=models.CASCADE,
        related_name="penalty_case",
    )
    escalated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="escalated_penalties",
    )
    approved_by_controller = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_penalties",
    )
    payment_status = models.CharField(
        max_length=30,
        choices=PAYMENT_STATUS_CHOICES,
        default="pending",
    )
    appeal_status = models.CharField(
        max_length=30,
        choices=APPEAL_STATUS_CHOICES,
        default="none",
    )

    class Meta:
        db_table = "penalty_cases"

    def __str__(self):
        return f"PenaltyCase for Case #{self.case_id} (Payment: {self.payment_status}, Appeal: {self.appeal_status})"
