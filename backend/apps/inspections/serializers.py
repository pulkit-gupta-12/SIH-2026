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
        ]
