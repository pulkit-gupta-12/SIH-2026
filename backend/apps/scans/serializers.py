"""
Serializers for Scans app.
"""
from rest_framework import serializers
from .models import Scan, ScanImage, ExtractedField
from apps.compliance.models import ComplianceCheck, Violation


class ScanImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScanImage
        fields = ["id", "image_url", "angle_type", "quality_check_passed", "created_at"]


class ExtractedFieldSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExtractedField
        fields = [
            "id", "field_type", "extracted_value", "confidence_score",
            "font_size_mm", "placement_zone",
        ]


class ViolationSerializer(serializers.ModelSerializer):
    rule_id_code = serializers.CharField(source="rule.rule_id_code", read_only=True)
    section_ref = serializers.CharField(source="rule.section_ref", read_only=True)

    class Meta:
        model = Violation
        fields = [
            "id", "rule", "rule_id_code", "section_ref",
            "description", "created_at",
        ]


class ComplianceCheckSerializer(serializers.ModelSerializer):
    violations = ViolationSerializer(many=True, read_only=True)

    class Meta:
        model = ComplianceCheck
        fields = [
            "id", "verdict", "overall_confidence",
            "evaluated_against_rule_set_date", "violations", "created_at",
        ]


class ScanDetailSerializer(serializers.ModelSerializer):
    scan_images = ScanImageSerializer(many=True, read_only=True)
    extracted_fields = ExtractedFieldSerializer(many=True, read_only=True)
    compliance_check = ComplianceCheckSerializer(source="compliancecheck", read_only=True)

    class Meta:
        model = Scan
        fields = [
            "id", "product", "performed_by", "role_context",
            "location", "capture_method", "status",
            "scan_images", "extracted_fields", "compliance_check", "created_at",
        ]


class ScanCreateSerializer(serializers.ModelSerializer):
    image_urls = serializers.ListField(child=serializers.CharField(), required=False, write_only=True)
    category = serializers.CharField(required=False, write_only=True, default="general")

    class Meta:
        model = Scan
        fields = [
            "id", "product", "role_context", "location",
            "capture_method", "image_urls", "category",
        ]
