"""
Admin registration for product_master.
"""
from django.contrib import admin
from .models import Product


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("id", "brand_name", "product_name", "category", "gtin_barcode", "manufacturer_name", "created_at")
    list_filter = ("category", "created_at")
    search_fields = ("brand_name", "product_name", "gtin_barcode", "manufacturer_name")
    ordering = ("-created_at",)
