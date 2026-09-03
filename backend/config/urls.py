"""
Root URL Configuration for Legal Metrology Compliance Platform.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response


@api_view(["GET"])
@permission_classes([AllowAny])
def api_root_view(request):
    """
    Root API health check and endpoint directory.
    """
    return Response({
        "status": "online",
        "service": "National Legal Metrology Compliance Platform API",
        "version": "1.0.0",
        "frontend_app": "http://localhost:5173",
        "admin_portal": "/admin/",
        "endpoints": {
            "auth": "/api/auth/",
            "products": "/api/products/",
            "scans": "/api/scans/",
            "rules": "/api/rules/",
            "compliance_checks": "/api/compliance-checks/",
            "cases": "/api/cases/",
            "complaints": "/api/complaints/",
            "inspections": "/api/inspections/",
            "reports": "/api/reports/",
            "ecommerce": "/api/ecommerce/",
            "notifications": "/api/notifications/",
            "dashboards": "/api/dashboards/",
        },
    })


urlpatterns = [
    # Root & API index
    path("", api_root_view, name="api-root"),
    path("api/", api_root_view, name="api-index"),

    # Django Admin
    path("admin/", admin.site.urls),

    # === API v1 ===
    path("api/auth/", include("apps.accounts.urls")),
    path("api/products/", include("apps.product_master.urls")),
    path("api/scans/", include("apps.scans.urls")),
    path("api/rules/", include("apps.rules_engine.urls")),
    path("api/admin/", include("apps.rules_engine.urls")),
    path("api/compliance/", include("apps.compliance.urls")),
    path("api/compliance-checks/", include("apps.compliance.urls")),
    path("api/cases/", include("apps.cases.urls")),

    path("api/complaints/", include("apps.complaints.urls")),
    path("api/inspections/", include("apps.inspections.urls")),
    path("api/reports/", include("apps.reports.urls")),
    path("api/ecommerce/", include("apps.ecommerce_integration.urls")),
    path("api/notifications/", include("apps.notifications.urls")),
    path("api/dashboards/", include("apps.dashboards.urls")),
]

# Debug toolbar (dev only)
if settings.DEBUG:
    try:
        import debug_toolbar
        urlpatterns = [
            path("__debug__/", include(debug_toolbar.urls)),
        ] + urlpatterns
    except ImportError:
        pass
