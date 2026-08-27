"""
Admin registration for compliance.
"""
from django.contrib import admin
from .models import ComplianceCheck, Violation, ProductComplianceHistory


class ViolationInline(admin.TabularInline):
    model = Violation
    extra = 0


@admin.register(ComplianceCheck)
class ComplianceCheckAdmin(admin.ModelAdmin):
    list_display = ("id", "scan", "verdict", "overall_confidence", "evaluated_against_rule_set_date", "reviewed_by_officer", "created_at")
    list_filter = ("verdict", "evaluated_against_rule_set_date", "created_at")
    search_fields = ("scan__performed_by__username", "scan__product__product_name")
    inlines = [ViolationInline]


@admin.register(Violation)
class ViolationAdmin(admin.ModelAdmin):
    list_display = ("id", "compliance_check", "rule", "description", "created_at")
    list_filter = ("rule__category", "created_at")
    search_fields = ("description", "rule__rule_id_code")


@admin.register(ProductComplianceHistory)
class ProductComplianceHistoryAdmin(admin.ModelAdmin):
    list_display = ("id", "product", "violation", "is_first_time", "case", "created_at")
    list_filter = ("is_first_time", "created_at")
    search_fields = ("product__product_name", "product__brand_name")
