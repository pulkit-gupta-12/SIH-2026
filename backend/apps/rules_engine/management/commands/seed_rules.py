"""
Management command: seed_rules
Loads seed_rules.json into rules_engine models (RuleSource, Rule).
Supports two-pass loading for superseded_by self-referencing foreign keys.
"""
import json
from pathlib import Path
from django.core.management.base import BaseCommand
from django.db import transaction
from apps.rules_engine.models import RuleSource, Rule


class Command(BaseCommand):
    help = "Loads legal metrology rules from seed_rules.json fixture into RuleSource and Rule models."

    def handle(self, *args, **options):
        fixture_path = Path(__file__).resolve().parent.parent.parent / "fixtures" / "seed_rules.json"

        if not fixture_path.exists():
            self.stderr.write(self.style.ERROR(f"Fixture not found at {fixture_path}"))
            return

        with open(fixture_path, "r", encoding="utf-8") as f:
            rules_data = json.load(f)

        self.stdout.write(f"Loading {len(rules_data)} rules from {fixture_path.name}...")

        with transaction.atomic():
            # Pass 1: Create or update RuleSources and Rules (without superseded_by links)
            created_sources = 0
            created_rules = 0
            updated_rules = 0
            supersede_map = {}

            for item in rules_data:
                source_data = item.get("source", {})
                notification_no = source_data.get("notification_no", "UNKNOWN")

                source, s_created = RuleSource.objects.get_or_create(
                    notification_no=notification_no,
                    defaults={
                        "title": source_data.get("title", ""),
                        "gazette_url": source_data.get("gazette_url", ""),
                        "published_date": source_data.get("published_date", "2011-01-01"),
                    },
                )
                if s_created:
                    created_sources += 1

                rule_id_code = item["rule_id_code"]
                superseded_code = item.get("superseded_by")
                if superseded_code:
                    supersede_map[rule_id_code] = superseded_code

                rule, r_created = Rule.objects.update_or_create(
                    rule_id_code=rule_id_code,
                    defaults={
                        "section_ref": item["section_ref"],
                        "category": item["category"],
                        "condition": item["condition"],
                        "effective_from": item["effective_from"],
                        "effective_to": item.get("effective_to"),
                        "status": item.get("status", "draft"),
                        "source": source,
                    },
                )

                if r_created:
                    created_rules += 1
                else:
                    updated_rules += 1

            # Pass 2: Link superseded_by relationships
            linked_supersedes = 0
            for rule_code, super_code in supersede_map.items():
                try:
                    rule = Rule.objects.get(rule_id_code=rule_code)
                    superseding_rule = Rule.objects.get(rule_id_code=super_code)
                    rule.superseded_by = superseding_rule
                    rule.save(update_fields=["superseded_by"])
                    linked_supersedes += 1
                except Rule.DoesNotExist:
                    self.stderr.write(
                        self.style.WARNING(
                            f"Warning: Superseding rule '{super_code}' not found for '{rule_code}'"
                        )
                    )

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully processed rules:\n"
                f"  - Rule Sources created: {created_sources}\n"
                f"  - Rules created: {created_rules}\n"
                f"  - Rules updated: {updated_rules}\n"
                f"  - Supersede relationships linked: {linked_supersedes}\n"
                f"  - Total Rules in DB: {Rule.objects.count()}"
            )
        )
