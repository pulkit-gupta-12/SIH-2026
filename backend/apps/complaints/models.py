"""
Complaints models: Complaint.
Matches schema from 05_Database_Schema.md.
"""
from django.conf import settings
from django.db import models


class Complaint(models.Model):
    """
    Complaints table.
    Fields: id, filed_by (FK users), product_id (FK), description,
    photo_urls (array), location, risk_score, routed_to_state (nullable), status, created_at.
    """
    STATUS_CHOICES = [
        ("open", "Open"),
        ("under_investigation", "Under Investigation"),
        ("resolved", "Resolved"),
        ("dismissed", "Dismissed"),
    ]

    filed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="complaints",
    )
    product = models.ForeignKey(
        "product_master.Product",
        on_delete=models.CASCADE,
        related_name="complaints",
    )
    description = models.TextField()
    photo_urls = models.JSONField(default=list)
    location = models.CharField(max_length=255, blank=True, null=True)
    risk_score = models.FloatField(default=0.0)
    routed_to_state = models.CharField(max_length=100, blank=True, null=True)
    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default="open",
        db_index=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "complaints"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Complaint #{self.id} on {self.product.product_name} by {self.filed_by.username} [{self.status}]"
