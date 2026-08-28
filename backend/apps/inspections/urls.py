"""
Inspections URL configuration.
"""
from rest_framework.routers import DefaultRouter
from .views import InspectionTargetViewSet

router = DefaultRouter()
router.register(r"", InspectionTargetViewSet, basename="inspection")

urlpatterns = router.urls
