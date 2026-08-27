"""
Rules Engine models: RuleSource, Rule.
Matches schema from 05_Database_Schema.md and condition structure from 08_Rule_Engine_Dataset_Build_Instructions.md.
"""
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
    Rules table.
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
