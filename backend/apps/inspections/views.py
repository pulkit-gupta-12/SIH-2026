"""
Views for Inspections app: InspectionTargetViewSet with /queue/ action.
"""
from django.db.models import Q
from django.utils.dateparse import parse_date
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import InspectionTarget
from .serializers import InspectionTargetSerializer
from apps.complaints.models import Complaint
from apps.compliance.models import ComplianceCheck
from apps.reports.models import Report
from apps.cases.models import Case
from apps.common.permissions import IsFieldOfficer, IsStateController, IsNationalAdmin


class InspectionTargetViewSet(viewsets.ModelViewSet):
    """
    API endpoint for Inspection Targets and Officer Queue.
    GET /api/inspections/queue/   -> Priority-sorted inspection queue for officer.
    GET /api/inspections/history/ -> Filterable historical inspection logs for officer.
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
            role__name__in=["field_officer", "state_controller", "national_admin", "rule_admin"]
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

    @action(detail=False, methods=["get"], url_path="history")
    def history(self, request):
        """
        GET /api/inspections/history/
        Returns list of completed inspections with product details, inspection date,
        inspecting officer, verdict, violation count, and statutory report links.
        Supports query params:
          - search: brand, product name, or barcode
          - verdict: compliant, non_compliant, needs_review
          - date_from: YYYY-MM-DD
          - date_to: YYYY-MM-DD
          - officer: officer username or ID, or 'me'
          - all: true (disable pagination)
        """
        user = request.user
        is_officer = user.role_assignments.filter(
            role__name__in=["field_officer", "state_controller", "national_admin", "rule_admin"]
        ).exists()

        if not is_officer:
            return Response(
                {"detail": "Field Officer, Controller, or Admin role required."},
                status=status.HTTP_403_FORBIDDEN,
            )

        qs = (
            ComplianceCheck.objects.all()
            .select_related(
                "scan",
                "scan__product",
                "scan__performed_by",
                "reviewed_by_officer",
            )
            .prefetch_related(
                "violations",
                "violations__rule",
                "reports",
            )
            .order_by("-created_at")
        )

        # Search filter
        search = request.query_params.get("search", "").strip()
        if search:
            qs = qs.filter(
                Q(scan__product__product_name__icontains=search)
                | Q(scan__product__brand_name__icontains=search)
                | Q(scan__product__gtin_barcode__icontains=search)
                | Q(scan__location__icontains=search)
            )

        # Verdict filter
        verdict = request.query_params.get("verdict", "").strip()
        if verdict and verdict != "all":
            qs = qs.filter(verdict=verdict)

        # Date range filters
        date_from = request.query_params.get("date_from", "").strip()
        if date_from:
            d_from = parse_date(date_from)
            if d_from:
                qs = qs.filter(created_at__date__gte=d_from)

        date_to = request.query_params.get("date_to", "").strip()
        if date_to:
            d_to = parse_date(date_to)
            if d_to:
                qs = qs.filter(created_at__date__lte=d_to)

        # Officer filter
        officer_param = request.query_params.get("officer", "").strip()
        if officer_param:
            if officer_param == "me":
                qs = qs.filter(
                    Q(reviewed_by_officer=user) | Q(scan__performed_by=user)
                )
            elif officer_param.isdigit():
                qs = qs.filter(
                    Q(reviewed_by_officer_id=int(officer_param))
                    | Q(scan__performed_by_id=int(officer_param))
                )
            else:
                qs = qs.filter(
                    Q(reviewed_by_officer__username__icontains=officer_param)
                    | Q(scan__performed_by__username__icontains=officer_param)
                )

        no_paginate = request.query_params.get("all", "").lower() in ("true", "1", "yes")

        def build_item(check):
            scan = check.scan
            prod = scan.product if scan else None

            # Identify inspecting officer
            officer_user = check.reviewed_by_officer or (scan.performed_by if scan else None)
            officer_info = {
                "id": officer_user.id if officer_user else None,
                "username": officer_user.username if officer_user else "System / Auto",
                "name": (officer_user.get_full_name() or officer_user.username) if officer_user else "System",
            }

            # Identify linked report
            report_obj = check.reports.order_by("-generated_at").first()
            if not report_obj and check.violations.exists():
                case_with_report = Case.objects.filter(violation__compliance_check=check).first()
                if case_with_report:
                    report_obj = case_with_report.reports.order_by("-generated_at").first()

            report_data = None
            if report_obj and report_obj.file_url:
                report_data = {
                    "id": report_obj.id,
                    "file_url": report_obj.file_url,
                    "format": report_obj.format,
                    "signed": report_obj.signed,
                    "generated_at": report_obj.generated_at.isoformat(),
                }

            # Check if there is an associated case
            linked_case = Case.objects.filter(violation__compliance_check=check).first()

            return {
                "id": check.id,
                "compliance_check_id": check.id,
                "scan_id": check.scan_id,
                "product": {
                    "id": prod.id if prod else None,
                    "product_name": prod.product_name if prod else "Unregistered Package",
                    "brand_name": prod.brand_name if prod else "Generic",
                    "gtin_barcode": prod.gtin_barcode if prod else (scan.canonical_data.get("barcode") if scan and scan.canonical_data else "N/A"),
                    "category": prod.category if prod else "general",
                    "manufacturer_name": prod.manufacturer_name if prod else "",
                },
                "verdict": check.verdict,
                "overall_confidence": round(check.overall_confidence, 2),
                "inspection_date": check.created_at.isoformat(),
                "officer": officer_info,
                "location": scan.location if scan and scan.location else "Market Inspection Site",
                "capture_method": scan.capture_method if scan else "guided_capture",
                "violations_count": check.violations.count(),
                "violations": [
                    {
                        "id": v.id,
                        "rule_id_code": v.rule.rule_id_code if v.rule else "",
                        "section_ref": v.rule.section_ref if v.rule else "",
                        "description": v.description,
                    }
                    for v in check.violations.all()[:5]
                ],
                "report": report_data,
                "case_id": linked_case.id if linked_case else None,
            }

        if no_paginate:
            results = [build_item(c) for c in qs]
            return Response(results, status=status.HTTP_200_OK)

        page = self.paginate_queryset(qs)
        if page is not None:
            items = [build_item(c) for c in page]
            return self.get_paginated_response(items)

        results = [build_item(c) for c in qs]
        return Response(results, status=status.HTTP_200_OK)
