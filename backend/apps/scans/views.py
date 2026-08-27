"""
Views for Scans app.
"""
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action

from .models import Scan
from .serializers import ScanDetailSerializer, ScanCreateSerializer
from .services import process_scan_pipeline


class ScanViewSet(viewsets.ModelViewSet):
    """
    API endpoint for Scans.
    POST /api/scans/ -> uploads scan, calls OCR stub, runs Rule Engine, returns verdict.
    """
    queryset = Scan.objects.all().select_related("product", "performed_by").prefetch_related("scan_images", "extracted_fields")
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.action == "create":
            return ScanCreateSerializer
        return ScanDetailSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_validate_serializer = serializer.is_valid(raise_exception=True)

        image_urls = serializer.validated_data.pop("image_urls", [])
        category = serializer.validated_data.pop("category", "general")

        scan = serializer.save(performed_by=request.user)

        # Trigger OCR + Rule Engine pipeline
        process_scan_pipeline(scan, image_urls=image_urls, category=category)

        # Return full detail serializer
        detail_serializer = ScanDetailSerializer(scan)
        return Response(detail_serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["get"], url_path="processing-result")
    def processing_result(self, request, pk=None):
        """GET /api/scans/{id}/processing-result/"""
        scan = self.get_object()
        serializer = ScanDetailSerializer(scan)
        return Response(serializer.data)
