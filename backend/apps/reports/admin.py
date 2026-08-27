"""
Admin registration for reports.
"""
from django.contrib import admin
from .models import Report


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ("id", "case", "format", "signed", "file_url", "generated_at")
    list_filter = ("format", "signed", "generated_at")
    search_fields = ("case__product__product_name", "file_url")
