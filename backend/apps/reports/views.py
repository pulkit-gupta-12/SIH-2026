"""
Views for Reports app.
Provides report generation and retrieval endpoints for Field Officers and Controllers.
"""
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response

from .models import Report
from .serializers import ReportSerializer
from .services import generate_and_save_report
from apps.cases.models import Case
from apps.compliance.models import ComplianceCheck
from apps.common.permissions import IsOfficerOrController


class ReportViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for listing and retrieving inspection reports.
    """
    queryset = Report.objects.all().select_related("case", "compliance_check").order_by("-generated_at")
    serializer_class = ReportSerializer
    permission_classes = [permissions.IsAuthenticated, IsOfficerOrController]

    @action(detail=False, methods=["post"], url_path="generate")
    def generate(self, request):
        """
        POST /api/reports/generate/
        Body: {
            "case_id": <int, optional>,
            "compliance_check_id": <int, optional>,
            "regenerate": <bool, optional>
        }
        """
        case_id = request.data.get("case_id")
        check_id = request.data.get("compliance_check_id")
        regenerate = request.data.get("regenerate", False)

        if not case_id and not check_id:
            return Response(
                {"error": "Either 'case_id' or 'compliance_check_id' must be provided."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        case = None
        check = None

        if case_id:
            try:
                case = Case.objects.select_related("product", "violation", "opened_by").get(id=case_id)
            except Case.DoesNotExist:
                return Response({"error": f"Case #{case_id} not found."}, status=status.HTTP_404_NOT_FOUND)

        if check_id:
            try:
                check = ComplianceCheck.objects.select_related("scan", "scan__product", "reviewed_by_officer").get(id=check_id)
            except ComplianceCheck.DoesNotExist:
                return Response({"error": f"ComplianceCheck #{check_id} not found."}, status=status.HTTP_404_NOT_FOUND)

        # Check if report already exists and regenerate was not requested
        existing_report = None
        if case and not regenerate:
            existing_report = Report.objects.filter(case=case).order_by("-generated_at").first()
        elif check and not regenerate:
            existing_report = Report.objects.filter(compliance_check=check).order_by("-generated_at").first()

        if existing_report and existing_report.file_url:
            serializer = ReportSerializer(existing_report)
            return Response(serializer.data, status=status.HTTP_200_OK)

        # Generate report
        try:
            report = generate_and_save_report(
                case=case,
                compliance_check=check,
                officer=request.user,
            )
            serializer = ReportSerializer(report)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response(
                {"error": f"Report generation failed: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=False, methods=["get"], url_path="latest")
    def latest(self, request):
        """
        GET /api/reports/latest/?case_id=X OR ?compliance_check_id=Y
        """
        case_id = request.query_params.get("case_id")
        check_id = request.query_params.get("compliance_check_id")

        query = Report.objects.none()
        if case_id:
            query = Report.objects.filter(case_id=case_id)
        elif check_id:
            query = Report.objects.filter(compliance_check_id=check_id)
        else:
            return Response({"error": "Provide case_id or compliance_check_id"}, status=status.HTTP_400_BAD_REQUEST)

        latest_rep = query.order_by("-generated_at").first()
        if not latest_rep:
            return Response({"detail": "No report found."}, status=status.HTTP_404_NOT_FOUND)

        return Response(ReportSerializer(latest_rep).data)
