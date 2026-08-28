"""
Rules Engine URL configuration (Phase 4.3).
"""
from django.urls import path
from .views import (
    IncomingNotificationsView,
    RuleDraftCreateView,
    RuleDraftDetailView,
    RuleDraftApproveView,
    RuleDraftReviseView,
    RuleDraftSimulateView,
    RuleDraftPublishView,
    RuleRepositoryListView,
    AdminDashboardSummaryView,
    InspectionWeightConfigView,
)

urlpatterns = [
    # Incoming notifications
    path("incoming-notifications/", IncomingNotificationsView.as_view(), name="incoming_notifications"),

    # Rule Draft lifecycle
    path("draft/", RuleDraftCreateView.as_view(), name="rule_draft_create"),
    path("<int:pk>/", RuleDraftDetailView.as_view(), name="rule_draft_detail"),
    path("<int:pk>/approve/", RuleDraftApproveView.as_view(), name="rule_draft_approve"),
    path("<int:pk>/revise/", RuleDraftReviseView.as_view(), name="rule_draft_revise"),
    path("<int:pk>/simulate/", RuleDraftSimulateView.as_view(), name="rule_draft_simulate"),
    path("<int:pk>/publish/", RuleDraftPublishView.as_view(), name="rule_draft_publish"),

    # Admin Analytics & Weights
    path("admin-dashboard/", AdminDashboardSummaryView.as_view(), name="admin_dashboard_summary"),
    path("dashboard/summary/", AdminDashboardSummaryView.as_view(), name="admin_dashboard_summary_alias"),
    path("inspection-weights/", InspectionWeightConfigView.as_view(), name="inspection_weights"),

    # Live repository list
    path("", RuleRepositoryListView.as_view(), name="rule_repository_list"),
]
