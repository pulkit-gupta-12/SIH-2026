"""
Admin registration for rules_engine (Phase 4.3).
"""
from django.contrib import admin
from .models import (
    RuleSource,
    Rule,
    RuleNotification,
    RuleDraft,
    RuleSimulationResult,
    InspectionWeightConfig,
)


@admin.register(RuleSource)
class RuleSourceAdmin(admin.ModelAdmin):
    list_display = ("id", "notification_no", "title", "published_date", "gazette_url")
    search_fields = ("notification_no", "title")
    list_filter = ("published_date",)


@admin.register(Rule)
class RuleAdmin(admin.ModelAdmin):
    list_display = ("id", "rule_id_code", "section_ref", "category", "status", "effective_from", "effective_to", "superseded_by")
    list_filter = ("category", "status", "effective_from")
    search_fields = ("rule_id_code", "section_ref")


@admin.register(RuleNotification)
class RuleNotificationAdmin(admin.ModelAdmin):
    list_display = ("id", "notification_no", "title", "category", "status", "published_date", "date_detected")
    list_filter = ("status", "category", "published_date")
    search_fields = ("notification_no", "title", "source_text")


class RuleSimulationResultInline(admin.TabularInline):
    model = RuleSimulationResult
    extra = 0
    readonly_fields = ("total_scans_evaluated", "before_compliance_rate", "after_compliance_rate", "projected_violation_diff", "created_at")


@admin.register(RuleDraft)
class RuleDraftAdmin(admin.ModelAdmin):
    list_display = ("id", "rule_id_code", "section_ref", "category", "status", "effective_date", "reviewing_admin", "updated_at")
    list_filter = ("status", "category", "effective_date")
    search_fields = ("rule_id_code", "section_ref", "new_clause_text")
    inlines = [RuleSimulationResultInline]


@admin.register(RuleSimulationResult)
class RuleSimulationResultAdmin(admin.ModelAdmin):
    list_display = ("id", "draft", "total_scans_evaluated", "before_compliance_rate", "after_compliance_rate", "projected_violation_diff", "created_at")
    list_filter = ("created_at",)


@admin.register(InspectionWeightConfig)
class InspectionWeightConfigAdmin(admin.ModelAdmin):
    list_display = ("id", "risk_engine_weight", "complaint_weight", "ecommerce_weight", "repeat_offense_multiplier", "updated_at", "updated_by")
