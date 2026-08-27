"""
Admin registration for complaints.
"""
from django.contrib import admin
from .models import Complaint


@admin.register(Complaint)
class ComplaintAdmin(admin.ModelAdmin):
    list_display = ("id", "filed_by", "product", "location", "risk_score", "routed_to_state", "status", "created_at")
    list_filter = ("status", "routed_to_state", "created_at")
    search_fields = ("filed_by__username", "product__product_name", "description", "location")
