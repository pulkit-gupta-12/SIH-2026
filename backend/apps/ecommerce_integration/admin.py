"""
Admin registration for ecommerce_integration.
"""
from django.contrib import admin
from .models import EcommerceListing


@admin.register(EcommerceListing)
class EcommerceListingAdmin(admin.ModelAdmin):
    list_display = ("id", "platform_name", "product", "screening_result", "flagged_reason", "created_at")
    list_filter = ("platform_name", "screening_result", "created_at")
    search_fields = ("platform_name", "product__product_name", "flagged_reason")
