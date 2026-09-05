"""
Views for Compliance app: ComplianceCheckViewSet with confirm/override actions.
"""
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import ComplianceCheck, Violation, ProductComplianceHistory
from .serializers import ComplianceCheckDetailSerializer, ProductViolationHistorySerializer
from apps.common.permissions import IsFieldOfficer, IsStateController, IsNationalAdmin
from apps.notifications.models import AuditLog


class ComplianceCheckViewSet(viewsets.ModelViewSet):
    """
    API endpoint for Compliance Checks.
    POST /api/compliance-checks/{id}/confirm/  -> Officer confirms finding.
    POST /api/compliance-checks/{id}/override/ -> Officer overrides finding with notes.
    """
    queryset = (
        ComplianceCheck.objects.all()
        .select_related("scan", "scan__product", "reviewed_by_officer")
        .prefetch_related("violations", "violations__rule")
    )
    serializer_class = ComplianceCheckDetailSerializer
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=True, methods=["post"], url_path="confirm")
    def confirm(self, request, pk=None):
        """
        POST /api/compliance-checks/{id}/confirm/
        Officer confirms the automated compliance verdict.
        """
        check = self.get_object()
        check.reviewed_by_officer = request.user
        check.save(update_fields=["reviewed_by_officer"])

        AuditLog.objects.create(
            user=request.user,
            action="confirm_compliance_check",
            target_type="ComplianceCheck",
            target_id=str(check.id),
            metadata={"verdict": check.verdict},
        )

        serializer = self.get_serializer(check)
        return Response(
            {
                "message": "Compliance check verdict confirmed by officer.",
                "compliance_check": serializer.data,
            },
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["post"], url_path="override")
    def override(self, request, pk=None):
        """
        POST /api/compliance-checks/{id}/override/
        Officer overrides verdict (e.g. non_compliant -> compliant or vice-versa) with notes.
        """
        check = self.get_object()
        old_verdict = check.verdict
        new_verdict = request.data.get("verdict")
        notes = request.data.get("notes", "")

        if new_verdict not in ["compliant", "non_compliant", "needs_review"]:
            return Response(
                {"detail": "Invalid verdict. Must be 'compliant', 'non_compliant', or 'needs_review'."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        check.verdict = new_verdict
        check.reviewed_by_officer = request.user
        check.save(update_fields=["verdict", "reviewed_by_officer"])

        AuditLog.objects.create(
            user=request.user,
            action="override_compliance_check",
            target_type="ComplianceCheck",
            target_id=str(check.id),
            metadata={"old_verdict": old_verdict, "new_verdict": new_verdict, "notes": notes},
        )

        serializer = self.get_serializer(check)
        return Response(
            {
                "message": "Compliance check verdict successfully overridden.",
                "notes": notes,
                "compliance_check": serializer.data,
            },
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["post"], url_path="generate-report")
    def generate_report(self, request, pk=None):
        """
        POST /api/compliance-checks/{id}/generate-report/
        Body: {"regenerate": false} (optional)
        """
        check = self.get_object()
        regenerate = request.data.get("regenerate", False)

        from apps.reports.models import Report
        from apps.reports.serializers import ReportSerializer
        from apps.reports.services import generate_and_save_report

        if not regenerate:
            existing = Report.objects.filter(compliance_check=check).order_by("-generated_at").first()
            if existing and existing.file_url:
                return Response(ReportSerializer(existing).data, status=status.HTTP_200_OK)

        try:
            report = generate_and_save_report(compliance_check=check, officer=request.user)
            return Response(ReportSerializer(report).data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response(
                {"error": f"Report generation failed: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=True, methods=["get"], url_path="report")
    def get_report(self, request, pk=None):
        """
        GET /api/compliance-checks/{id}/report/
        """
        check = self.get_object()
        from apps.reports.models import Report
        from apps.reports.serializers import ReportSerializer

        existing = Report.objects.filter(compliance_check=check).order_by("-generated_at").first()
        if not existing or not existing.file_url:
            return Response({"detail": "No report found for this compliance check."}, status=status.HTTP_404_NOT_FOUND)
        return Response(ReportSerializer(existing).data, status=status.HTTP_200_OK)
