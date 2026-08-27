"""
Inspections models: InspectionTarget.
Matches schema from 05_Database_Schema.md.
"""
from django.conf import settings
from django.db import models


class InspectionTarget(models.Model):
    """
    Inspection Targets table.
    Fields: id, product_id (FK), assigned_to (FK users), source (risk_engine/complaint/ecommerce_flag),
    priority_score, complaint_id (FK, nullable), status (pending/in_progress/done), created_at.
    """
    SOURCE_CHOICES = [
        ("risk_engine", "Risk Engine Prioritization"),
        ("complaint", "Citizen Complaint"),
        ("ecommerce_flag", "E-commerce Flagged Listing"),
    ]
    STATUS_CHOICES = [
        ("pending", "Pending Inspection"),
        ("in_progress", "In Progress"),
        ("done", "Inspection Done"),
    ]

    product = models.ForeignKey(
        "product_master.Product",
        on_delete=models.CASCADE,
        related_name="inspection_targets",
    )
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="assigned_inspections",
    )
    source = models.CharField(max_length=50, choices=SOURCE_CHOICES)
    priority_score = models.FloatField(default=0.0)
    complaint = models.ForeignKey(
        "complaints.Complaint",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="inspection_targets",
    )
    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default="pending",
        db_index=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "inspection_targets"
        ordering = ["-priority_score", "-created_at"]

    def __str__(self):
        return f"InspectionTarget #{self.id}: {self.product.brand_name} -> {self.assigned_to.username} (Priority: {self.priority_score:.1f}, {self.status})"
