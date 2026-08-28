"""
Automated unit tests for Phase 4.3: Rule Engine Admin Console.
Tests all Admin Flow steps A–I:
1. Notification ingestion & listing (GET /api/rules/incoming-notifications/)
2. AI draft generation from notification (POST /api/rules/draft/)
3. Admin draft review detail (GET /api/rules/{id}/)
4. Admin draft approval (POST /api/rules/{id}/approve/)
5. In-place draft revision without duplicate rows (POST /api/rules/{id}/revise/)
6. Read-only sandbox simulation without writing to Rule/History (POST /api/rules/{id}/simulate/)
7. Rule publication with versioning and superseding (POST /api/rules/{id}/publish/)
8. Rule repository list with status/category/date filtering & pagination (GET /api/rules/)
9. Admin enforcement dashboard summary analytics (GET /api/rules/admin-dashboard/)
10. Dynamic inspection priority weight configuration (GET/POST /api/rules/inspection-weights/)
11. Permission boundaries: 403 Forbidden for non-admins (citizen, officer) on all write endpoints.
"""
from datetime import date, timedelta
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

from apps.accounts.models import Role, RoleAssignment
from apps.product_master.models import Product
from apps.scans.models import Scan
from apps.compliance.models import ComplianceCheck, Violation, ProductComplianceHistory
from apps.cases.models import Case
from apps.complaints.models import Complaint
from apps.inspections.models import InspectionTarget
from apps.rules_engine.models import (
    RuleSource,
    Rule,
    RuleNotification,
    RuleDraft,
    RuleSimulationResult,
    InspectionWeightConfig,
)

User = get_user_model()


class RuleEngineAdminConsoleTests(TestCase):
    def setUp(self):
        self.client = APIClient()

        # 1. Create Roles
        self.admin_role, _ = Role.objects.get_or_create(name="national_admin")
        self.rule_admin_role, _ = Role.objects.get_or_create(name="rule_admin")
        self.officer_role, _ = Role.objects.get_or_create(name="field_officer")
        self.citizen_role, _ = Role.objects.get_or_create(name="citizen")

        # 2. Create Users
        self.admin_user = User.objects.create_user(
            username="admin_tester",
            password="testpassword123",
            email="admin@doca.gov.in",
            first_name="National",
            last_name="Admin",
        )
        RoleAssignment.objects.create(user=self.admin_user, role=self.admin_role)

        self.officer_user = User.objects.create_user(
            username="officer_tester",
            password="testpassword123",
            email="officer@delhi.gov.in",
            first_name="Field",
            last_name="Officer",
        )
        RoleAssignment.objects.create(user=self.officer_user, role=self.officer_role, state="DL")

        self.citizen_user = User.objects.create_user(
            username="citizen_tester",
            password="testpassword123",
            email="citizen@public.org",
        )
        RoleAssignment.objects.create(user=self.citizen_user, role=self.citizen_role)

        # 3. Seed Rule Source & Base Live Rules
        self.source = RuleSource.objects.create(
            notification_no="G.S.R. 2024-TEST",
            title="Base Legal Metrology Rules",
            published_date=date(2024, 1, 1),
        )
        self.live_rule_font = Rule.objects.create(
            rule_id_code="PCR-BASE-FONT-2024",
            section_ref="PC Rules 2011, Rule 18",
            category="general",
            condition={"type": "font_size_check", "field": "net_quantity", "min_height_mm": 2.0},
            effective_from=date(2024, 1, 1),
            status="in_force",
            source=self.source,
        )
        self.live_rule_mfg = Rule.objects.create(
            rule_id_code="PCR-BASE-MFG-2024",
            section_ref="PC Rules 2011, Rule 6(1)(d)",
            category="food",
            condition={"type": "required_field", "field": "mfg_date"},
            effective_from=date(2024, 1, 1),
            status="in_force",
            source=self.source,
        )

        # 4. Seed Notification for Testing
        self.notification = RuleNotification.objects.create(
            notification_no="G.S.R. 999(E)/2026",
            title="Packaging Numeral Height & Font Standardization Amendment 2026",
            source_text=(
                "In Rule 18, Table II, the minimum height of numeral in declarations shall be 2.5 mm "
                "for packages up to 1000g, and 6.5 mm for packages exceeding 1000g."
            ),
            category="general",
            published_date=date(2026, 3, 1),
            status="new",
        )

    def test_01_incoming_notifications_list(self):
        """Step A: GET /api/rules/incoming-notifications/ returns detected notifications."""
        self.client.force_authenticate(user=self.admin_user)

        response = self.client.get("/api/rules/incoming-notifications/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()

        # Handle both paginated and plain array responses
        results = data.get("results", data) if isinstance(data, dict) else data
        self.assertGreaterEqual(len(results), 1)
        self.assertEqual(results[0]["notification_no"], "G.S.R. 999(E)/2026")
        self.assertEqual(results[0]["status"], "new")

    def test_02_ai_draft_generation_from_notification(self):
        """Step B: POST /api/rules/draft/ generates structured rule draft from notification."""
        self.client.force_authenticate(user=self.admin_user)

        payload = {"notification_id": self.notification.id}
        response = self.client.post("/api/rules/draft/", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = response.json()

        self.assertEqual(data["notification"], self.notification.id)
        self.assertEqual(data["status"], "pending_review")
        self.assertIn("font", data["rule_id_code"].lower())
        self.assertEqual(data["proposed_condition"]["type"], "font_size_check")
        self.assertEqual(data["proposed_condition"]["min_height_mm"], 2.5)

        # Confirm notification marked drafted
        self.notification.refresh_from_db()
        self.assertEqual(self.notification.status, "drafted")

    def test_03_admin_draft_review_detail(self):
        """Step C: GET /api/rules/{id}/ retrieves single draft with old vs new diff."""
        draft = RuleDraft.objects.create(
            notification=self.notification,
            rule_id_code="PCR2026-FONT-TEST",
            section_ref="PC Rules 2011, Rule 18",
            category="general",
            old_clause_text="Min height 2.0 mm",
            new_clause_text="Min height 2.5 mm for <=1000g, 6.5 mm for >1000g",
            proposed_condition={"type": "font_size_check", "min_height_mm": 2.5},
            status="pending_review",
            reviewing_admin=self.admin_user,
        )

        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(f"/api/rules/{draft.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()

        self.assertEqual(data["id"], draft.id)
        self.assertEqual(data["old_clause_text"], "Min height 2.0 mm")
        self.assertEqual(data["new_clause_text"], "Min height 2.5 mm for <=1000g, 6.5 mm for >1000g")
        self.assertEqual(data["status"], "pending_review")

    def test_04_revise_draft_updates_in_place_without_duplicate_rows(self):
        """Step E (Revise): POST /api/rules/{id}/revise/ updates draft in-place without duplicate rows."""
        draft = RuleDraft.objects.create(
            notification=self.notification,
            rule_id_code="PCR2026-FONT-REVISE-TEST",
            section_ref="PC Rules 2011, Rule 18",
            category="general",
            old_clause_text="Min height 2.0 mm",
            new_clause_text="Initial proposal",
            proposed_condition={"type": "font_size_check", "min_height_mm": 2.2},
            status="pending_review",
            reviewing_admin=self.admin_user,
        )

        initial_draft_count = RuleDraft.objects.count()
        initial_notif_count = RuleNotification.objects.count()

        self.client.force_authenticate(user=self.admin_user)
        payload = {
            "new_clause_text": "Updated clause: Min height 2.5 mm explicitly on principal display panel",
            "proposed_condition": {"type": "font_size_check", "min_height_mm": 2.5, "min_height_mm_large_pack": 6.5},
            "category": "food",
            "comment": "Legal counsel requested explicit principal display panel clause and category specification.",
        }

        response = self.client.post(f"/api/rules/{draft.id}/revise/", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()

        # CONFIRMATION: Row counts did NOT change (in-place update, NO duplicates)
        self.assertEqual(RuleDraft.objects.count(), initial_draft_count)
        self.assertEqual(RuleNotification.objects.count(), initial_notif_count)

        # Confirm fields updated
        draft.refresh_from_db()
        self.assertEqual(draft.status, "revised")
        self.assertEqual(draft.category, "food")
        self.assertIn("principal display panel", draft.new_clause_text)
        self.assertEqual(draft.proposed_condition["min_height_mm"], 2.5)
        self.assertGreaterEqual(len(draft.comments), 1)

    def test_05_approve_draft_sets_effective_date(self):
        """Step F (Approve): POST /api/rules/{id}/approve/ marks draft approved with effective_date."""
        draft = RuleDraft.objects.create(
            notification=self.notification,
            rule_id_code="PCR2026-APPROVE-TEST",
            section_ref="PC Rules 2011, Rule 6",
            category="general",
            new_clause_text="Approved new standard",
            status="pending_review",
        )

        self.client.force_authenticate(user=self.admin_user)
        target_date = date.today() + timedelta(days=60)
        payload = {
            "effective_date": str(target_date),
            "comment": "Final administrative sign-off by National Admin.",
        }

        response = self.client.post(f"/api/rules/{draft.id}/approve/", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        draft.refresh_from_db()
        self.assertEqual(draft.status, "approved")
        self.assertEqual(draft.effective_date, target_date)
        self.assertEqual(draft.reviewing_admin, self.admin_user)

    def test_06_simulate_draft_is_strictly_read_only(self):
        """Step H6–H7: POST /api/rules/{id}/simulate/ writes ONLY to RuleSimulationResult."""
        draft = RuleDraft.objects.create(
            notification=self.notification,
            rule_id_code="PCR2026-SIM-TEST",
            section_ref="PC Rules 2011, Rule 18",
            category="general",
            proposed_condition={"type": "font_size_check", "field": "net_quantity", "min_height_mm": 2.5},
            status="pending_review",
        )

        initial_rules_count = Rule.objects.count()
        initial_history_count = ProductComplianceHistory.objects.count()
        initial_checks_count = ComplianceCheck.objects.count()
        initial_sim_count = RuleSimulationResult.objects.count()

        self.client.force_authenticate(user=self.admin_user)
        response = self.client.post(f"/api/rules/{draft.id}/simulate/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()

        self.assertEqual(data["draft"], draft.id)
        self.assertIn("before_compliance_rate", data)
        self.assertIn("after_compliance_rate", data)

        # STRICT ASSERTION: Rule, ProductComplianceHistory, and ComplianceCheck counts MUST BE UNCHANGED
        self.assertEqual(Rule.objects.count(), initial_rules_count)
        self.assertEqual(ProductComplianceHistory.objects.count(), initial_history_count)
        self.assertEqual(ComplianceCheck.objects.count(), initial_checks_count)

        # Confirm exactly one simulation result record created
        self.assertEqual(RuleSimulationResult.objects.count(), initial_sim_count + 1)

    def test_07_publish_creates_versioned_rule_without_mutating_history(self):
        """Step G: POST /api/rules/{id}/publish/ activates new Rule and supersedes prior version."""
        draft = RuleDraft.objects.create(
            notification=self.notification,
            rule_id_code="PCR2026-FONT-V2",
            section_ref="PC Rules 2011, Rule 18 (Amended 2026)",
            category="general",
            proposed_condition={"type": "font_size_check", "field": "net_quantity", "min_height_mm": 2.5},
            effective_date=date(2026, 4, 1),
            supersedes_rule=self.live_rule_font,
            status="approved",
        )

        initial_rules_count = Rule.objects.count()
        initial_history_count = ProductComplianceHistory.objects.count()

        self.client.force_authenticate(user=self.admin_user)
        response = self.client.post(f"/api/rules/{draft.id}/publish/", format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = response.json()

        # Confirm new live Rule created
        self.assertEqual(Rule.objects.count(), initial_rules_count + 1)
        self.assertEqual(data["rule_id_code"], "PCR2026-FONT-V2")
        self.assertEqual(data["status"], "in_force")
        self.assertEqual(data["effective_from"], "2026-04-01")

        # Confirm prior version was superseded and archived, NOT deleted or mutated
        self.live_rule_font.refresh_from_db()
        self.assertEqual(self.live_rule_font.status, "repealed")
        self.assertEqual(self.live_rule_font.effective_to, date(2026, 4, 1))
        self.assertEqual(self.live_rule_font.superseded_by_id, data["id"])

        # Confirm historical violation records intact
        self.assertEqual(ProductComplianceHistory.objects.count(), initial_history_count)

        # Confirm draft marked published
        draft.refresh_from_db()
        self.assertEqual(draft.status, "published")

    def test_08_rule_repository_filtering_and_pagination(self):
        """Live Repository: GET /api/rules/ supports category, status, search filtering & pagination."""
        self.client.force_authenticate(user=self.admin_user)

        # Filter by category
        resp_food = self.client.get("/api/rules/?category=food")
        self.assertEqual(resp_food.status_code, status.HTTP_200_OK)
        data_food = resp_food.json()
        results_food = data_food.get("results", data_food) if isinstance(data_food, dict) else data_food
        self.assertTrue(all(r["category"] == "food" for r in results_food))

        # Filter by status
        resp_in_force = self.client.get("/api/rules/?status=in_force")
        self.assertEqual(resp_in_force.status_code, status.HTTP_200_OK)
        data_in_force = resp_in_force.json()
        results_in_force = data_in_force.get("results", data_in_force) if isinstance(data_in_force, dict) else data_in_force
        self.assertTrue(all(r["status"] == "in_force" for r in results_in_force))

        # Search by keyword
        resp_search = self.client.get("/api/rules/?search=MFG")
        self.assertEqual(resp_search.status_code, status.HTTP_200_OK)
        data_search = resp_search.json()
        results_search = data_search.get("results", data_search) if isinstance(data_search, dict) else data_search
        self.assertTrue(any("MFG" in r["rule_id_code"] for r in results_search))

    def test_09_admin_dashboard_summary_kpis(self):
        """Step H: GET /api/rules/admin-dashboard/ returns aggregate regional & category statistics."""
        self.client.force_authenticate(user=self.admin_user)

        response = self.client.get("/api/rules/admin-dashboard/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()

        self.assertIn("kpis", data)
        self.assertIn("violations_by_category", data)
        self.assertIn("violations_by_region", data)
        self.assertIn("officer_performance", data)
        self.assertGreaterEqual(data["kpis"]["total_active_rules"], 1)

    def test_10_inspection_priority_weights_get_and_post(self):
        """Step I: GET and POST /api/rules/inspection-weights/ adjusts risk scoring parameters."""
        self.client.force_authenticate(user=self.admin_user)

        # GET
        get_resp = self.client.get("/api/rules/inspection-weights/")
        self.assertEqual(get_resp.status_code, status.HTTP_200_OK)
        get_data = get_resp.json()
        self.assertIn("risk_engine_weight", get_data)

        # POST Update
        payload = {
            "risk_engine_weight": 0.45,
            "complaint_weight": 0.35,
            "ecommerce_weight": 0.20,
            "repeat_offense_multiplier": 2.0,
        }
        post_resp = self.client.post("/api/rules/inspection-weights/", payload, format="json")
        self.assertEqual(post_resp.status_code, status.HTTP_200_OK)
        post_data = post_resp.json()

        self.assertEqual(post_data["risk_engine_weight"], 0.45)
        self.assertEqual(post_data["complaint_weight"], 0.35)
        self.assertEqual(post_data["repeat_offense_multiplier"], 2.0)

    def test_11_non_admin_gets_403_on_all_write_endpoints(self):
        """Permission Boundary: Citizen & Field Officer receive 403 Forbidden on all write endpoints."""
        draft = RuleDraft.objects.create(
            notification=self.notification,
            rule_id_code="PCR2026-PERM-TEST",
            section_ref="PC Rules 2011",
            category="general",
            status="pending_review",
        )

        for user in [self.officer_user, self.citizen_user]:
            self.client.force_authenticate(user=user)

            # 1. Draft create write
            r1 = self.client.post("/api/rules/draft/", {"notification_id": self.notification.id}, format="json")
            self.assertEqual(r1.status_code, status.HTTP_403_FORBIDDEN)

            # 2. Draft approve write
            r2 = self.client.post(f"/api/rules/{draft.id}/approve/", {"effective_date": "2026-06-01"}, format="json")
            self.assertEqual(r2.status_code, status.HTTP_403_FORBIDDEN)

            # 3. Draft revise write
            r3 = self.client.post(f"/api/rules/{draft.id}/revise/", {"new_clause_text": "Hacked"}, format="json")
            self.assertEqual(r3.status_code, status.HTTP_403_FORBIDDEN)

            # 4. Draft simulate write
            r4 = self.client.post(f"/api/rules/{draft.id}/simulate/")
            self.assertEqual(r4.status_code, status.HTTP_403_FORBIDDEN)

            # 5. Draft publish write
            r5 = self.client.post(f"/api/rules/{draft.id}/publish/", format="json")
            self.assertEqual(r5.status_code, status.HTTP_403_FORBIDDEN)

            # 6. Inspection weights update write
            r6 = self.client.post("/api/rules/inspection-weights/", {"risk_engine_weight": 0.9}, format="json")
            self.assertEqual(r6.status_code, status.HTTP_403_FORBIDDEN)
