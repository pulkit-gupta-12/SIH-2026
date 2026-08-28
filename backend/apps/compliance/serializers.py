"""
Serializers for Compliance app.
"""
from rest_framework import serializers
from .models import ComplianceCheck, Violation, ProductComplianceHistory
from apps.rules_engine.models import Rule


class ViolationDetailSerializer(serializers.ModelSerializer):
    rule_id_code = serializers.CharField(source="rule.rule_id_code", read_only=True)
    section_ref = serializers.CharField(source="rule.section_ref", read_only=True)
    field = serializers.SerializerMethodField()
    is_first_time = serializers.SerializerMethodField()

    class Meta:
        model = Violation
        fields = [
            "id",
            "rule",
            "rule_id_code",
            "section_ref",
            "description",
            "field",
            "is_first_time",
            "created_at",
        ]

    def get_field(self, obj):
        if obj.rule and isinstance(obj.rule.condition, dict):
            return obj.rule.condition.get("field")
        return None

    def get_is_first_time(self, obj):
        history = ProductComplianceHistory.objects.filter(violation=obj).first()
        if history:
            return history.is_first_time
        return True


class ComplianceCheckDetailSerializer(serializers.ModelSerializer):
    violations = ViolationDetailSerializer(many=True, read_only=True)
    reviewed_by_officer_username = serializers.CharField(
        source="reviewed_by_officer.username", read_only=True
    )
    product_id = serializers.IntegerField(source="scan.product.id", read_only=True)
    product_name = serializers.CharField(source="scan.product.product_name", read_only=True)
    brand_name = serializers.CharField(source="scan.product.brand_name", read_only=True)

    class Meta:
        model = ComplianceCheck
        fields = [
            "id",
            "scan",
            "product_id",
            "product_name",
            "brand_name",
            "verdict",
            "overall_confidence",
            "evaluated_against_rule_set_date",
            "reviewed_by_officer",
            "reviewed_by_officer_username",
            "violations",
            "created_at",
        ]


class ProductViolationHistorySerializer(serializers.ModelSerializer):
    rule_id_code = serializers.CharField(source="violation.rule.rule_id_code", read_only=True)
    section_ref = serializers.CharField(source="violation.rule.section_ref", read_only=True)
    description = serializers.CharField(source="violation.description", read_only=True)
    case_status = serializers.CharField(source="case.status", read_only=True)
    case_id = serializers.IntegerField(source="case.id", read_only=True)

    class Meta:
        model = ProductComplianceHistory
        fields = [
            "id",
            "product",
            "violation",
            "rule_id_code",
            "section_ref",
            "description",
            "is_first_time",
            "case",
            "case_id",
            "case_status",
            "created_at",
        ]

