"""
Scans app URL configuration.
"""
from rest_framework.routers import DefaultRouter
from .views import ScanViewSet

router = DefaultRouter()
router.register(r"", ScanViewSet, basename="scan")

urlpatterns = router.urls
