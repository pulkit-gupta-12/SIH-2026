"""
Views for Scans app.
"""
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action

from .models import Scan
from .serializers import ScanDetailSerializer, ScanCreateSerializer
from apps.common.permissions import IsCitizenOrFieldOfficer, IsCitizen
from apps.product_master.views import build_compliance_snapshot_payload
from apps.product_master.serializers import ComplianceSnapshotSerializer
from apps.notifications.models import AuditLog
from .services import (
    resolve_product_from_barcode,
    get_existing_compliance_result,
    process_scan_pipeline,
)


class ScanViewSet(viewsets.ModelViewSet):
    """
    API endpoint for Scans.
    POST /api/scans/ ->
      - Citizen with existing scan history: instant stored snapshot (200 OK, no OCR, no Scan row).
      - Citizen first scan: requires 1 photo, runs OCR stub + evaluation, records history (201 Created).
      - Field Officer: full multi-image guided capture flow.
    """
    queryset = (
        Scan.objects.all()
        .select_related("product", "performed_by")
        .prefetch_related("images", "extracted_fields")
    )
    permission_classes = [permissions.IsAuthenticated, IsCitizenOrFieldOfficer]

    def get_serializer_class(self):
        if self.action == "create":
            return ScanCreateSerializer
        return ScanDetailSerializer

    def create(self, request, *args, **kwargs):
        serializer = ScanCreateSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        is_citizen = (
            request.user.role_assignments.filter(role__name="citizen").exists()
            if request.user.is_authenticated
            else False
        )

        if is_citizen:
            return self._handle_citizen_scan(request, data)
        return self._handle_officer_scan(request, data)

    def _handle_citizen_scan(self, request, data):
        barcode = data.get("barcode")
        product = data.get("product")

        if barcode and not product:
            product = resolve_product_from_barcode(barcode, category=data.get("category", "general"))

        # Check if product has any prior ComplianceCheck (scanned before by any role)
        existing_check = get_existing_compliance_result(product) if product else None
        if existing_check is not None:
            # Stored result exists -> return immediately (no OCR, no Scan row)
            payload = build_compliance_snapshot_payload(product, existing_check)
            serializer = ComplianceSnapshotSerializer(payload)
            return Response(serializer.data, status=status.HTTP_200_OK)

        # First-time scan: require an image
        image_urls = data.get("image_urls", [])
        if not image_urls:
            return Response(
                {
                    "detail": "This product has not been scanned before — please provide a photo.",
                    "needs_photo": True,
                    "product_id": product.id if product else None,
                    "barcode": barcode,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Create lightweight Scan row
        scan = Scan.objects.create(
            performed_by=request.user,
            product=product,
            role_context="citizen",
            capture_method="single_image",
            status="pending",
        )

        AuditLog.objects.create(
            user=request.user,
            action="create_scan",
            target_type="Scan",
            target_id=str(scan.id),
            metadata={
                "role_context": "citizen",
                "gtin_barcode": getattr(product, "gtin_barcode", barcode),
                "product_id": getattr(product, "id", None),
            },
        )

        # Run OCR stub + evaluation pipeline; persist history (case=None)
        check = process_scan_pipeline(
            scan,
            image_urls=image_urls,
            category=data.get("category", "general"),
            is_citizen_scan=True,
        )

        if check:
            AuditLog.objects.create(
                user=request.user,
                action="create_compliance_check",
                target_type="ComplianceCheck",
                target_id=str(check.id),
                metadata={
                    "verdict": check.verdict,
                    "scan_id": scan.id,
                    "violations_count": check.violations.count(),
                },
            )

        # Return compliance snapshot
        payload = build_compliance_snapshot_payload(scan.product or product, check)
        serializer = ComplianceSnapshotSerializer(payload)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def _handle_officer_scan(self, request, data):
        barcode = data.get("barcode")
        product = data.get("product")
        if barcode and not product:
            product = resolve_product_from_barcode(barcode, category=data.get("category", "general"))

        image_urls = data.get("image_urls", [])
        category = data.get("category", "general")
        capture_method = data.get("capture_method", "guided_capture")
        location = data.get("location")

        scan = Scan.objects.create(
            performed_by=request.user,
            product=product,
            role_context="officer",
            location=location,
            capture_method=capture_method,
            status="pending",
        )

        AuditLog.objects.create(
            user=request.user,
            action="create_scan",
            target_type="Scan",
            target_id=str(scan.id),
            metadata={
                "role_context": "officer",
                "capture_method": capture_method,
                "location": location,
                "gtin_barcode": getattr(product, "gtin_barcode", barcode),
                "product_id": getattr(product, "id", None),
            },
        )

        check = process_scan_pipeline(
            scan,
            image_urls=image_urls,
            category=category,
            is_citizen_scan=False,
        )

        if check:
            AuditLog.objects.create(
                user=request.user,
                action="create_compliance_check",
                target_type="ComplianceCheck",
                target_id=str(check.id),
                metadata={
                    "verdict": check.verdict,
                    "scan_id": scan.id,
                    "violations_count": check.violations.count(),
                },
            )

        detail_serializer = ScanDetailSerializer(scan)
        return Response(detail_serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["get"], url_path="processing-result")
    def processing_result(self, request, pk=None):
        """GET /api/scans/{id}/processing-result/"""
        scan = self.get_object()
        serializer = ScanDetailSerializer(scan)
        return Response(serializer.data, status=status.HTTP_200_OK)
