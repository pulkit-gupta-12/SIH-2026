"""
Admin registration for rules_engine.
"""
from django.contrib import admin
from .models import RuleSource, Rule


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
