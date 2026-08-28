"""
Serializers for Product Master app.
"""
from rest_framework import serializers
from .models import Product


class ProductSerializer(serializers.ModelSerializer):
    """Read-only detail view for Product/Brand Info screen."""

    class Meta:
        model = Product
        fields = [
            "id",
            "gtin_barcode",
            "brand_name",
            "product_name",
            "category",
            "manufacturer_name",
            "manufacturer_address",
            "registered_by_business",
            "created_at",
        ]
        read_only_fields = fields


class ViolationSnapshotSerializer(serializers.Serializer):
    """Violation item in a compliance snapshot."""
    rule_id = serializers.IntegerField()
    rule_code = serializers.CharField(allow_null=True)
    rule_name = serializers.CharField(allow_null=True, required=False)
    section_ref = serializers.CharField(allow_null=True, required=False)
    description = serializers.CharField(allow_null=True, required=False)
    field = serializers.CharField(allow_null=True, required=False)
    is_first_time = serializers.BooleanField(allow_null=True, required=False)


class ComplianceSnapshotSerializer(serializers.Serializer):
    """
    Shape returned by GET /api/products/{id}/compliance-snapshot/
    and POST /api/scans/ (for citizen scans).
    """
    product_id = serializers.IntegerField()
    product_name = serializers.CharField()
    brand_name = serializers.CharField(allow_null=True)
    gtin_barcode = serializers.CharField(allow_null=True)
    category = serializers.CharField(allow_null=True, required=False)
    has_been_scanned = serializers.BooleanField()
    verdict = serializers.CharField()
    last_checked_at = serializers.DateTimeField(allow_null=True)
    violation_count = serializers.IntegerField()
    violations = ViolationSnapshotSerializer(many=True, required=False)
