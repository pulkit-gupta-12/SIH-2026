"""
Serializers for Rule Engine Admin Console (Phase 4.3).
"""
from rest_framework import serializers
from .models import (
    RuleSource,
    Rule,
    RuleNotification,
    RuleDraft,
    RuleSimulationResult,
    InspectionWeightConfig,
)


class RuleSourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = RuleSource
        fields = ["id", "notification_no", "title", "gazette_url", "published_date"]


class RuleSerializer(serializers.ModelSerializer):
    """Live rules repository serializer."""
    source_title = serializers.CharField(source="source.title", read_only=True)
    source_notification_no = serializers.CharField(source="source.notification_no", read_only=True)
    superseded_by_code = serializers.CharField(source="superseded_by.rule_id_code", read_only=True, default=None)

    class Meta:
        model = Rule
        fields = [
            "id",
            "rule_id_code",
            "section_ref",
            "category",
            "condition",
            "effective_from",
            "effective_to",
            "superseded_by",
            "superseded_by_code",
            "status",
            "source",
            "source_title",
            "source_notification_no",
        ]


class RuleNotificationSerializer(serializers.ModelSerializer):
    draft_count = serializers.IntegerField(source="drafts.count", read_only=True)

    class Meta:
        model = RuleNotification
        fields = [
            "id",
            "notification_no",
            "title",
            "source_text",
            "gazette_url",
            "published_date",
            "date_detected",
            "category",
            "status",
            "draft_count",
        ]


class RuleSimulationResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = RuleSimulationResult
        fields = [
            "id",
            "draft",
            "total_scans_evaluated",
            "before_compliance_rate",
            "after_compliance_rate",
            "projected_violation_diff",
            "metrics",
            "created_at",
        ]


class RuleDraftSerializer(serializers.ModelSerializer):
    notification_title = serializers.CharField(source="notification.title", read_only=True)
    notification_no = serializers.CharField(source="notification.notification_no", read_only=True)
    reviewing_admin_name = serializers.CharField(source="reviewing_admin.get_full_name", read_only=True)
    supersedes_rule_code = serializers.CharField(source="supersedes_rule.rule_id_code", read_only=True, default=None)
    simulation_results = RuleSimulationResultSerializer(many=True, read_only=True)

    class Meta:
        model = RuleDraft
        fields = [
            "id",
            "notification",
            "notification_title",
            "notification_no",
            "rule_id_code",
            "section_ref",
            "category",
            "old_clause_text",
            "new_clause_text",
            "proposed_condition",
            "effective_date",
            "status",
            "comments",
            "reviewing_admin",
            "reviewing_admin_name",
            "supersedes_rule",
            "supersedes_rule_code",
            "simulation_results",
            "created_at",
            "updated_at",
        ]


class RuleDraftCreateSerializer(serializers.Serializer):
    notification_id = serializers.IntegerField(required=False, allow_null=True)
    rule_id_code = serializers.CharField(required=False)
    section_ref = serializers.CharField(required=False)
    category = serializers.CharField(required=False, default="general")
    old_clause_text = serializers.CharField(required=False, allow_blank=True)
    new_clause_text = serializers.CharField(required=False, allow_blank=True)
    proposed_condition = serializers.DictField(required=False)
    supersedes_rule_id = serializers.IntegerField(required=False, allow_null=True)


class RuleDraftReviseSerializer(serializers.Serializer):
    rule_id_code = serializers.CharField(required=False)
    section_ref = serializers.CharField(required=False)
    category = serializers.CharField(required=False)
    old_clause_text = serializers.CharField(required=False, allow_blank=True)
    new_clause_text = serializers.CharField(required=False)
    proposed_condition = serializers.DictField(required=False)
    effective_date = serializers.DateField(required=False, allow_null=True)
    comment = serializers.CharField(required=False, allow_blank=True)


class RuleDraftApproveSerializer(serializers.Serializer):
    effective_date = serializers.DateField(required=True)
    comment = serializers.CharField(required=False, allow_blank=True)


class InspectionWeightConfigSerializer(serializers.ModelSerializer):
    updated_by_name = serializers.CharField(source="updated_by.get_full_name", read_only=True)

    class Meta:
        model = InspectionWeightConfig
        fields = [
            "id",
            "risk_engine_weight",
            "complaint_weight",
            "ecommerce_weight",
            "repeat_offense_multiplier",
            "category_multipliers",
            "updated_by",
            "updated_by_name",
            "updated_at",
        ]
