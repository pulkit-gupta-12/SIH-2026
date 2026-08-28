"""
Views for Rule Engine Admin Console (Phase 4.3).
Handles Notification Ingestion, AI Draft Generation, Admin Review, Revise/Approve,
Sandbox Simulation, Rule Publication, and Admin Dashboard Analytics.
"""
from datetime import date
from django.utils import timezone
from django.db import transaction
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, permissions, status, filters
from rest_framework.views import APIView
from rest_framework.response import Response

from apps.common.permissions import IsNationalAdmin, IsOfficerOrController
from apps.notifications.models import AuditLog
from .models import (
    RuleSource,
    Rule,
    RuleNotification,
    RuleDraft,
    RuleSimulationResult,
    InspectionWeightConfig,
)
from .serializers import (
    RuleSerializer,
    RuleNotificationSerializer,
    RuleDraftSerializer,
    RuleDraftCreateSerializer,
    RuleDraftReviseSerializer,
    RuleDraftApproveSerializer,
    RuleSimulationResultSerializer,
    InspectionWeightConfigSerializer,
)
from .generator import generate_rule_draft_from_notification
from .simulator import run_sandbox_simulation
from .analytics import get_admin_dashboard_summary, get_or_create_inspection_weights


class IncomingNotificationsView(generics.ListAPIView):
    """
    GET /api/rules/incoming-notifications/
    Lists detected/seeded legal amendment notifications.
    """
    permission_classes = [permissions.IsAuthenticated, IsNationalAdmin]
    serializer_class = RuleNotificationSerializer
    queryset = RuleNotification.objects.all().order_by("-date_detected")

    def get_queryset(self):
        qs = super().get_queryset()
        # Seed realistic notifications if empty so dashboard is immediately demoable
        if not qs.exists():
            RuleNotification.objects.create(
                notification_no="G.S.R. 248(E)/2026",
                title="Legal Metrology (Packaged Commodities) Fourth Amendment Rules, 2026",
                source_text=(
                    "In exercise of powers conferred by sub-section (1) read with clause (j) and (q) of sub-section (2) "
                    "of section 52 of the Legal Metrology Act, 2009, the Central Government hereby makes the following rules "
                    "further to amend the Legal Metrology (Packaged Commodities) Rules, 2011. In Rule 18, Table II, "
                    "the minimum height of numerals for net quantity and MRP shall be increased to 2.5 mm for packages up to 1000g."
                ),
                gazette_url="https://egazette.gov.in/notifications/gsr248e.pdf",
                published_date=date(2026, 2, 10),
                category="general",
                status="new",
            )
            RuleNotification.objects.create(
                notification_no="G.S.R. 185(E)/2026",
                title="Mandatory Digital QR & Unit Sale Price Display Guidelines for E-Commerce",
                source_text=(
                    "Amendments to Rule 6(10): All e-commerce marketplace entities and pre-packaged commodity packers "
                    "must display unit sale price per gram/ml prominently alongside MRP, and provide a scannable QR Code "
                    "for direct National Legal Metrology database authentication."
                ),
                gazette_url="https://egazette.gov.in/notifications/gsr185e.pdf",
                published_date=date(2026, 1, 20),
                category="ecommerce",
                status="new",
            )
            RuleNotification.objects.create(
                notification_no="G.S.R. 89(E)/2026",
                title="Harmonized Food Declaration Standards & Expiry Prominence Regulations",
                source_text=(
                    "In Rule 6(1)(d), Month and Year of manufacture or packing shall be declared in words or numerals "
                    "with high contrast and minimum font height 2.0 mm across all food & beverage commodities."
                ),
                gazette_url="https://egazette.gov.in/notifications/gsr89e.pdf",
                published_date=date(2026, 1, 5),
                category="food",
                status="new",
            )
            qs = RuleNotification.objects.all().order_by("-date_detected")
        return qs


class RuleDraftCreateView(APIView):
    """
    POST /api/rules/draft/
    Creates a RuleDraft from a notification (AI-generated diff) or custom payload.
    """
    permission_classes = [permissions.IsAuthenticated, IsNationalAdmin]

    def post(self, request, *args, **kwargs):
        serializer = RuleDraftCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        notification_id = data.get("notification_id")
        notification = None
        if notification_id:
            try:
                notification = RuleNotification.objects.get(pk=notification_id)
            except RuleNotification.DoesNotExist:
                return Response({"error": "RuleNotification not found."}, status=status.HTTP_404_NOT_FOUND)

        if notification:
            # Generate structured diff using AI generator
            generated = generate_rule_draft_from_notification(notification)
            supersedes_rule = None
            if generated.get("supersedes_rule_id"):
                supersedes_rule = Rule.objects.filter(pk=generated["supersedes_rule_id"]).first()

            draft = RuleDraft.objects.create(
                notification=notification,
                rule_id_code=data.get("rule_id_code") or generated["rule_id_code"],
                section_ref=data.get("section_ref") or generated["section_ref"],
                category=data.get("category") or generated["category"],
                old_clause_text=data.get("old_clause_text") or generated["old_clause_text"],
                new_clause_text=data.get("new_clause_text") or generated["new_clause_text"],
                proposed_condition=data.get("proposed_condition") or generated["proposed_condition"],
                supersedes_rule=supersedes_rule,
                status="pending_review",
                reviewing_admin=request.user,
                comments=[{
                    "admin": request.user.username,
                    "action": "draft_created",
                    "comment": f"Draft automatically generated from notification {notification.notification_no}.",
                    "timestamp": timezone.now().isoformat(),
                }],
            )
            notification.status = "drafted"
            notification.save(update_fields=["status"])
        else:
            draft = RuleDraft.objects.create(
                rule_id_code=data.get("rule_id_code", f"PCR2026-CUSTOM-{date.today().strftime('%Y%m%d')}"),
                section_ref=data.get("section_ref", "PC Rules 2011 (Amended)"),
                category=data.get("category", "general"),
                old_clause_text=data.get("old_clause_text", ""),
                new_clause_text=data.get("new_clause_text", ""),
                proposed_condition=data.get("proposed_condition", {"type": "required_field", "field": "mfg_date"}),
                status="pending_review",
                reviewing_admin=request.user,
                comments=[{
                    "admin": request.user.username,
                    "action": "manual_draft_created",
                    "comment": "Draft manually registered by legal administrator.",
                    "timestamp": timezone.now().isoformat(),
                }],
            )

        AuditLog.objects.create(
            user=request.user,
            action="create_rule_draft",
            target_type="RuleDraft",
            target_id=str(draft.id),
            metadata={"rule_id_code": draft.rule_id_code},
        )

        return Response(RuleDraftSerializer(draft).data, status=status.HTTP_201_CREATED)


class RuleDraftDetailView(APIView):
    """
    GET /api/rules/{id}/
    Retrieves a single RuleDraft with old vs new clause diff and simulation metrics.
    If the ID is a live Rule ID instead of a draft, returns the published Rule details.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk, *args, **kwargs):
        draft = RuleDraft.objects.filter(pk=pk).first()
        if draft:
            return Response(RuleDraftSerializer(draft).data)

        # Fallback check if asking for published Rule
        rule = Rule.objects.filter(pk=pk).first()
        if rule:
            return Response(RuleSerializer(rule).data)

        return Response({"error": "Rule draft or rule not found."}, status=status.HTTP_404_NOT_FOUND)


class RuleDraftApproveView(APIView):
    """
    POST /api/rules/{id}/approve/
    Marks draft approved and sets its planned effective_date.
    """
    permission_classes = [permissions.IsAuthenticated, IsNationalAdmin]

    def post(self, request, pk, *args, **kwargs):
        draft = RuleDraft.objects.filter(pk=pk).first()
        if not draft:
            return Response({"error": "RuleDraft not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = RuleDraftApproveSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        effective_date = serializer.validated_data["effective_date"]
        comment_text = serializer.validated_data.get("comment", "Draft approved by National Admin.")

        draft.status = "approved"
        draft.effective_date = effective_date
        draft.reviewing_admin = request.user

        comments = list(draft.comments)
        comments.append({
            "admin": request.user.username,
            "action": "approved",
            "comment": comment_text,
            "effective_date": str(effective_date),
            "timestamp": timezone.now().isoformat(),
        })
        draft.comments = comments
        draft.save()

        if draft.notification:
            draft.notification.status = "approved"
            draft.notification.save(update_fields=["status"])

        AuditLog.objects.create(
            user=request.user,
            action="approve_rule_draft",
            target_type="RuleDraft",
            target_id=str(draft.id),
            metadata={"effective_date": str(effective_date)},
        )

        return Response(RuleDraftSerializer(draft).data, status=status.HTTP_200_OK)


class RuleDraftReviseView(APIView):
    """
    POST /api/rules/{id}/revise/
    Updates draft IN PLACE with admin edits + comments.
    CRITICAL: Does NOT create duplicate RuleNotification or RuleDraft rows!
    """
    permission_classes = [permissions.IsAuthenticated, IsNationalAdmin]

    def post(self, request, pk, *args, **kwargs):
        draft = RuleDraft.objects.filter(pk=pk).first()
        if not draft:
            return Response({"error": "RuleDraft not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = RuleDraftReviseSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        # Update draft fields in place
        if "rule_id_code" in data and data["rule_id_code"]:
            draft.rule_id_code = data["rule_id_code"]
        if "section_ref" in data and data["section_ref"]:
            draft.section_ref = data["section_ref"]
        if "category" in data and data["category"]:
            draft.category = data["category"]
        if "old_clause_text" in data:
            draft.old_clause_text = data["old_clause_text"]
        if "new_clause_text" in data and data["new_clause_text"]:
            draft.new_clause_text = data["new_clause_text"]
        if "proposed_condition" in data and data["proposed_condition"]:
            draft.proposed_condition = data["proposed_condition"]
        if "effective_date" in data:
            draft.effective_date = data["effective_date"]

        draft.status = "revised"
        draft.reviewing_admin = request.user

        # Record revision history
        comment_text = data.get("comment") or "Admin revised draft clauses and condition thresholds."
        comments = list(draft.comments)
        comments.append({
            "admin": request.user.username,
            "action": "revised",
            "comment": comment_text,
            "timestamp": timezone.now().isoformat(),
        })
        draft.comments = comments
        draft.save()

        AuditLog.objects.create(
            user=request.user,
            action="revise_rule_draft",
            target_type="RuleDraft",
            target_id=str(draft.id),
            metadata={"comment": comment_text},
        )

        return Response(RuleDraftSerializer(draft).data, status=status.HTTP_200_OK)


class RuleDraftSimulateView(APIView):
    """
    POST /api/rules/{id}/simulate/
    Runs read-only sandbox simulation of the draft against historical inspections.
    Writes strictly to RuleSimulationResult.
    """
    permission_classes = [permissions.IsAuthenticated, IsNationalAdmin]

    def post(self, request, pk, *args, **kwargs):
        draft = RuleDraft.objects.filter(pk=pk).first()
        if not draft:
            return Response({"error": "RuleDraft not found."}, status=status.HTTP_404_NOT_FOUND)

        result = run_sandbox_simulation(draft)

        AuditLog.objects.create(
            user=request.user,
            action="simulate_rule_draft",
            target_type="RuleDraft",
            target_id=str(draft.id),
            metadata={
                "before_rate": result.before_compliance_rate,
                "after_rate": result.after_compliance_rate,
            },
        )

        return Response(RuleSimulationResultSerializer(result).data, status=status.HTTP_200_OK)


class RuleDraftPublishView(APIView):
    """
    POST /api/rules/{id}/publish/
    Creates a new live versioned Rule effective as of effective_date,
    archives/supersedes prior rule versions, and sets draft status to published.
    """
    permission_classes = [permissions.IsAuthenticated, IsNationalAdmin]

    def post(self, request, pk, *args, **kwargs):
        draft = RuleDraft.objects.filter(pk=pk).first()
        if not draft:
            return Response({"error": "RuleDraft not found."}, status=status.HTTP_404_NOT_FOUND)

        effective_date = draft.effective_date or request.data.get("effective_date") or date.today()
        if isinstance(effective_date, str):
            try:
                effective_date = date.fromisoformat(effective_date)
            except ValueError:
                effective_date = date.today()

        with transaction.atomic():
            # 1. Source lookup or creation
            source = None
            if draft.notification:
                source, _ = RuleSource.objects.get_or_create(
                    notification_no=draft.notification.notification_no,
                    defaults={
                        "title": draft.notification.title,
                        "gazette_url": draft.notification.gazette_url,
                        "published_date": draft.notification.published_date,
                    },
                )
            else:
                source = RuleSource.objects.first() or RuleSource.objects.create(
                    notification_no="G.S.R. PUBLISHED-DIRECT",
                    title="Direct National Admin Regulatory Update",
                    published_date=date.today(),
                )

            # 2. Create the live versioned Rule
            live_rule = Rule.objects.create(
                rule_id_code=draft.rule_id_code,
                section_ref=draft.section_ref,
                category=draft.category,
                condition=draft.proposed_condition,
                effective_from=effective_date,
                effective_to=None,
                status="in_force",
                source=source,
            )

            # 3. If replacing an older rule, link supersedes and update old rule's effective_to
            if draft.supersedes_rule:
                old_rule = draft.supersedes_rule
                old_rule.superseded_by = live_rule
                old_rule.effective_to = effective_date
                old_rule.status = "repealed"
                old_rule.save(update_fields=["superseded_by", "effective_to", "status"])

            # 4. Mark draft and notification published
            draft.status = "published"
            draft.effective_date = effective_date
            comments = list(draft.comments)
            comments.append({
                "admin": request.user.username,
                "action": "published",
                "comment": f"Rule published live to repository with effective date {effective_date}.",
                "timestamp": timezone.now().isoformat(),
            })
            draft.comments = comments
            draft.save()

            if draft.notification:
                draft.notification.status = "published"
                draft.notification.save(update_fields=["status"])

            # 5. Write audit log
            AuditLog.objects.create(
                user=request.user,
                action="publish_rule",
                target_type="Rule",
                target_id=str(live_rule.id),
                metadata={
                    "rule_id_code": live_rule.rule_id_code,
                    "effective_from": str(live_rule.effective_from),
                    "superseded_rule_id": draft.supersedes_rule_id,
                },
            )

        return Response(RuleSerializer(live_rule).data, status=status.HTTP_201_CREATED)


class RuleRepositoryListView(generics.ListAPIView):
    """
    GET /api/rules/
    Filterable live rules repository: status, category, effective_from range, search.
    Paginated per DRF standard.
    """
    permission_classes = [permissions.IsAuthenticated, IsOfficerOrController]
    serializer_class = RuleSerializer
    queryset = Rule.objects.all().select_related("source", "superseded_by").order_by("rule_id_code")
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["status", "category", "effective_from", "source"]
    search_fields = ["rule_id_code", "section_ref", "category", "source__title", "source__notification_no"]
    ordering_fields = ["rule_id_code", "effective_from", "category", "status"]


class AdminDashboardSummaryView(APIView):
    """
    GET /api/rules/admin-dashboard/
    Also available at /api/admin/dashboard/summary/
    Aggregated violations by region, category, officer performance, and KPIs.
    """
    permission_classes = [permissions.IsAuthenticated, IsNationalAdmin]

    def get(self, request, *args, **kwargs):
        summary = get_admin_dashboard_summary()
        return Response(summary, status=status.HTTP_200_OK)


class InspectionWeightConfigView(APIView):
    """
    GET /api/rules/inspection-weights/
    POST /api/rules/inspection-weights/
    Adjusts dynamic risk prioritization weights for inspection targets.
    """
    permission_classes = [permissions.IsAuthenticated, IsNationalAdmin]

    def get(self, request, *args, **kwargs):
        config = get_or_create_inspection_weights()
        return Response(InspectionWeightConfigSerializer(config).data, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        config = get_or_create_inspection_weights()
        serializer = InspectionWeightConfigSerializer(config, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        updated = serializer.save(updated_by=request.user)

        AuditLog.objects.create(
            user=request.user,
            action="update_inspection_weights",
            target_type="InspectionWeightConfig",
            target_id=str(updated.id),
            metadata=serializer.validated_data,
        )

        return Response(InspectionWeightConfigSerializer(updated).data, status=status.HTTP_200_OK)
