"""
Views for Compliance app: ComplianceCheckViewSet with confirm/override actions.
"""
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import ComplianceCheck, Violation, ProductComplianceHistory
from .serializers import ComplianceCheckDetailSerializer, ProductViolationHistorySerializer
from apps.common.permissions import IsFieldOfficer, IsStateController, IsNationalAdmin


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

        serializer = self.get_serializer(check)
        return Response(
            {
                "message": "Compliance check verdict successfully overridden.",
                "notes": notes,
                "compliance_check": serializer.data,
            },
            status=status.HTTP_200_OK,
        )
