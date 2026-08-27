"""
Admin registration for cases.
"""
from django.contrib import admin
from .models import Case, ImprovementNotice, PenaltyCase


class ImprovementNoticeInline(admin.StackedInline):
    model = ImprovementNotice
    extra = 0


class PenaltyCaseInline(admin.StackedInline):
    model = PenaltyCase
    extra = 0


@admin.register(Case)
class CaseAdmin(admin.ModelAdmin):
    list_display = ("id", "product", "classification", "status", "opened_by", "created_at", "closed_at")
    list_filter = ("classification", "status", "created_at")
    search_fields = ("product__product_name", "product__brand_name", "opened_by__username")
    inlines = [ImprovementNoticeInline, PenaltyCaseInline]


@admin.register(ImprovementNotice)
class ImprovementNoticeAdmin(admin.ModelAdmin):
    list_display = ("id", "case", "issued_by", "rectification_deadline", "outcome", "verified_by")
    list_filter = ("outcome", "rectification_deadline")
    search_fields = ("case__product__product_name", "issued_by__username")


@admin.register(PenaltyCase)
class PenaltyCaseAdmin(admin.ModelAdmin):
    list_display = ("id", "case", "escalated_by", "approved_by_controller", "payment_status", "appeal_status")
    list_filter = ("payment_status", "appeal_status")
    search_fields = ("case__product__product_name", "escalated_by__username")
