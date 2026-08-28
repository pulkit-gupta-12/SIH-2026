"""
Views for Product Master app.
"""
from django.db.models import Q
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Product
from .serializers import ProductSerializer, ComplianceSnapshotSerializer
from apps.compliance.models import ComplianceCheck, Violation, ProductComplianceHistory


def build_compliance_snapshot_payload(product, latest_check=None):
    """
    Helper function to build a structured compliance snapshot payload for a product.
    If latest_check is not passed, looks up the latest ComplianceCheck for the product.
    """
    if latest_check is None and product is not None:
        latest_check = (
            ComplianceCheck.objects.filter(scan__product=product)
            .order_by("-created_at")
            .first()
        )

    if latest_check is None:
        return {
            "product_id": product.id if product else 0,
            "product_name": product.product_name if product else "Unknown Product",
            "brand_name": getattr(product, "brand_name", None),
            "gtin_barcode": getattr(product, "gtin_barcode", None),
            "category": getattr(product, "category", "general"),
            "has_been_scanned": False,
            "verdict": "unknown",
            "last_checked_at": None,
            "violation_count": 0,
            "violations": [],
        }

    violations = Violation.objects.filter(compliance_check=latest_check).select_related("rule")
    violation_list = []
    for v in violations:
        history_entry = (
            ProductComplianceHistory.objects.filter(product=product, violation=v).first()
            if product
            else None
        )
        is_first_time = history_entry.is_first_time if history_entry else True
        field_name = None
        if v.rule and isinstance(v.rule.condition, dict):
            field_name = v.rule.condition.get("field")

        violation_list.append({
            "rule_id": v.rule_id,
            "rule_code": v.rule.rule_id_code if v.rule else f"RULE-{v.rule_id}",
            "rule_name": getattr(v.rule, "rule_name", ""),
            "section_ref": getattr(v.rule, "section_ref", ""),
            "description": v.description,
            "field": field_name,
            "is_first_time": is_first_time,
        })

    return {
        "product_id": product.id,
        "product_name": product.product_name,
        "brand_name": product.brand_name,
        "gtin_barcode": product.gtin_barcode,
        "category": product.category,
        "has_been_scanned": True,
        "verdict": latest_check.verdict,
        "last_checked_at": latest_check.created_at,
        "violation_count": len(violation_list),
        "violations": violation_list,
    }


class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    """
    GET /api/products/                -> search/list (Scan/Search screen fallback)
    GET /api/products/{id}/           -> Product/Brand Info screen
    GET /api/products/{id}/compliance-snapshot/ -> Compliance Snapshot screen
    """
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        q = self.request.query_params.get("q")
        barcode = (
            self.request.query_params.get("barcode")
            or self.request.query_params.get("gtin")
            or self.request.query_params.get("gtin_barcode")
        )
        if barcode:
            qs = qs.filter(gtin_barcode=barcode)
        elif q:
            qs = qs.filter(
                Q(product_name__icontains=q)
                | Q(brand_name__icontains=q)
                | Q(gtin_barcode__icontains=q)
                | Q(manufacturer_name__icontains=q)
            )
        return qs

    @action(detail=True, methods=["get"], url_path="compliance-snapshot")
    def compliance_snapshot(self, request, pk=None):
        """
        GET /api/products/{id}/compliance-snapshot/
        Read-only; never triggers evaluation.
        """
        product = self.get_object()
        payload = build_compliance_snapshot_payload(product)
        serializer = ComplianceSnapshotSerializer(payload)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["get"], url_path="violation-history")
    def violation_history(self, request, pk=None):
        """
        GET /api/products/{id}/violation-history/
        Returns timeline of all violations recorded for this product.
        """
        product = self.get_object()
        history_qs = (
            ProductComplianceHistory.objects.filter(product=product)
            .select_related("violation", "violation__rule", "case")
            .order_by("-created_at")
        )

        timeline = []
        for h in history_qs:
            rule_code = getattr(h.violation.rule, "rule_id_code", "") if h.violation and h.violation.rule else None
            section_ref = getattr(h.violation.rule, "section_ref", "") if h.violation and h.violation.rule else ""
            timeline.append({
                "id": h.id,
                "violation_id": h.violation_id,
                "rule_id_code": rule_code,
                "section_ref": section_ref,
                "description": h.violation.description if h.violation else "",
                "is_first_time": h.is_first_time,
                "case_id": h.case_id,
                "case_status": h.case.status if h.case else None,
                "created_at": h.created_at.isoformat(),
            })


        return Response(
            {
                "product_id": product.id,
                "product_name": product.product_name,
                "brand_name": product.brand_name,
                "gtin_barcode": product.gtin_barcode,
                "total_violations": len(timeline),
                "has_repeat_offenses": any(not item["is_first_time"] for item in timeline),
                "history": timeline,
            },
            status=status.HTTP_200_OK,
        )

