"""
Serializers for Scans app.
"""
from rest_framework import serializers
from .models import Scan, ScanImage, ExtractedField
from apps.compliance.models import ComplianceCheck, Violation
from apps.product_master.models import Product


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
    scan_images = ScanImageSerializer(source="images", many=True, read_only=True)
    extracted_fields = ExtractedFieldSerializer(many=True, read_only=True)
    compliance_check = ComplianceCheckSerializer(read_only=True)


    class Meta:
        model = Scan
        fields = [
            "id", "product", "performed_by", "role_context",
            "location", "capture_method", "status",
            "scan_images", "extracted_fields", "compliance_check", "created_at",
        ]


class ScanCreateSerializer(serializers.ModelSerializer):
    barcode = serializers.CharField(required=False, write_only=True, allow_blank=True)
    image_urls = serializers.ListField(child=serializers.CharField(), required=False, write_only=True, default=list)
    images = serializers.ListField(child=serializers.FileField(), required=False, write_only=True, default=list)
    category = serializers.CharField(required=False, write_only=True, default="general")

    class Meta:
        model = Scan
        fields = [
            "id", "product", "role_context", "location",
            "capture_method", "barcode", "image_urls", "images", "category",
        ]
        extra_kwargs = {
            "role_context": {"required": False, "default": "citizen"},
            "capture_method": {"required": False, "default": "single_image"},
        }

    def validate(self, attrs):
        request = self.context.get("request")
        is_citizen = False
        if request and request.user and request.user.is_authenticated:
            is_citizen = request.user.role_assignments.filter(role__name="citizen").exists()

        image_urls = attrs.get("image_urls") or []
        uploaded_files = list(attrs.get("images") or [])
        if request and request.FILES:
            uploaded_files.extend(request.FILES.getlist("images"))
            if "image" in request.FILES and request.FILES["image"] not in uploaded_files:
                uploaded_files.append(request.FILES["image"])

        has_images = bool(image_urls or uploaded_files)

        if is_citizen:
            barcode = attrs.get("barcode")
            product = attrs.get("product")
            if not barcode and not has_images and not product:
                raise serializers.ValidationError(
                    "Provide a barcode to look up, or an image to scan a new product."
                )
            if (len(image_urls) + len(uploaded_files)) > 1:
                raise serializers.ValidationError(
                    "Citizen scans support a single image only."
                )
        return attrs

