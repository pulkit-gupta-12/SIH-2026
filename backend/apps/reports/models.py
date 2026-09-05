"""
Reports models: Report.
Matches schema from 05_Database_Schema.md.
"""
from django.db import models


class Report(models.Model):
    """
    Reports table.
    Fields: id, case_id (FK), file_url, format (pdf/docx), signed (bool, stub for now), generated_at.
    """
    FORMAT_CHOICES = [
        ("pdf", "PDF Document"),
        ("docx", "Word Document"),
    ]

    case = models.ForeignKey(
        "cases.Case",
        on_delete=models.CASCADE,
        related_name="reports",
        null=True,
        blank=True,
    )
    compliance_check = models.ForeignKey(
        "compliance.ComplianceCheck",
        on_delete=models.CASCADE,
        related_name="reports",
        null=True,
        blank=True,
    )
    file_url = models.CharField(max_length=500)
    format = models.CharField(
        max_length=10,
        choices=FORMAT_CHOICES,
        default="pdf",
    )
    signed = models.BooleanField(default=False)
    generated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "reports"
        ordering = ["-generated_at"]

    def __str__(self):
        sign_status = "Signed" if self.signed else "Unsigned"
        target = f"Case #{self.case_id}" if self.case_id else f"Check #{self.compliance_check_id}"
        return f"Report #{self.id} for {target} [{self.format.upper()}, {sign_status}]"
