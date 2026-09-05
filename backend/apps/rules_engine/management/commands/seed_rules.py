"""
Management command: seed_rules
Loads rules strictly from 2011_rules.json and 2026_rules.json into rules_engine models (RuleSource, Rule).
Does NOT use seed_rules.json.
Supports two-pass loading for superseded_by self-referencing foreign keys.
"""
import json
from pathlib import Path
from django.core.management.base import BaseCommand
from django.db import transaction
from apps.rules_engine.models import RuleSource, Rule


class Command(BaseCommand):
    help = "Loads legal metrology rules strictly from 2011_rules.json and 2026_rules.json into RuleSource and Rule models."

    def handle(self, *args, **options):
        rules_dir = Path(__file__).resolve().parent.parent.parent

        path_2011 = rules_dir / "2011_rules.json"
        if not path_2011.exists():
            path_2011 = rules_dir / "2011_rule.json"

        path_2026 = rules_dir / "2026_rules.json"

        if not path_2011.exists():
            self.stderr.write(self.style.ERROR(f"2011 rules file not found at {path_2011}"))
            return

        with open(path_2011, "r", encoding="utf-8") as f:
            rules_2011_data = json.load(f)

        rules_2026_data = []
        if path_2026.exists():
            with open(path_2026, "r", encoding="utf-8") as f:
                rules_2026_data = json.load(f)

        self.stdout.write(
            f"Seeding {len(rules_2011_data)} rules from {path_2011.name} and "
            f"{len(rules_2026_data)} rules from {path_2026.name} (seed_rules.json omitted)..."
        )

        with transaction.atomic():
            created_sources = 0
            created_rules = 0
            updated_rules = 0
            supersede_map = {}

            # 1. Source & Rules for PCR 2011
            source_2011, s11_created = RuleSource.objects.get_or_create(
                notification_no="G.S.R. 202(E)",
                defaults={
                    "title": "The Legal Metrology (Packaged Commodities) Rules, 2011",
                    "gazette_url": "https://consumeraffairs.nic.in",
                    "published_date": "2011-03-07",
                },
            )
            if s11_created:
                created_sources += 1

            for item in rules_2011_data:
                rule_id_code = item["rule_id_code"]
                superseded_code = item.get("superseded_by")
                if superseded_code:
                    supersede_map[rule_id_code] = superseded_code

                status_ver = item.get("status_in_this_source_version", "operative")
                status = "in_force" if status_ver == "operative" else "repealed"

                cat = item.get("category", "general")
                if isinstance(cat, list):
                    cat = cat[0] if cat else "general"

                rule, r_created = Rule.objects.update_or_create(
                    rule_id_code=rule_id_code,
                    defaults={
                        "section_ref": item.get("section_ref", ""),
                        "category": str(cat)[:50],
                        "condition": item.get("condition") or {},
                        "effective_from": item["effective_from"][:10],
                        "effective_to": item["effective_to"][:10] if item.get("effective_to") else None,
                        "status": status,
                        "source": source_2011,
                    },
                )
                if r_created:
                    created_rules += 1
                else:
                    updated_rules += 1

            # 2. Source & Rules for Jan Vishwas Act 2026
            if rules_2026_data:
                source_2026, s26_created = RuleSource.objects.get_or_create(
                    notification_no="Act No. 8 of 2026",
                    defaults={
                        "title": "The Jan Vishwas (Amendment of Provisions) Act, 2026",
                        "gazette_url": "https://www.indiacode.nic.in",
                        "published_date": "2026-05-01",
                    },
                )
                if s26_created:
                    created_sources += 1

                for item in rules_2026_data:
                    rule_id_code = item["rule_id_code"]
                    superseded_code = item.get("superseded_by")
                    if superseded_code:
                        supersede_map[rule_id_code] = superseded_code

                    sec = item.get("section_ref") or item.get("source_section") or ""
                    cat = item.get("category", "general")
                    if isinstance(cat, list):
                        cat = cat[0] if cat else "general"

                    rule, r_created = Rule.objects.update_or_create(
                        rule_id_code=rule_id_code,
                        defaults={
                            "section_ref": sec[:255],
                            "category": str(cat)[:50],
                            "condition": item.get("condition") or {},
                            "effective_from": item.get("effective_from", "2026-05-01")[:10],
                            "effective_to": item["effective_to"][:10] if item.get("effective_to") else None,
                            "status": "in_force",
                            "source": source_2026,
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
                    pass

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully loaded statutory rules (2011 + 2026):\n"
                f"  - Rule Sources created: {created_sources}\n"
                f"  - Rules created: {created_rules}\n"
                f"  - Rules updated: {updated_rules}\n"
                f"  - Supersede relationships linked: {linked_supersedes}\n"
                f"  - Total Rules in DB: {Rule.objects.count()}"
            )
        )
