"""
Views for Inspections app: InspectionTargetViewSet with /queue/ action.
"""
from django.db.models import Q
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import InspectionTarget
from .serializers import InspectionTargetSerializer
from apps.complaints.models import Complaint
from apps.common.permissions import IsFieldOfficer, IsStateController, IsNationalAdmin


class InspectionTargetViewSet(viewsets.ModelViewSet):
    """
    API endpoint for Inspection Targets and Officer Queue.
    GET /api/inspections/queue/ -> Priority-sorted inspection queue for officer.
    """
    queryset = (
        InspectionTarget.objects.all()
        .select_related("product", "assigned_to", "complaint")
        .order_by("-priority_score", "-created_at")
    )
    serializer_class = InspectionTargetSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return InspectionTarget.objects.none()

        # If user is a field officer, show targets assigned to them or unassigned
        is_officer = user.role_assignments.filter(role__name="field_officer").exists()
        if is_officer:
            assignment = user.role_assignments.filter(role__name="field_officer").first()
            state = assignment.state if assignment else None
            qs = InspectionTarget.objects.filter(
                Q(assigned_to=user) | Q(assigned_to__isnull=True)
            )
            return qs.select_related("product", "assigned_to", "complaint")

        return super().get_queryset()

    @action(detail=False, methods=["get"], url_path="queue")
    def queue(self, request):
        """
        GET /api/inspections/queue/
        Returns priority-ranked list of inspection targets for the officer,
        including open citizen complaints.
        """
        user = request.user
        is_officer = user.role_assignments.filter(
            role__name__in=["field_officer", "state_controller", "national_admin"]
        ).exists()

        if not is_officer:
            return Response(
                {"detail": "Field Officer or Controller role required."},
                status=status.HTTP_403_FORBIDDEN,
            )

        # 1. Existing InspectionTarget rows
        target_qs = (
            InspectionTarget.objects.filter(
                Q(assigned_to=user) | Q(assigned_to__isnull=True)
            )
            .select_related("product", "assigned_to", "complaint")
            .order_by("-priority_score", "-created_at")
        )
        target_serializer = InspectionTargetSerializer(target_qs, many=True)
        items = list(target_serializer.data)

        # 2. Add open citizen complaints that don't have an explicit InspectionTarget yet
        existing_complaint_ids = set(
            InspectionTarget.objects.exclude(complaint__isnull=True).values_list(
                "complaint_id", flat=True
            )
        )
        open_complaints = (
            Complaint.objects.filter(status="open")
            .exclude(id__in=existing_complaint_ids)
            .select_related("product", "filed_by")
            .order_by("-risk_score", "-created_at")
        )

        for c in open_complaints:
            items.append({
                "id": f"cmp-{c.id}",
                "product": c.product_id,
                "product_detail": {
                    "id": c.product.id,
                    "gtin_barcode": c.product.gtin_barcode,
                    "brand_name": c.product.brand_name,
                    "product_name": c.product.product_name,
                    "category": c.product.category,
                    "manufacturer_name": c.product.manufacturer_name,
                    "manufacturer_address": c.product.manufacturer_address,
                },
                "assigned_to": user.id,
                "assigned_to_username": user.username,
                "source": "complaint",
                "priority_score": c.risk_score,
                "complaint": c.id,
                "complaint_detail": {
                    "id": c.id,
                    "description": c.description,
                    "photo_urls": c.photo_urls,
                    "location": c.location,
                    "risk_score": c.risk_score,
                    "routed_to_state": c.routed_to_state,
                    "status": c.status,
                    "created_at": c.created_at.isoformat(),
                },
                "status": "pending",
                "created_at": c.created_at.isoformat(),
            })

        # Sort combined queue by priority score descending
        items.sort(key=lambda x: x.get("priority_score", 0.0), reverse=True)

        return Response(items, status=status.HTTP_200_OK)
