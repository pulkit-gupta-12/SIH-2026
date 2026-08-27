"""
Admin registration for inspections.
"""
from django.contrib import admin
from .models import InspectionTarget


@admin.register(InspectionTarget)
class InspectionTargetAdmin(admin.ModelAdmin):
    list_display = ("id", "product", "assigned_to", "source", "priority_score", "complaint", "status", "created_at")
    list_filter = ("source", "status", "created_at")
    search_fields = ("product__product_name", "assigned_to__username")
