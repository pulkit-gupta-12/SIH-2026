"""
Unified Compliance Report Layer for Legal Metrology.

Combines:
1. Normalized OCR / canonical package data
2. Deterministic rule-engine results
3. Semantic LLM results
4. Complete raw OCR evidence
5. Confidence scoring
6. Human-review requirements

Produces a standardized ComplianceReport object.
"""

from datetime import datetime, timezone
import logging
from typing import Any, Dict, List, Optional, Union

logger = logging.getLogger(__name__)

# Standard human-readable titles for common Legal Metrology rules
RULE_TITLES = {
    "PCR2011-R1-TITLE-COMMENCEMENT": "Title & Commencement",
    "PCR2011-R2-DEFINITIONS": "Statutory Definitions & Scope",
    "PCR2011-R2-M-MRP-FORMAT": "MRP Statutory Format & Inclusivity of Taxes",
    "PCR2011-R3-APPLICABILITY": "Package Size & Applicability Scope",
    "PCR2011-R4-GENERAL-PREPACK": "General Pre-packed Commodities Compliance",
    "PCR2011-R5-SECOND-SCHEDULE": "Standard Package Sizes (Schedule II)",
    "PCR2011-R6-1-A-NAME-ADDRESS": "Manufacturer / Packer / Importer Name & Address",
    "PCR2011-R6-1-B-GENERIC-NAME": "Generic / Commodity Name Declaration",
    "PCR2011-R6-1-C-NETQTY": "Net Quantity Declaration Requirement",
    "PCR2011-R6-1-D-MFG-DATE": "Month & Year of Manufacture / Pre-packing",
    "PCR2011-R6-1-DA-EXPIRY-DATE": "Expiry / Best Before Date Declaration",
    "PCR2011-R6-1-DA-BEST-BEFORE": "Best Before Statement Format",
    "PCR2011-R6-1-E-MRP-DECLARATION": "Maximum Retail Price (MRP) Declaration",
    "PCR2011-R6-1-E-USP": "Unit Sale Price (USP) Declaration",
    "PCR2011-R6-1-F-CONSUMER-CARE": "Consumer Care & Grievance Contact Details",
    "PCR2011-R6-1-G-COUNTRY-ORIGIN": "Country of Origin Declaration",
    "PCR2011-R6-1-H-BARCODE": "Barcode / GTIN Code Presence",
    "PCR2011-R6-1-I-FSSAI": "FSSAI License / Food Safety Registration",
    "PCR2011-R7-PDP-DIMENSIONS": "Principal Display Panel (PDP) Dimensions",
    "PCR2011-R8-DECLARATION-PROMINENCE": "Prominence & Legibility of Declarations",
    "PCR2011-R9-FONT-SIZE-NETQTY": "Statutory Font Size for Net Quantity",
    "PCR2011-R10-DECLARATION-LANGUAGE": "Statutory Declaration Language (Hindi/English)",
    "PCR2011-R11-UNIT-SYMBOLS": "Standard Measurement Unit Symbols (g, kg, ml, l)",
    "PCR2011-R12-DECIMAL-NOTATION": "Decimal Quantity Representation",
    "PCR2011-R13-MULTIPLE-UNITS": "Multi-piece / Combo Package Declarations",
    "PCR-DATE-CONSISTENCY": "Statutory Date Consistency (Mfg vs Expiry)",
    "PCR-USP-CALCULATION": "Unit Sale Price Arithmetic Accuracy",
    "PCR-SEM-01": "Semantic Verification of Consumer Care Contact",
    "PCR-SEM-02": "Semantic Verification of Manufacturer Entity",
    "PCR-SEM-03": "Semantic Verification of Commodity Identity",
}

# Standard expected requirements for common Legal Metrology rules
RULE_EXPECTED = {
    "PCR2011-R2-M-MRP-FORMAT": "MRP must be declared as 'Maximum Retail Price ₹...' or 'MRP ₹... incl. of all taxes'.",
    "PCR2011-R6-1-A-NAME-ADDRESS": "Complete name and physical postal address of manufacturer, packer, or importer.",
    "PCR2011-R6-1-B-GENERIC-NAME": "Common or generic name of the commodity must be prominently declared on PDP.",
    "PCR2011-R6-1-C-NETQTY": "Net quantity in standard units of weight, measure, or number (g, kg, ml, l).",
    "PCR2011-R6-1-D-MFG-DATE": "Month and year of manufacture, pre-packing, or import (MM/YYYY format).",
    "PCR2011-R6-1-DA-EXPIRY-DATE": "Expiry date or 'Best Before' statement clearly legible for perishable commodities.",
    "PCR2011-R6-1-E-MRP-DECLARATION": "Maximum Retail Price (MRP) clearly stated inclusive of all statutory taxes.",
    "PCR2011-R6-1-E-USP": "Unit Sale Price (e.g. ₹/g, ₹/kg, ₹/ml, ₹/unit) mandatory for packages > 1kg/1L or multi-packs.",
    "PCR2011-R6-1-F-CONSUMER-CARE": "Name, phone, and/or email of person/office to contact for consumer grievances.",
    "PCR2011-R6-1-G-COUNTRY-ORIGIN": "Country of origin clearly stated (mandatory for imported or domestic packages).",
    "PCR2011-R11-UNIT-SYMBOLS": "Statutory SI symbols only (e.g. 'g', 'kg', 'ml', 'l', not 'gms', 'kgs', 'mls').",
    "PCR-DATE-CONSISTENCY": "Expiry or Best Before date must occur on or after the date of manufacture.",
    "PCR-USP-CALCULATION": "Unit Sale Price must equal MRP divided by the declared net quantity.",
}


def _resolve_rule_title(rule_id: str, raw_title: Optional[str] = None) -> str:
    """Returns a clear, standardized human-readable title for a rule."""
    if raw_title and len(raw_title.strip()) > 3:
        return raw_title.strip()
    if rule_id in RULE_TITLES:
        return RULE_TITLES[rule_id]
    clean_id = rule_id.replace("PCR2011-", "").replace("PCR-", "").replace("-", " ")
    return clean_id.title()


def _resolve_expected_requirement(
    rule_id: str,
    condition: Optional[Dict[str, Any]] = None,
    default_expected: Optional[str] = None,
) -> str:
    """Returns statutory expected requirement description."""
    if default_expected:
        return default_expected
    if rule_id in RULE_EXPECTED:
        return RULE_EXPECTED[rule_id]
    if condition and isinstance(condition, dict):
        cond_type = condition.get("type", "")
        field = condition.get("field", "")
        if cond_type == "required_field":
            return f"Mandatory declaration of '{field}' must be prominently displayed on package."
        if cond_type == "format_check":
            fmt = condition.get("format", "")
            return f"Must strictly adhere to statutory format: {fmt}."
        if cond_type == "numeric_check":
            return f"Value for '{field}' must satisfy legal numerical bounds."
    return "Mandatory compliance requirement under Legal Metrology (Packaged Commodities) Rules, 2011."


def _resolve_source_panel(
    field_key: Optional[str],
    evidence_dict: Dict[str, Any],
    canonical_package: Dict[str, Any],
) -> str:
    """Resolves which capture panel the evidence originated from."""
    if evidence_dict.get("source_panel"):
        return str(evidence_dict["source_panel"])

    if field_key and field_key in canonical_package:
        f_data = canonical_package.get(field_key, {})
        if isinstance(f_data, dict) and f_data.get("source_panel"):
            return str(f_data["source_panel"])

    if field_key in ["commodity_name", "brand_name"]:
        return "front_pdp"
    if field_key in ["mrp", "net_quantity", "mfg_date", "expiry_date", "manufacturer_address"]:
        return "mandatory_declaration"

    return "unspecified"


def _format_detected_value(evidence_dict: Dict[str, Any]) -> str:
    """Formats detected value cleanly for reporting."""
    raw_val = evidence_dict.get("raw_text") or evidence_dict.get("raw_value")
    if raw_val is not None:
        return str(raw_val)

    norm_val = evidence_dict.get("normalized_value")
    if norm_val is not None:
        if isinstance(norm_val, dict):
            if "amount" in norm_val and "currency" in norm_val:
                return f"{norm_val.get('currency', '₹')} {norm_val.get('amount')}"
            if "quantity" in norm_val and "unit" in norm_val:
                return f"{norm_val.get('quantity')} {norm_val.get('unit')}"
            if "date_iso" in norm_val:
                return str(norm_val.get("date_iso"))
            if "name" in norm_val:
                return str(norm_val.get("name"))
        return str(norm_val)

    return "Not Detected"


def _build_rule_finding(
    raw_result: Dict[str, Any],
    canonical_package: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Transforms an internal rule evaluation result into a standardized
    finding item containing rule ID, section ref, title, severity, detected value,
    expected requirement, reason, structured evidence, source panel, confidence,
    and human review requirement.
    """
    rule_id = raw_result.get("rule_id", "UNKNOWN_RULE")
    status = raw_result.get("status", "REVIEW")
    severity = raw_result.get("severity", "MEDIUM")
    confidence = float(raw_result.get("confidence", 0.90))
    requires_human_review = bool(raw_result.get("requires_human_review", False))
    eval_source = raw_result.get("evaluation_source", "deterministic")

    # Resolve evidence details
    raw_ev = raw_result.get("evidence", {})
    field_key = raw_ev.get("field") if isinstance(raw_ev, dict) else None

    # Resolve panel
    source_panel = _resolve_source_panel(field_key, raw_ev if isinstance(raw_ev, dict) else {}, canonical_package)

    # Resolve raw text & normalized value
    raw_text = None
    norm_value = None
    bbox = None
    if isinstance(raw_ev, dict):
        raw_text = raw_ev.get("raw_text") or raw_ev.get("raw_value")
        norm_value = raw_ev.get("normalized_value")

    # If evidence did not carry raw_text directly, pull from canonical package field
    if not raw_text and field_key and field_key in canonical_package:
        f_entry = canonical_package.get(field_key, {})
        if isinstance(f_entry, dict):
            raw_text = f_entry.get("raw")
            if norm_value is None:
                norm_value = f_entry.get("normalized")
            bbox = f_entry.get("bbox")

    # Format detected value string
    detected_value = raw_result.get("detected_value")
    if not detected_value:
        detected_value = _format_detected_value({
            "raw_text": raw_text,
            "normalized_value": norm_value,
        })

    # Expected requirement
    expected = raw_result.get("expected") or _resolve_expected_requirement(
        rule_id=rule_id,
        condition=raw_result.get("condition"),
    )

    # Title
    title = _resolve_rule_title(rule_id, raw_result.get("title"))

    # Reason
    reason = raw_result.get("reason") or f"Rule evaluation completed with status: {status}."

    # Administrative or definition statutory clauses (e.g. Title, Definitions, Applicability scope)
    # with no testable package condition are classified as NOT_APPLICABLE for package evaluation
    is_admin_clause = (
        (field_key == "general_compliance" or (isinstance(raw_ev, dict) and raw_ev.get("field") == "general_compliance"))
        and severity == "LOW"
        and not raw_result.get("condition")
        and eval_source != "semantic_llm"
        and status == "REVIEW"
    )
    if is_admin_clause:
        status = "NOT_APPLICABLE"
        reason = f"Administrative or definition statutory clause ({raw_result.get('section_ref', '')}) - not a direct package test condition."
        requires_human_review = False

    # Package-wide meta rules that refer to language, small-pack exemption, or general declarations
    if rule_id in ["PCR2011-R7-1-SMALLPACK", "PCR2011-R12-7-TAGDECLARATION"]:
        net_qty = canonical_package.get("net_quantity", {}).get("normalized", {})
        qty_val = net_qty.get("quantity") if isinstance(net_qty, dict) else None
        if qty_val and qty_val > 5:
            status = "NOT_APPLICABLE"
            reason = f"Package net quantity ({qty_val} {net_qty.get('unit', '')}) exceeds 5 cubic cm / 5 ml. Small pack exemption is not applicable."
            requires_human_review = False
        elif qty_val is not None:
            status = "PASS"
            reason = "Package capacity conforms to small packaging guidelines."
            requires_human_review = False

    elif rule_id == "PCR2011-R9-4-LANGUAGE":
        raw_ocr = canonical_package.get("raw_text") or ""
        if raw_ocr and any(c.isalnum() for c in raw_ocr):
            status = "PASS"
            reason = "Mandatory declarations are printed in authorized language (English / Hindi)."
            requires_human_review = False

    elif rule_id in ["PCR2011-R8-1-PLACEMENT", "PCR2011-R9-1A-LEGIBILITY", "PCR2011-R9-2-LIQUIDREADABILITY", "PCR2011-R12-5-ADDINFO"]:
        mandatory_keys = ["mrp", "net_quantity", "mfg_date", "manufacturer_address"]
        detected_mandatories = [
            k for k in mandatory_keys
            if canonical_package.get(k, {}).get("detected")
            and float(canonical_package.get(k, {}).get("confidence", 0.0)) >= 0.60
        ]
        if len(detected_mandatories) >= 3:
            status = "PASS"
            reason = "General statutory declarations are clearly placed and legible on the package."
            requires_human_review = False

    # Standard evidence object (never discard raw OCR evidence)
    evidence = {
        "field": field_key,
        "raw_text": raw_text,
        "source_panel": source_panel,
        "normalized_value": norm_value,
    }
    if bbox:
        evidence["bounding_box"] = bbox
    if isinstance(raw_ev, dict) and "matched_snippets" in raw_ev:
        evidence["matched_snippets"] = raw_ev["matched_snippets"]

    return {
        "rule_id": rule_id,
        "section_ref": raw_result.get("section_ref", ""),
        "title": title,
        "status": status,
        "severity": severity,
        "detected_value": detected_value,
        "expected": expected,
        "reason": reason,
        "evidence": evidence,
        "source_panel": source_panel,
        "confidence": round(confidence, 2),
        "requires_human_review": requires_human_review,
        "evaluation_source": eval_source,
    }


def extract_package_evidence(canonical_package: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Collects complete, unabridged package evidence extracted from OCR across panels.
    Ensures raw OCR evidence is never discarded.
    """
    evidence_list: List[Dict[str, Any]] = []

    # Standard canonical fields
    standard_fields = [
        "mrp",
        "net_quantity",
        "unit_sale_price",
        "mfg_date",
        "expiry_date",
        "best_before",
        "manufacturer_name",
        "manufacturer_address",
        "consumer_care_details",
        "country_of_origin",
        "commodity_name",
        "fssai_license_no",
        "batch_number",
        "barcode",
    ]

    for f_key in standard_fields:
        f_data = canonical_package.get(f_key)
        if not f_data or not isinstance(f_data, dict):
            continue

        raw = f_data.get("raw")
        detected = f_data.get("detected", False)
        if detected or raw:
            evidence_list.append({
                "field": f_key,
                "raw_text": raw,
                "normalized_value": f_data.get("normalized"),
                "confidence": round(float(f_data.get("confidence", 0.0)), 2),
                "source_panel": f_data.get("source_panel", "unspecified"),
                "bounding_box": f_data.get("bbox"),
                "detected": detected,
                "normalization_status": f_data.get("normalization_status", "success"),
                "ambiguity": f_data.get("ambiguity"),
            })

    # Add raw text capture stream metadata from root or _meta
    raw_ocr_stream = (
        canonical_package.get("raw_text")
        or canonical_package.get("_meta", {}).get("raw_text")
    )
    if raw_ocr_stream:
        barcode_val = None
        bc_field = canonical_package.get("barcode")
        if isinstance(bc_field, dict):
            barcode_val = bc_field.get("raw")
        elif isinstance(bc_field, str):
            barcode_val = bc_field
        if not barcode_val:
            barcode_val = canonical_package.get("_meta", {}).get("barcode")

        evidence_list.append({
            "field": "_raw_ocr_stream",
            "raw_text": raw_ocr_stream,
            "normalized_value": None,
            "confidence": 1.0,
            "source_panel": "all_panels",
            "detected": True,
            "normalization_status": "raw",
            "barcode": barcode_val,
            "total_fields_extracted": len(evidence_list),
        })

    return evidence_list


def generate_compliance_report(
    canonical_package_data: Dict[str, Any],
    evaluation_results: List[Dict[str, Any]],
    inspection_id: Optional[str] = None,
    scan: Any = None,
) -> Dict[str, Any]:
    """
    Generates a unified, structured ComplianceReport object.

    Status Logic:
    - A confirmed deterministic violation results in FAIL.
    - A high-confidence semantic violation results in FAIL.
    - Uncertain OCR (< 0.60 confidence / ambiguous) produces REVIEW, never auto-fail.
    - Low-confidence LLM results produce REVIEW.
    - Missing critical mandatory declarations where uncaptured produce REVIEW.
    - Warnings do NOT convert automatically into violations.

    Overall Status:
    - 'NON_COMPLIANT' if any rule failed.
    - 'NEEDS_REVIEW' if no failures, but human reviews are required or OCR was uncertain.
    - 'COMPLIANT' if all applicable rules passed and no reviews/failures exist.
    """
    if inspection_id:
        insp_id = inspection_id
    elif scan and hasattr(scan, "id"):
        insp_id = f"INSP-{scan.id}"
    else:
        insp_id = f"INSP-{int(datetime.now(timezone.utc).timestamp())}"

    # Allow evaluation_results to be either a list of results or a dict with {"results": [...]}
    if isinstance(evaluation_results, dict) and "results" in evaluation_results:
        eval_items = evaluation_results["results"]
    elif isinstance(evaluation_results, list):
        eval_items = evaluation_results
    else:
        eval_items = []

    violations: List[Dict[str, Any]] = []
    warnings: List[Dict[str, Any]] = []
    reviews: List[Dict[str, Any]] = []
    passed_rules: List[Dict[str, Any]] = []
    not_applicable_count = 0

    for res in eval_items:
        finding = _build_rule_finding(res, canonical_package_data)
        st = finding["status"]

        if st == "FAIL":
            violations.append(finding)
        elif st == "WARNING":
            warnings.append(finding)
            if finding["requires_human_review"]:
                reviews.append(finding)
        elif st == "REVIEW":
            reviews.append(finding)
        elif st == "PASS":
            passed_rules.append(finding)
        elif st == "NOT_APPLICABLE":
            not_applicable_count += 1
        else:
            reviews.append(finding)

    # Check for critical uncaptured/ambiguous fields in canonical data that mandate review
    critical_mandatories = ["mrp", "net_quantity", "mfg_date", "manufacturer_address"]
    for crit_f in critical_mandatories:
        f_entry = canonical_package_data.get(crit_f, {})
        if isinstance(f_entry, dict):
            if f_entry.get("normalization_status") == "ambiguous" or (
                f_entry.get("detected") and float(f_entry.get("confidence", 1.0)) < 0.60
            ):
                already_flagged = any(
                    r.get("evidence", {}).get("field") == crit_f for r in reviews
                )
                if not already_flagged:
                    crit_finding = {
                        "rule_id": f"LMPC-OCR-UNCERTAIN-{crit_f.upper()}",
                        "section_ref": "Legal Metrology Packaged Commodities Rules, 2011",
                        "title": f"Uncertain OCR for Mandatory Declaration: {crit_f}",
                        "status": "REVIEW",
                        "severity": "MEDIUM",
                        "detected_value": f_entry.get("raw") or "Uncertain",
                        "expected": f"Legible, clear declaration of {crit_f}.",
                        "reason": f"OCR confidence is low ({f_entry.get('confidence')}) or text is ambiguous ({f_entry.get('ambiguity')}). Requires officer verification.",
                        "evidence": {
                            "field": crit_f,
                            "raw_text": f_entry.get("raw"),
                            "source_panel": f_entry.get("source_panel", "mandatory_declaration"),
                            "normalized_value": f_entry.get("normalized"),
                        },
                        "source_panel": f_entry.get("source_panel", "mandatory_declaration"),
                        "confidence": round(float(f_entry.get("confidence", 0.50)), 2),
                        "requires_human_review": True,
                        "evaluation_source": "deterministic",
                    }
                    reviews.append(crit_finding)

    # Compute overall status
    if len(violations) > 0:
        overall_status = "NON_COMPLIANT"
    elif len(reviews) > 0:
        overall_status = "NEEDS_REVIEW"
    else:
        overall_status = "COMPLIANT"

    # Build Summary
    summary = {
        "total_rules": len(eval_items),
        "passed": len(passed_rules),
        "failed": len(violations),
        "warnings": len(warnings),
        "review_required": len(reviews),
        "not_applicable": not_applicable_count,
    }

    # Collect complete package evidence
    evidence = extract_package_evidence(canonical_package_data)

    report = {
        "inspection_id": insp_id,
        "overall_status": overall_status,
        "summary": summary,
        "violations": violations,
        "warnings": warnings,
        "reviews": reviews,
        "passed_rules": passed_rules,
        "evidence": evidence,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }

    return report
