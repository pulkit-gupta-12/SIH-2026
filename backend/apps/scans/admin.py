"""
Admin registration for scans.
"""
from django.contrib import admin
from .models import Scan, ScanImage, ExtractedField


class ScanImageInline(admin.TabularInline):
    model = ScanImage
    extra = 0


class ExtractedFieldInline(admin.TabularInline):
    model = ExtractedField
    extra = 0


@admin.register(Scan)
class ScanAdmin(admin.ModelAdmin):
    list_display = ("id", "performed_by", "product", "role_context", "capture_method", "status", "created_at")
    list_filter = ("role_context", "capture_method", "status", "created_at")
    search_fields = ("performed_by__username", "product__product_name", "product__brand_name", "location")
    inlines = [ScanImageInline, ExtractedFieldInline]


@admin.register(ScanImage)
class ScanImageAdmin(admin.ModelAdmin):
    list_display = ("id", "scan", "angle_type", "quality_check_passed", "created_at")
    list_filter = ("angle_type", "quality_check_passed")


@admin.register(ExtractedField)
class ExtractedFieldAdmin(admin.ModelAdmin):
    list_display = ("id", "scan", "field_type", "extracted_value", "confidence_score", "font_size_mm", "placement_zone")
    list_filter = ("field_type", "placement_zone")
    search_fields = ("field_type", "extracted_value")
