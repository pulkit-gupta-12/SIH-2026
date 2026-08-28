"""
Rules Engine models: RuleSource, Rule, RuleNotification, RuleDraft, RuleSimulationResult, InspectionWeightConfig.
Matches schema from 05_Database_Schema.md and Phase 4.3 Rule Engine Admin Console specifications.
"""
from datetime import date
from django.conf import settings
from django.db import models


class RuleSource(models.Model):
    """
    Rule Sources table.
    Fields: id, notification_no, title, gazette_url, published_date.
    """
    notification_no = models.CharField(max_length=100)
    title = models.CharField(max_length=500)
    gazette_url = models.CharField(max_length=500, blank=True, null=True)
    published_date = models.DateField()

    class Meta:
        db_table = "rule_sources"
        ordering = ["-published_date"]

    def __str__(self):
        return f"{self.notification_no}: {self.title[:50]}"


class Rule(models.Model):
    """
    Rules table (versioned live rules repository).
    Fields: id, rule_id_code (unique), section_ref, category, condition (JSONB),
    effective_from, effective_to (nullable), superseded_by_id (FK rules, nullable),
    status (draft/in_force/repealed), source_id (FK rule_sources).
    """
    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("in_force", "In Force"),
        ("repealed", "Repealed"),
    ]

    rule_id_code = models.CharField(max_length=100, unique=True, db_index=True)
    section_ref = models.CharField(max_length=255)
    category = models.CharField(max_length=50, db_index=True)
    condition = models.JSONField(default=dict)
    effective_from = models.DateField()
    effective_to = models.DateField(blank=True, null=True)
    superseded_by = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="supersedes",
    )
    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default="draft",
        db_index=True,
    )
    source = models.ForeignKey(
        RuleSource,
        on_delete=models.CASCADE,
        related_name="rules",
    )

    class Meta:
        db_table = "rules"
        ordering = ["rule_id_code"]

    def __str__(self):
        return f"{self.rule_id_code} ({self.section_ref}) [{self.status}]"


class RuleNotification(models.Model):
    """
    Detected/Seeded legal amendment notifications from e-Gazette / Ministry of Consumer Affairs.
    Feeds step A of the Admin workflow.
    """
    STATUS_CHOICES = [
        ("new", "New"),
        ("drafted", "Drafted"),
        ("approved", "Approved"),
        ("published", "Published"),
    ]

    notification_no = models.CharField(max_length=100, unique=True, db_index=True)
    title = models.CharField(max_length=500)
    source_text = models.TextField(help_text="Full text of notification or amendment clause")
    gazette_url = models.CharField(max_length=500, blank=True, null=True)
    published_date = models.DateField(default=date.today)
    date_detected = models.DateTimeField(auto_now_add=True)
    category = models.CharField(max_length=50, default="general", db_index=True)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default="new", db_index=True)

    class Meta:
        db_table = "rule_notifications"
        ordering = ["-date_detected"]

    def __str__(self):
        return f"{self.notification_no}: {self.title[:40]} [{self.status}]"


class RuleDraft(models.Model):
    """
    AI-generated / Admin-reviewed structured draft rule before publication.
    Feeds steps B, C, D, E, F of the Admin workflow.
    """
    STATUS_CHOICES = [
        ("pending_review", "Pending Review"),
        ("revised", "Revised"),
        ("approved", "Approved"),
        ("published", "Published"),
    ]

    notification = models.ForeignKey(
        RuleNotification,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="drafts",
    )
    rule_id_code = models.CharField(max_length=100, db_index=True)
    section_ref = models.CharField(max_length=255)
    category = models.CharField(max_length=50, default="general", db_index=True)
    old_clause_text = models.TextField(blank=True, default="", help_text="Current in-force legal clause")
    new_clause_text = models.TextField(help_text="Proposed amendment clause text")
    proposed_condition = models.JSONField(
        default=dict,
        help_text="JSON condition schema (required_field, format_check, font_size_check, etc.)"
    )
    effective_date = models.DateField(null=True, blank=True, help_text="Planned effective date set upon approval")
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default="pending_review", db_index=True)
    comments = models.JSONField(default=list, help_text="Audit log of review comments and revision history")
    reviewing_admin = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_rule_drafts",
    )
    supersedes_rule = models.ForeignKey(
        Rule,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="superseded_by_drafts",
        help_text="Existing live rule to be superseded when published"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "rule_drafts"
        ordering = ["-updated_at"]

    def __str__(self):
        return f"Draft {self.rule_id_code} [{self.status}]"


class RuleSimulationResult(models.Model):
    """
    Read-only sandbox simulation metrics run against historical scans.
    Feeds step H6–H7 of the Admin workflow.
    """
    draft = models.ForeignKey(
        RuleDraft,
        on_delete=models.CASCADE,
        related_name="simulation_results",
    )
    total_scans_evaluated = models.IntegerField(default=0)
    before_compliance_rate = models.FloatField(default=0.0, help_text="Percentage (0-100)")
    after_compliance_rate = models.FloatField(default=0.0, help_text="Percentage (0-100)")
    projected_violation_diff = models.IntegerField(default=0, help_text="Estimated change in violation count")
    metrics = models.JSONField(default=dict, help_text="Detailed category breakdown and impact analytics")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "rule_simulation_results"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Sim #{self.id} for Draft #{self.draft_id}: {self.before_compliance_rate:.1f}% -> {self.after_compliance_rate:.1f}%"


class InspectionWeightConfig(models.Model):
    """
    Configurable weights and risk parameters for the National Admin (Step I).
    Feeds the dynamic risk scoring engine for InspectionTargets.
    """
    risk_engine_weight = models.FloatField(default=0.50)
    complaint_weight = models.FloatField(default=0.30)
    ecommerce_weight = models.FloatField(default=0.20)
    repeat_offense_multiplier = models.FloatField(default=1.50)
    category_multipliers = models.JSONField(
        default=dict,
        help_text="Category-specific risk multipliers e.g. {'food': 1.2, 'medical_device': 1.4}"
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="updated_inspection_configs"
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "inspection_weight_configs"

    def __str__(self):
        return f"InspectionWeightConfig (Risk={self.risk_engine_weight}, Complaint={self.complaint_weight}, Ecom={self.ecommerce_weight})"
