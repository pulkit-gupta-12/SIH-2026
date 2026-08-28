"""
Views for Cases app: CaseViewSet with dynamic statutory pathing.
"""
from datetime import date, timedelta
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response

from .models import Case, ImprovementNotice, PenaltyCase
from .serializers import CaseDetailSerializer, CaseCreateSerializer
from apps.compliance.models import ProductComplianceHistory, Violation
from apps.complaints.models import Complaint
from apps.product_master.models import Product
from apps.common.permissions import IsOfficerOrController


class CaseViewSet(viewsets.ModelViewSet):
    """
    API endpoint for Legal Metrology Enforcement Cases.
    POST /api/cases/ -> Spawns Section 29 Improvement Notice (1st offense) or Section 39 Penalty Case (repeat).
    GET  /api/cases/ -> Lists active cases.
    """
    queryset = (
        Case.objects.all()
        .select_related("product", "violation", "opened_by", "improvement_notice", "penalty_case")
        .prefetch_related("violation__rule")
        .order_by("-created_at")
    )
    permission_classes = [permissions.IsAuthenticated, IsOfficerOrController]

    def get_serializer_class(self):
        if self.action == "create":
            return CaseCreateSerializer
        return CaseDetailSerializer

    def create(self, request, *args, **kwargs):
        user = request.user

        serializer = CaseCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        product = data["product"]
        violation = data.get("violation")
        complaint_id = data.get("complaint")
        rectification_days = data.get("rectification_days", 30)

        # READ ONLY from existing ProductComplianceHistory record written at scan time
        history_entry = None
        if violation:
            history_entry = ProductComplianceHistory.objects.filter(
                product=product, violation=violation
            ).first()
        if not history_entry:
            history_entry = ProductComplianceHistory.objects.filter(product=product).first()

        is_first_time = history_entry.is_first_time if history_entry else True

        if is_first_time:
            # 1st Offense -> Section 29 Improvement Notice (30-day rectification window)
            case = Case.objects.create(
                product=product,
                violation=violation,
                complaint_id=complaint_id,
                classification="first_time",
                status="notice_sent",
                opened_by=user,
            )
            deadline = date.today() + timedelta(days=rectification_days)
            ImprovementNotice.objects.create(
                case=case,
                issued_by=user,
                rectification_deadline=deadline,
                outcome="pending",
            )
        else:
            # Repeat Offense -> Section 39 Penalty Case
            case = Case.objects.create(
                product=product,
                violation=violation,
                complaint_id=complaint_id,
                classification="repeat",
                status="escalated",
                opened_by=user,
            )
            PenaltyCase.objects.create(
                case=case,
                escalated_by=user,
                payment_status="pending",
                appeal_status="none",
            )

        # Link case back to the compliance history entry without creating any duplicate entry
        if history_entry and not history_entry.case:
            history_entry.case = case
            history_entry.save(update_fields=["case"])

        # If opened from a citizen complaint, update complaint status to 'under_investigation'
        if complaint_id:
            Complaint.objects.filter(id=complaint_id).update(status="under_investigation")

        detail_serializer = CaseDetailSerializer(case)
        return Response(detail_serializer.data, status=status.HTTP_201_CREATED)
