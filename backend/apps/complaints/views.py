"""
Views for Complaints app.
"""
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Complaint
from .serializers import ComplaintSerializer
from .services import calculate_complaint_risk_score, determine_routed_state
from apps.common.permissions import IsCitizen


class ComplaintViewSet(viewsets.ModelViewSet):
    """
    API endpoint for complaints.
    POST /api/complaints/       -> File Complaint screen
    GET  /api/complaints/mine/  -> Complaint Status screen (citizen's own only; officer gets 403)
    """
    serializer_class = ComplaintSerializer
    permission_classes = [permissions.IsAuthenticated, IsCitizen]

    def get_queryset(self):
        # Scoped strictly to the authenticated citizen's complaints
        if not self.request.user.is_authenticated:
            return Complaint.objects.none()
        return (
            Complaint.objects.filter(filed_by=self.request.user)
            .select_related("product", "filed_by")
            .order_by("-created_at")
        )

    def perform_create(self, serializer):
        product = serializer.validated_data.get("product")
        description = serializer.validated_data.get("description", "")
        photo_urls = serializer.validated_data.get("photo_urls", [])
        location = serializer.validated_data.get("location", "")

        # Compute realistic risk score and determine routed state
        risk_score = calculate_complaint_risk_score(
            product=product,
            description=description,
            photo_urls=photo_urls,
        )
        routed_state = determine_routed_state(
            location=location,
            user=self.request.user,
        )

        serializer.save(
            filed_by=self.request.user,
            status="open",
            risk_score=risk_score,
            routed_to_state=routed_state,
        )

    @action(detail=False, methods=["get"], url_path="mine")
    def mine(self, request):
        """
        GET /api/complaints/mine/
        Returns list of complaints filed by the current citizen.
        """
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
