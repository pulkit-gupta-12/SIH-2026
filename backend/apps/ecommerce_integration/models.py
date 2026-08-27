"""
E-commerce Integration models: EcommerceListing.
Matches schema from 05_Database_Schema.md.
"""
from django.db import models


class EcommerceListing(models.Model):
    """
    E-commerce Listings table.
    Fields: id, platform_name, product_id (FK, nullable),
    raw_listing_data (JSONB), screening_result (compliant/flagged/pending),
    flagged_reason (nullable), created_at.
    """
    SCREENING_RESULT_CHOICES = [
        ("compliant", "Compliant"),
        ("flagged", "Flagged for Review"),
        ("pending", "Pending Screening"),
    ]

    platform_name = models.CharField(max_length=100, db_index=True)
    product = models.ForeignKey(
        "product_master.Product",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="ecommerce_listings",
    )
    raw_listing_data = models.JSONField(default=dict)
    screening_result = models.CharField(
        max_length=30,
        choices=SCREENING_RESULT_CHOICES,
        default="pending",
        db_index=True,
    )
    flagged_reason = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "ecommerce_listings"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.platform_name} Listing #{self.id} [{self.screening_result}]"
