"""
Serializers for Inspections app.
"""
from rest_framework import serializers
from .models import InspectionTarget
from apps.product_master.models import Product
from apps.complaints.models import Complaint


class InspectionProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ["id", "gtin_barcode", "brand_name", "product_name", "category", "manufacturer_name", "manufacturer_address"]


class InspectionComplaintSerializer(serializers.ModelSerializer):
    class Meta:
        model = Complaint
        fields = ["id", "description", "photo_urls", "location", "risk_score", "routed_to_state", "status", "created_at"]


class InspectionTargetSerializer(serializers.ModelSerializer):
    product_detail = InspectionProductSerializer(source="product", read_only=True)
    complaint_detail = InspectionComplaintSerializer(source="complaint", read_only=True)
    assigned_to_username = serializers.CharField(source="assigned_to.username", read_only=True)
    scan_id = serializers.IntegerField(source="scan.id", read_only=True)
    compliance_check_id = serializers.IntegerField(source="scan.compliance_check.id", read_only=True)
    verification = serializers.SerializerMethodField()

    class Meta:
        model = InspectionTarget
        fields = [
            "id",
            "product",
            "product_detail",
            "assigned_to",
            "assigned_to_username",
            "source",
            "priority_score",
            "complaint",
            "complaint_detail",
            "status",
            "created_at",
            "scan_id",
            "compliance_check_id",
            "verification",
        ]

    def get_verification(self, obj):
        if not obj.scan_id or not hasattr(obj.scan, "compliance_check"):
            return None
        check = obj.scan.compliance_check
        report = check.report_data or {}
        summary = report.get("summary", {})
        return {
            "verdict": check.verdict,
            "overall_confidence": check.overall_confidence,
            "capture_method": obj.scan.capture_method,
            "location": obj.scan.location,
            "evaluated_against_rule_set_date": check.evaluated_against_rule_set_date.isoformat(),
            "summary": summary,
            "violations": report.get("violations", []),
            "warnings": report.get("warnings", []),
            "reviews": report.get("reviews", []),
            "passed_rules": report.get("passed_rules", []),
            "evidence": report.get("evidence", []),
        }
