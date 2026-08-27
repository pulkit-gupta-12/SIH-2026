"""
Scans models: Scan, ScanImage, ExtractedField.
Matches schema from 05_Database_Schema.md.
"""
from django.conf import settings
from django.db import models


class Scan(models.Model):
    """
    Scans table.
    Fields: id, product_id (FK, nullable until resolved), performed_by (FK users),
    role_context (citizen/officer), location (nullable), capture_method,
    status (pending/processed/reviewed), created_at.
    """
    ROLE_CONTEXT_CHOICES = [
        ("citizen", "Citizen"),
        ("officer", "Field Officer"),
        ("field_officer", "Field Officer"),
    ]
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("processed", "Processed"),
        ("reviewed", "Reviewed"),
    ]
    CAPTURE_METHOD_CHOICES = [
        ("barcode", "Barcode Scan"),
        ("single_image", "Single Image"),
        ("guided_capture", "Guided Multi-Angle Capture"),
        ("manual_search", "Manual Search"),
    ]

    product = models.ForeignKey(
        "product_master.Product",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="scans",
    )
    performed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="scans",
    )
    role_context = models.CharField(max_length=30, choices=ROLE_CONTEXT_CHOICES)
    location = models.CharField(max_length=255, blank=True, null=True)
    capture_method = models.CharField(
        max_length=50,
        choices=CAPTURE_METHOD_CHOICES,
        default="guided_capture",
    )
    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default="pending",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "scans"
        ordering = ["-created_at"]

    def __str__(self):
        prod_str = f" for {self.product}" if self.product else " (unresolved product)"
        return f"Scan #{self.id} by {self.performed_by.username}{prod_str} [{self.status}]"


class ScanImage(models.Model):
    """
    Scan Images table.
    Fields: id, scan_id (FK), image_url, angle_type (front_panel/declaration_panel/close_up/barcode/wrap_around),
    quality_check_passed (bool), created_at.
    """
    ANGLE_TYPE_CHOICES = [
        ("front_panel", "Front Panel"),
        ("declaration_panel", "Declaration Panel"),
        ("close_up", "Close-Up"),
        ("barcode", "Barcode"),
        ("wrap_around", "Wrap Around"),
    ]

    scan = models.ForeignKey(
        Scan,
        on_delete=models.CASCADE,
        related_name="images",
    )
    image_url = models.CharField(max_length=500)
    angle_type = models.CharField(max_length=50, choices=ANGLE_TYPE_CHOICES)
    quality_check_passed = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "scan_images"
        ordering = ["created_at"]

    def __str__(self):
        return f"ScanImage #{self.id} (Scan #{self.scan_id}, {self.angle_type})"


class ExtractedField(models.Model):
    """
    Extracted Fields table.
    Fields: id, scan_id (FK), field_type (mrp/net_quantity/mfg_date/address/consumer_care/country_of_origin/license_no/...),
    extracted_value, confidence_score, font_size_mm (nullable), placement_zone (nullable).
    """
    scan = models.ForeignKey(
        Scan,
        on_delete=models.CASCADE,
        related_name="extracted_fields",
    )
    field_type = models.CharField(max_length=50, db_index=True)
    extracted_value = models.TextField()
    confidence_score = models.FloatField(default=0.0)
    font_size_mm = models.FloatField(blank=True, null=True)
    placement_zone = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        db_table = "extracted_fields"

    def __str__(self):
        return f"ExtractedField ({self.field_type}={self.extracted_value[:30]}) [Scan #{self.scan_id}]"
