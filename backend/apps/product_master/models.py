"""
Product Master models.
Matches schema from 05_Database_Schema.md.
"""
from django.conf import settings
from django.db import models


class Product(models.Model):
    """
    Product Master table.
    Fields: id, gtin_barcode (nullable), brand_name, product_name,
    category (food/electronics/medical_device/general/import),
    manufacturer_name, manufacturer_address, registered_by_business (FK users, nullable), created_at.
    """
    CATEGORY_CHOICES = [
        ("food", "Food & Beverages"),
        ("electronics", "Electronics"),
        ("medical_device", "Medical Devices"),
        ("general", "General Commodities"),
        ("import", "Imported Goods"),
    ]

    gtin_barcode = models.CharField(max_length=50, blank=True, null=True, db_index=True)
    brand_name = models.CharField(max_length=255, db_index=True)
    product_name = models.CharField(max_length=255)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default="general")
    manufacturer_name = models.CharField(max_length=255)
    manufacturer_address = models.TextField()
    registered_by_business = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="registered_products",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "products"
        ordering = ["-created_at"]

    def __str__(self):
        barcode_str = f" [{self.gtin_barcode}]" if self.gtin_barcode else ""
        return f"{self.brand_name} — {self.product_name}{barcode_str}"
