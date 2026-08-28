"""
AI Rule Draft Generator (Step B).
Generates structured old vs. new clause diffs and formal JSON condition schemas
from raw legal notification / amendment texts.
"""
import re
from datetime import date
from typing import Dict, Any, Optional
from .models import RuleNotification, Rule


def generate_rule_draft_from_notification(notification: RuleNotification) -> Dict[str, Any]:
    """
    Analyzes notification text and generates a structured draft rule.
    Deterministic and rule-aware.
    """
    text = (notification.source_text + " " + notification.title).lower()
    cat = notification.category or "general"

    # Default fallback values
    rule_id_code = f"PCR2026-AMEND-{notification.notification_no.replace(' ', '-').replace('/', '-')[:20].upper()}"
    section_ref = "Legal Metrology (Packaged Commodities) Rules, 2011 (Amended 2026)"
    old_clause_text = "Rule 6(1): General declarations on packaged commodities."
    new_clause_text = notification.source_text
    proposed_condition = {"type": "required_field", "field": "mfg_date", "exemptions": []}
    supersedes_rule_id = None

    # Pattern 1: Font Size / Numeral Height Amendment
    if "font" in text or "height" in text or "numeral" in text or "minimum size" in text:
        rule_id_code = f"PCR2026-FONT-AMEND-{cat.upper()}"
        section_ref = "PC (Amendment) Rules 2026, Rule 18 & Table II"
        old_clause_text = "The minimum height of numeral in declarations shall be 2.0 mm for packs up to 1000g."
        new_clause_text = (
            "The minimum height of numerals for net quantity and MRP shall be 2.5 mm for packs up to 1000g, "
            "and 6.5 mm for packages exceeding 1000g."
        )
        proposed_condition = {
            "type": "font_size_check",
            "field": "net_quantity",
            "min_height_mm": 2.5,
            "min_height_mm_large_pack": 6.5,
            "pack_size_threshold_g": 1000,
        }
        existing = Rule.objects.filter(rule_id_code__icontains="FONTSIZE", status="in_force").first()
        if existing:
            supersedes_rule_id = existing.id

    # Pattern 2: Unit Sale Price / Dual MRP
    elif "unit sale price" in text or "unit price" in text or "per gram" in text or "per ml" in text:
        rule_id_code = f"PCR2026-UNITPRICE-{cat.upper()}"
        section_ref = "PC (Amendment) Rules 2026, Rule 6(1)(e)"
        old_clause_text = "Unit sale price is recommended but not mandatory for smaller fractional packaging."
        new_clause_text = "Unit sale price shall be mandatory on all pre-packaged commodities irrespective of package size."
        proposed_condition = {
            "type": "required_field",
            "field": "unit_sale_price",
            "exemptions": [],
        }
        existing = Rule.objects.filter(rule_id_code__icontains="UNITMRP", status="in_force").first()
        if existing:
            supersedes_rule_id = existing.id

    # Pattern 3: QR Code / Digital Declarations / E-commerce
    elif "qr" in text or "digital" in text or "url" in text or "e-commerce" in text or "website" in text:
        rule_id_code = f"PCR2026-DIGITAL-QR-{cat.upper()}"
        section_ref = "PC (Packaged Commodities) Amendment Rules 2026, Rule 6(11)"
        old_clause_text = "Physical declarations on principal display panel are mandatory in full printed text."
        new_clause_text = (
            "Manufacturers may supplement physical declarations with a scannable QR Code leading directly "
            "to verified National Legal Metrology product record."
        )
        proposed_condition = {
            "type": "required_field",
            "field": "qr_code_declaration",
            "exemptions": ["bulk_industrial_packages"],
        }

    # Pattern 4: Country of Origin (Imported Goods / E-commerce filter)
    elif "country of origin" in text or "coo" in text or "imported" in text or "import" in text:
        rule_id_code = "PCR2026-COO-EXPANDED"
        section_ref = "PC (Amendment) Rules 2026, Rule 6(10) & Rule 6(1)(a)"
        old_clause_text = "Country of origin required only on packages imported directly from foreign origins."
        new_clause_text = (
            "Country of Origin must be explicitly declared on both physical product packaging and digital listing "
            "prominently on the declaration panel."
        )
        proposed_condition = {
            "type": "conditional_required_field",
            "field": "country_of_origin",
            "applies_if": {"category": "import"},
        }
        existing = Rule.objects.filter(rule_id_code__icontains="COO", status="in_force").first()
        if existing:
            supersedes_rule_id = existing.id

    # Pattern 5: Manufacturing / Expiry Date format
    elif "mfg" in text or "expiry" in text or "best before" in text or "date" in text:
        rule_id_code = f"PCR2026-DATEFMT-{cat.upper()}"
        section_ref = "PC (Amendment) Rules 2026, Rule 6(1)(d)"
        old_clause_text = "Month and year of manufacture or packing shall be declared in standard MM/YYYY format."
        new_clause_text = (
            "Month and Year of manufacture or packing must be declared in words and numerals (e.g. March 2026 or 03/2026) "
            "with minimum font height 2.0 mm."
        )
        proposed_condition = {
            "type": "format_check",
            "field": "mfg_date",
            "format": "month_year",
        }
        existing = Rule.objects.filter(rule_id_code__icontains="MFGDATE-V2", status="in_force").first()
        if existing:
            supersedes_rule_id = existing.id

    return {
        "rule_id_code": rule_id_code,
        "section_ref": section_ref,
        "category": cat,
        "old_clause_text": old_clause_text,
        "new_clause_text": new_clause_text,
        "proposed_condition": proposed_condition,
        "supersedes_rule_id": supersedes_rule_id,
    }
