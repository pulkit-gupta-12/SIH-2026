"""
Cases URL configuration.
"""
from rest_framework.routers import DefaultRouter
from .views import CaseViewSet

router = DefaultRouter()
router.register(r"", CaseViewSet, basename="case")

urlpatterns = router.urls
