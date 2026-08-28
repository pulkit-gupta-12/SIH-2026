"""
Serializers for Cases app: Case, ImprovementNotice, PenaltyCase.
"""
from rest_framework import serializers
from .models import Case, ImprovementNotice, PenaltyCase
from apps.product_master.models import Product
from apps.compliance.models import Violation


class ImprovementNoticeSerializer(serializers.ModelSerializer):
    issued_by_username = serializers.CharField(source="issued_by.username", read_only=True)

    class Meta:
        model = ImprovementNotice
        fields = [
            "id",
            "case",
            "issued_by",
            "issued_by_username",
            "rectification_deadline",
            "business_response",
            "outcome",
        ]
        read_only_fields = ["id", "case", "issued_by"]


class PenaltyCaseSerializer(serializers.ModelSerializer):
    escalated_by_username = serializers.CharField(source="escalated_by.username", read_only=True)

    class Meta:
        model = PenaltyCase
        fields = [
            "id",
            "case",
            "escalated_by",
            "escalated_by_username",
            "approved_by_controller",
            "payment_status",
            "appeal_status",
        ]
        read_only_fields = ["id", "case", "escalated_by"]


class CaseDetailSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.product_name", read_only=True)
    brand_name = serializers.CharField(source="product.brand_name", read_only=True)
    gtin_barcode = serializers.CharField(source="product.gtin_barcode", read_only=True)
    opened_by_username = serializers.CharField(source="opened_by.username", read_only=True)
    rule_id_code = serializers.CharField(source="violation.rule.rule_id_code", read_only=True)
    violation_description = serializers.CharField(source="violation.description", read_only=True)
    improvement_notice = ImprovementNoticeSerializer(read_only=True)
    penalty_case = PenaltyCaseSerializer(read_only=True)

    class Meta:
        model = Case
        fields = [
            "id",
            "product",
            "product_name",
            "brand_name",
            "gtin_barcode",
            "violation",
            "rule_id_code",
            "violation_description",
            "complaint",
            "classification",
            "status",
            "opened_by",
            "opened_by_username",
            "improvement_notice",
            "penalty_case",
            "created_at",
            "closed_at",
        ]
        read_only_fields = fields


class CaseCreateSerializer(serializers.Serializer):
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all())
    violation = serializers.PrimaryKeyRelatedField(queryset=Violation.objects.all(), required=False, allow_null=True)
    complaint = serializers.IntegerField(required=False, allow_null=True)
    rectification_days = serializers.IntegerField(default=30, required=False)
    notes = serializers.CharField(required=False, allow_blank=True)
