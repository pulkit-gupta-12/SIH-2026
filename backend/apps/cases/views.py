"""
Views for Cases app: CaseViewSet with dynamic statutory pathing.
"""
from datetime import date, timedelta
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Case, ImprovementNotice, PenaltyCase
from .serializers import CaseDetailSerializer, CaseCreateSerializer
from apps.compliance.models import ProductComplianceHistory, Violation
from apps.complaints.models import Complaint
from apps.product_master.models import Product
from apps.common.permissions import IsOfficerOrController
from apps.notifications.models import AuditLog


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

        AuditLog.objects.create(
            user=user,
            action="create_case",
            target_type="Case",
            target_id=str(case.id),
            metadata={
                "classification": case.classification,
                "status": case.status,
                "product_id": getattr(product, "id", None),
                "violation_id": getattr(violation, "id", None),
                "complaint_id": complaint_id,
            },
        )

        detail_serializer = CaseDetailSerializer(case)
        return Response(detail_serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"], url_path="generate-report")
    def generate_report(self, request, pk=None):
        """
        POST /api/cases/{id}/generate-report/
        Body: {"regenerate": false} (optional)
        """
        case = self.get_object()
        regenerate = request.data.get("regenerate", False)

        from apps.reports.models import Report
        from apps.reports.serializers import ReportSerializer
        from apps.reports.services import generate_and_save_report

        if not regenerate:
            existing = Report.objects.filter(case=case).order_by("-generated_at").first()
            if existing and existing.file_url:
                return Response(ReportSerializer(existing).data, status=status.HTTP_200_OK)

        try:
            report = generate_and_save_report(case=case, officer=request.user)
            return Response(ReportSerializer(report).data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response(
                {"error": f"Report generation failed: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=False, methods=["post"], url_path="generate-report")
    def generate_report_from_check(self, request):
        """
        POST /api/cases/generate-report/
        Allows generating report directly from a compliance_check_id for pre-case inspections.
        Body: {"compliance_check_id": 123, "regenerate": false}
        """
        check_id = request.data.get("compliance_check_id")
        case_id = request.data.get("case_id")
        regenerate = request.data.get("regenerate", False)

        if not check_id and not case_id:
            return Response(
                {"error": "Provide 'compliance_check_id' or 'case_id'."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        from apps.reports.models import Report
        from apps.reports.serializers import ReportSerializer
        from apps.reports.services import generate_and_save_report
        from apps.compliance.models import ComplianceCheck

        case = None
        check = None
        if case_id:
            case = Case.objects.filter(id=case_id).first()
            if not case:
                return Response({"error": f"Case #{case_id} not found."}, status=status.HTTP_404_NOT_FOUND)
        if check_id:
            check = ComplianceCheck.objects.filter(id=check_id).first()
            if not check:
                return Response({"error": f"ComplianceCheck #{check_id} not found."}, status=status.HTTP_404_NOT_FOUND)

        if not regenerate:
            existing = None
            if case:
                existing = Report.objects.filter(case=case).order_by("-generated_at").first()
            elif check:
                existing = Report.objects.filter(compliance_check=check).order_by("-generated_at").first()
            if existing and existing.file_url:
                return Response(ReportSerializer(existing).data, status=status.HTTP_200_OK)

        try:
            report = generate_and_save_report(case=case, compliance_check=check, officer=request.user)
            return Response(ReportSerializer(report).data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response(
                {"error": f"Report generation failed: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=True, methods=["get"], url_path="report")
    def get_report(self, request, pk=None):
        """
        GET /api/cases/{id}/report/
        """
        case = self.get_object()
        from apps.reports.models import Report
        from apps.reports.serializers import ReportSerializer

        existing = Report.objects.filter(case=case).order_by("-generated_at").first()
        if not existing or not existing.file_url:
            return Response({"detail": "No report found for this case."}, status=status.HTTP_404_NOT_FOUND)
        return Response(ReportSerializer(existing).data, status=status.HTTP_200_OK)
