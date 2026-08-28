"""
Serializers for Complaints app.
"""
from rest_framework import serializers
from .models import Complaint
from apps.product_master.models import Product


class ComplaintSerializer(serializers.ModelSerializer):
    """
    Serializer for Complaints.
    Used for POST /api/complaints/ and GET /api/complaints/mine/.
    """
    product_name = serializers.CharField(source="product.product_name", read_only=True)
    brand_name = serializers.CharField(source="product.brand_name", read_only=True)
    gtin_barcode = serializers.CharField(source="product.gtin_barcode", read_only=True)
    filed_by_username = serializers.CharField(source="filed_by.username", read_only=True)
    photo_urls = serializers.ListField(child=serializers.CharField(), required=False, default=list)

    class Meta:
        model = Complaint
        fields = [
            "id",
            "product",
            "product_name",
            "brand_name",
            "gtin_barcode",
            "description",
            "photo_urls",
            "location",
            "risk_score",
            "routed_to_state",
            "status",
            "filed_by",
            "filed_by_username",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "risk_score",
            "routed_to_state",
            "status",
            "filed_by",
            "filed_by_username",
            "created_at",
        ]
