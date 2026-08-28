"""
Root URL Configuration for Legal Metrology Compliance Platform.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings

urlpatterns = [
    path("admin/", admin.site.urls),

    # === API v1 ===
    path("api/auth/", include("apps.accounts.urls")),
    path("api/products/", include("apps.product_master.urls")),
    path("api/scans/", include("apps.scans.urls")),
    path("api/rules/", include("apps.rules_engine.urls")),
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
