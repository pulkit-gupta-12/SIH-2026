"""
Canonical Normalized Package-Data Representation for Legal Metrology.

This module provides a normalized layer between raw OCR outputs and future
compliance checking (Rules Engine / audit).

Every field in the canonical representation preserves:
1. raw: Exact unparsed string from OCR
2. normalized: Structured data (e.g. amount+currency, quantity+unit, year+month+day)
3. confidence: OCR confidence score (0.0 to 1.0) if available
4. source_panel: Capture panel from which the text was extracted
5. bbox: [x_min, y_min, x_max, y_max] bounding box if available
6. detected: Whether the field was detected in the scan
7. normalization_status: 'success' | 'failed' | 'ambiguous' | 'not_detected'
8. ambiguity: Explanation of any ambiguity, conflicting candidates, or parsing failure
"""

import re
from typing import Any, Dict, List, Optional, Tuple, Union
from pydantic import BaseModel, Field


# =====================================================================
# 1. Pydantic Models for Normalized Values
# =====================================================================

class NormalizedMrp(BaseModel):
    amount: float
    currency: str = "INR"
    inclusive_of_taxes: Optional[bool] = None


class NormalizedQuantity(BaseModel):
    quantity: float
    unit: str


class NormalizedUnitPrice(BaseModel):
    amount: float
    currency: str = "INR"
    unit: str


class NormalizedDate(BaseModel):
    year: int
    month: Optional[int] = None
    day: Optional[int] = None
    date_iso: str  # YYYY-MM-DD or YYYY-MM or YYYY


class NormalizedBestBefore(BaseModel):
    duration_value: Optional[int] = None
    duration_unit: Optional[str] = None  # months, days, years
    raw_statement: Optional[str] = None
    date: Optional[NormalizedDate] = None


class NormalizedFssai(BaseModel):
    license_number: str
    is_valid_format: bool


class NormalizedConsumerCare(BaseModel):
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    website: Optional[str] = None
    raw_statement: Optional[str] = None


class NormalizedCountry(BaseModel):
    country: str
    iso_code: Optional[str] = None


class NormalizedManufacturer(BaseModel):
    name: str


class NormalizedAddress(BaseModel):
    full_address: str
    pin_code: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None


class NormalizedBatch(BaseModel):
    batch_number: str


class NormalizedCommodity(BaseModel):
    commodity_name: str


class NormalizedBarcode(BaseModel):
    barcode: str
    type: Optional[str] = None


# =====================================================================
# 2. Canonical Field Model
# =====================================================================

class CanonicalField(BaseModel):
    raw: Optional[str] = None
    normalized: Optional[Any] = None
    confidence: Optional[float] = None
    source_panel: Optional[str] = None
    bbox: Optional[List[int]] = None
    detected: bool = False
    normalization_status: str = "not_detected"  # success | failed | ambiguous | not_detected
    ambiguity: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        norm_val = self.normalized
        if hasattr(norm_val, "model_dump"):
            norm_val = norm_val.model_dump()
        elif hasattr(norm_val, "dict"):
            norm_val = norm_val.dict()

        return {
            "raw": self.raw,
            "normalized": norm_val,
            "confidence": self.confidence,
            "source_panel": self.source_panel,
            "bbox": self.bbox,
            "detected": self.detected,
            "normalization_status": self.normalization_status,
            "ambiguity": self.ambiguity,
        }


# Default empty canonical field
def empty_canonical_field() -> Dict[str, Any]:
    return {
        "raw": None,
        "normalized": None,
        "confidence": None,
        "source_panel": None,
        "bbox": None,
        "detected": False,
        "normalization_status": "not_detected",
        "ambiguity": None,
    }


# =====================================================================
# 3. Deterministic Normalizers
# =====================================================================

# Month name mapping for date parsing
MONTH_NAMES = {
    "jan": 1, "january": 1,
    "feb": 2, "february": 2,
    "mar": 3, "march": 3,
    "apr": 4, "april": 4,
    "may": 5,
    "jun": 6, "june": 6,
    "jul": 7, "july": 7,
    "aug": 8, "august": 8,
    "sep": 9, "september": 9, "sept": 9,
    "oct": 10, "october": 10,
    "nov": 11, "november": 11,
    "dec": 12, "december": 12,
}

# Standard metric units recognized in Indian Legal Metrology
METRIC_UNITS = {
    "g": "g", "gm": "g", "gms": "g", "gram": "g", "grams": "g",
    "kg": "kg", "kgs": "kg", "kilogram": "kg", "kilograms": "kg",
    "ml": "ml", "m.l.": "ml", "millilitre": "ml", "millilitres": "ml",
    "l": "l", "lt": "l", "ltr": "l", "liter": "l", "liters": "l", "litre": "l", "litres": "l",
    "m": "m", "meter": "m", "meters": "m", "metre": "m", "metres": "m",
    "cm": "cm", "centimeter": "cm", "centimeters": "cm",
    "mm": "mm", "millimeter": "mm", "millimeters": "mm",
    "n": "N", "u": "units", "units": "units", "unit": "units",
    "piece": "pieces", "pieces": "pieces", "pcs": "pieces", "pc": "pieces",
    "pack": "pack", "packs": "pack",
}

# Known country codes for common origins
COUNTRY_ISO_MAP = {
    "india": "IN",
    "japan": "JP",
    "china": "CN",
    "germany": "DE",
    "united states": "US",
    "usa": "US",
    "united kingdom": "GB",
    "uk": "GB",
    "vietnam": "VN",
    "thailand": "TH",
    "taiwan": "TW",
    "south korea": "KR",
    "korea": "KR",
    "france": "FR",
    "italy": "IT",
    "switzerland": "CH",
    "bangladesh": "BD",
    "nepal": "NP",
    "sri lanka": "LK",
    "malaysia": "MY",
    "indonesia": "ID",
}

# Indian State abbreviations/names
INDIAN_STATES = [
    "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh",
    "Goa", "Gujarat", "Haryana", "Himachal Pradesh", "Jharkhand", "Karnataka",
    "Kerala", "Madhya Pradesh", "Maharashtra", "Manipur", "Meghalaya", "Mizoram",
    "Nagaland", "Odisha", "Punjab", "Rajasthan", "Sikkim", "Tamil Nadu",
    "Telangana", "Tripura", "Uttar Pradesh", "Uttarakhand", "West Bengal",
    "Delhi", "Jammu and Kashmir", "Ladakh", "Puducherry", "Chandigarh",
]


def normalize_mrp(raw: str) -> Tuple[Optional[Dict[str, Any]], str, Optional[str]]:
    """
    Normalizes MRP strings.
    Examples:
      - "MRP: Rs.349" -> amount=349.0, currency="INR"
      - "₹349.00 (Incl. of all taxes)" -> amount=349.0, currency="INR", inclusive_of_taxes=True
      - "Rs. 1,299" -> amount=1299.0, currency="INR"
    Returns: (normalized_dict, status, ambiguity)
    """
    if not raw or not raw.strip():
        return None, "failed", "Empty MRP text"

    text = raw.strip()

    # Check for tax statement
    has_taxes = bool(re.search(r"(?:incl|inclusive)\.?\s*(?:of)?\s*all\s*taxes", text, re.IGNORECASE))

    # Match numeric amounts with currency prefixes
    # Handles: Rs. 349, Rs 349, ₹349, INR 349, 349.00
    cleaned = text.replace(",", "")
    matches = re.findall(r"(?:Rs\.?|INR|₹|\bMRP\b)\s*[:\-]?\s*([0-9]+(?:\.[0-9]{1,2})?)", cleaned, re.IGNORECASE)

    if not matches:
        # Fallback: look for any decimal or integer number
        matches = re.findall(r"\b([0-9]+(?:\.[0-9]{1,2})?)\b", cleaned)

    if not matches:
        return None, "failed", f"No numeric price amount found in '{raw}'"

    # Check for multiple differing amounts (ambiguity)
    unique_amounts = list(dict.fromkeys(matches))
    if len(unique_amounts) > 1:
        # Could be MRP vs USP or dual pricing
        amt = float(unique_amounts[0])
        return (
            {"amount": amt, "currency": "INR", "inclusive_of_taxes": has_taxes},
            "ambiguous",
            f"Multiple candidate amounts found: {unique_amounts}"
        )

    try:
        amt = float(matches[0])
        # Validate realistic price
        if amt <= 0:
            return None, "failed", f"Invalid non-positive price amount: {amt}"
        return (
            {"amount": amt, "currency": "INR", "inclusive_of_taxes": has_taxes},
            "success",
            None
        )
    except Exception as e:
        return None, "failed", f"Failed to parse amount from '{raw}': {e}"


def normalize_net_quantity(raw: str) -> Tuple[Optional[Dict[str, Any]], str, Optional[str]]:
    """
    Normalizes Net Quantity declarations.
    Examples:
      - "500 ml" -> quantity=500.0, unit="ml"
      - "1 kg" -> quantity=1.0, unit="kg"
      - "Net Wt.: 750g" -> quantity=750.0, unit="g"
      - "2 L" -> quantity=2.0, unit="l"
      - "100 N" -> quantity=100.0, unit="N"
    Returns: (normalized_dict, status, ambiguity)
    """
    if not raw or not raw.strip():
        return None, "failed", "Empty quantity text"

    text = raw.strip().replace(",", "")

    # Match number followed by metric unit
    # e.g., 500 ml, 1.5 kg, 750g, 2L, 100 N, 50 units
    pattern = r"([0-9]+(?:\.[0-9]+)?)\s*([a-zA-Z\.]+)"
    matches = re.findall(pattern, text)

    if not matches:
        return None, "failed", f"No quantity and unit pattern found in '{raw}'"

    # Find the best candidate unit
    valid_candidates = []
    for qty_str, unit_raw in matches:
        clean_unit = unit_raw.lower().rstrip(".")
        if clean_unit in METRIC_UNITS:
            try:
                val = float(qty_str)
                canonical_unit = METRIC_UNITS[clean_unit]
                valid_candidates.append((val, canonical_unit))
            except ValueError:
                continue

    if not valid_candidates:
        return None, "failed", f"No recognized metric unit in '{raw}'"

    if len(valid_candidates) > 1:
        # If multiple units found (e.g. 500 ml / 16.9 fl oz)
        val, unit = valid_candidates[0]
        return (
            {"quantity": val, "unit": unit},
            "ambiguous",
            f"Multiple quantity declarations detected: {valid_candidates}"
        )

    val, unit = valid_candidates[0]
    return {"quantity": val, "unit": unit}, "success", None


def normalize_unit_sale_price(raw: str) -> Tuple[Optional[Dict[str, Any]], str, Optional[str]]:
    """
    Normalizes Unit Sale Price (USP).
    Examples:
      - "₹0.70 / ml" -> amount=0.70, currency="INR", unit="ml"
      - "Rs. 1.25 per g" -> amount=1.25, currency="INR", unit="g"
    Returns: (normalized_dict, status, ambiguity)
    """
    if not raw or not raw.strip():
        return None, "failed", "Empty unit sale price text"

    text = raw.strip().replace(",", "")

    # Match price and unit
    match = re.search(
        r"(?:Rs\.?|INR|₹)?\s*([0-9]+(?:\.[0-9]+)?)\s*(?:/|per)\s*([a-zA-Z\.]+)",
        text,
        re.IGNORECASE
    )

    if match:
        amt_str, unit_raw = match.groups()
        clean_unit = unit_raw.lower().rstrip(".")
        canonical_unit = METRIC_UNITS.get(clean_unit, clean_unit)
        try:
            return (
                {"amount": float(amt_str), "currency": "INR", "unit": canonical_unit},
                "success",
                None
            )
        except ValueError:
            pass

    # Fallback to general price extract
    mrp_res, _, _ = normalize_mrp(raw)
    if mrp_res:
        return (
            {"amount": mrp_res["amount"], "currency": "INR", "unit": "unit"},
            "ambiguous",
            "Could not determine explicit per-unit measure; defaulted unit to 'unit'"
        )

    return None, "failed", f"Unable to parse unit sale price from '{raw}'"


def normalize_date(raw: str) -> Tuple[Optional[Dict[str, Any]], str, Optional[str]]:
    """
    Normalizes dates (mfg_date, expiry_date).
    Supports:
      - MM/YYYY: "01/2026", "01-2026"
      - DD/MM/YYYY: "15/01/2026", "15-01-2026"
      - YYYY-MM-DD: "2026-01-15"
      - Mon YYYY: "Jan 2026", "January 2026"
      - DD Mon YYYY: "15 Jan 2026"
    Returns: (normalized_dict, status, ambiguity)
    """
    if not raw or not raw.strip():
        return None, "failed", "Empty date text"

    # Strip prefixes like "MFG:", "EXP:", "DATE OF MFG", etc.
    cleaned = re.sub(r"^(?:MFG|MFD|EXP|PKD|BATCH|DATE|OF|BEST|BEFORE)\s*[\:\.\-]?\s*", "", raw.strip(), flags=re.IGNORECASE).strip()

    # 1. YYYY-MM-DD
    m = re.search(r"\b(20[2-3][0-9])[\/\-\.](0[1-9]|1[0-2])[\/\-\.](0[1-9]|[12][0-9]|3[01])\b", cleaned)
    if m:
        y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
        return {"year": y, "month": mo, "day": d, "date_iso": f"{y:04d}-{mo:02d}-{d:02d}"}, "success", None

    # 2. DD/MM/YYYY
    m = re.search(r"\b(0[1-9]|[12][0-9]|3[01])[\/\-\.](0[1-9]|1[0-2])[\/\-\.](20[2-3][0-9])\b", cleaned)
    if m:
        d, mo, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
        return {"year": y, "month": mo, "day": d, "date_iso": f"{y:04d}-{mo:02d}-{d:02d}"}, "success", None

    # 3. MM/YYYY (standard Legal Metrology declaration)
    m = re.search(r"\b(0[1-9]|1[0-2])[\/\-\.](20[2-3][0-9])\b", cleaned)
    if m:
        mo, y = int(m.group(1)), int(m.group(2))
        return {"year": y, "month": mo, "day": None, "date_iso": f"{y:04d}-{mo:02d}"}, "success", None

    # 4. YYYY/MM
    m = re.search(r"\b(20[2-3][0-9])[\/\-\.](0[1-9]|1[0-2])\b", cleaned)
    if m:
        y, mo = int(m.group(1)), int(m.group(2))
        return {"year": y, "month": mo, "day": None, "date_iso": f"{y:04d}-{mo:02d}"}, "success", None

    # 5. DD Mon YYYY: e.g. "15 Jan 2026"
    m = re.search(r"\b(0?[1-9]|[12][0-9]|3[01])\s+([A-Za-z]{3,9})\s+(20[2-3][0-9])\b", cleaned)
    if m:
        d, mon_str, y = int(m.group(1)), m.group(2).lower(), int(m.group(3))
        mo = MONTH_NAMES.get(mon_str)
        if mo:
            return {"year": y, "month": mo, "day": d, "date_iso": f"{y:04d}-{mo:02d}-{d:02d}"}, "success", None

    # 6. Mon YYYY: e.g. "Jan 2026"
    m = re.search(r"\b([A-Za-z]{3,9})\s+(20[2-3][0-9])\b", cleaned)
    if m:
        mon_str, y = m.group(1).lower(), int(m.group(2))
        mo = MONTH_NAMES.get(mon_str)
        if mo:
            return {"year": y, "month": mo, "day": None, "date_iso": f"{y:04d}-{mo:02d}"}, "success", None

    # 7. MM/YY 2-digit year fallback: e.g. "01/26"
    m = re.search(r"\b(0[1-9]|1[0-2])[\/\-\.]([2-3][0-9])\b", cleaned)
    if m:
        mo, y2 = int(m.group(1)), int(m.group(2))
        y = 2000 + y2
        return (
            {"year": y, "month": mo, "day": None, "date_iso": f"{y:04d}-{mo:02d}"},
            "ambiguous",
            "Inferred 4-digit year from 2-digit YY format"
        )

    return None, "failed", f"Unrecognized date format in '{raw}'"


def normalize_best_before(raw: str) -> Tuple[Optional[Dict[str, Any]], str, Optional[str]]:
    """
    Normalizes Best Before statements.
    Examples:
      - "Best Before: 6 months" -> duration_value=6, duration_unit="months"
      - "Use within 24 months from manufacture" -> duration_value=24, duration_unit="months"
      - "09/2026" -> parsed date
    Returns: (normalized_dict, status, ambiguity)
    """
    if not raw or not raw.strip():
        return None, "failed", "Empty best before text"

    text = raw.strip()

    # Duration format: e.g., 6 months, 180 days, 1 year
    m = re.search(r"(\d+)\s*(month|months|day|days|year|years|week|weeks)\b", text, re.IGNORECASE)
    if m:
        val = int(m.group(1))
        unit = m.group(2).lower()
        if unit in ("month", "months"):
            unit = "months"
        elif unit in ("day", "days"):
            unit = "days"
        elif unit in ("year", "years"):
            unit = "years"
        elif unit in ("week", "weeks"):
            unit = "weeks"

        return {
            "duration_value": val,
            "duration_unit": unit,
            "raw_statement": f"{val} {unit}",
            "date": None,
        }, "success", None

    # If it's an explicit date instead of duration
    date_res, status, amb = normalize_date(text)
    if date_res:
        return {
            "duration_value": None,
            "duration_unit": None,
            "raw_statement": raw,
            "date": date_res,
        }, status, amb

    return None, "failed", f"Unable to parse best-before duration or date from '{raw}'"


def normalize_fssai(raw: str) -> Tuple[Optional[Dict[str, Any]], str, Optional[str]]:
    """
    Normalizes FSSAI 14-digit license numbers.
    Examples:
      - "10015022003344"
      - "Lic No. 10015022003344"
    Returns: (normalized_dict, status, ambiguity)
    """
    if not raw or not raw.strip():
        return None, "failed", "Empty FSSAI license text"

    digits = re.sub(r"\D", "", raw)
    if len(digits) == 14:
        return {"license_number": digits, "is_valid_format": True}, "success", None

    # Found digits but wrong length
    if digits:
        return (
            {"license_number": digits, "is_valid_format": False},
            "failed",
            f"FSSAI license must be 14 digits, found {len(digits)} digits ('{digits}')"
        )

    return None, "failed", f"No digits found in FSSAI field '{raw}'"


def normalize_consumer_care(raw: str) -> Tuple[Optional[Dict[str, Any]], str, Optional[str]]:
    """
    Normalizes consumer care / customer helpline details.
    Extracts phone numbers, email addresses, and websites.
    Returns: (normalized_dict, status, ambiguity)
    """
    if not raw or not raw.strip():
        return None, "failed", "Empty consumer care text"

    text = raw.strip()

    # Extract email
    email_m = re.search(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b", text)
    email = email_m.group(0) if email_m else None

    # Extract phone / toll-free numbers (e.g., 1800-111-222, 020-12345678, +91 9876543210)
    phone_m = re.search(r"(?:\+?91[\-\s]?)?(?:1800[\-\s]?[0-9]{3}[\-\s]?[0-9]{3,4}|\b[0-9]{3,5}[\-\s]?[0-9]{6,8}\b|\b[6-9][0-9]{9}\b)", text)
    phone = phone_m.group(0) if phone_m else None

    # Extract website
    web_m = re.search(r"\b(?:https?:\/\/|www\.)[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b", text)
    website = web_m.group(0) if web_m else None

    if email or phone or website:
        return {
            "phone": phone,
            "email": email,
            "website": website,
            "raw_statement": text
        }, "success", None

    return {
        "phone": None,
        "email": None,
        "website": None,
        "raw_statement": text
    }, "ambiguous", "No explicit phone, email, or URL could be parsed from consumer care text"


def normalize_country_of_origin(raw: str) -> Tuple[Optional[Dict[str, Any]], str, Optional[str]]:
    """
    Normalizes Country of Origin declarations.
    Examples:
      - "Made in Japan" -> country="Japan", iso_code="JP"
      - "Country of Origin: India" -> country="India", iso_code="IN"
    Returns: (normalized_dict, status, ambiguity)
    """
    if not raw or not raw.strip():
        return None, "failed", "Empty country of origin text"

    cleaned = re.sub(r"^(?:Made\s+in|Product\s+of|Country\s+of\s+Origin\s*[:\-]?|Manufactured\s+in)\s*", "", raw.strip(), flags=re.IGNORECASE).strip()

    country_lower = cleaned.lower()
    for name, code in COUNTRY_ISO_MAP.items():
        if name in country_lower:
            return {"country": name.title(), "iso_code": code}, "success", None

    # Capitalized single/multi word fallback
    if cleaned:
        return {"country": cleaned.title(), "iso_code": None}, "ambiguous", f"Unrecognized ISO country name: '{cleaned}'"

    return None, "failed", f"Cannot determine country from '{raw}'"


def normalize_manufacturer_address(raw: str) -> Tuple[Optional[Dict[str, Any]], str, Optional[str]]:
    """
    Normalizes manufacturer / packer / importer address.
    Extracts 6-digit Indian PIN code, state, and city where recognizable.
    Returns: (normalized_dict, status, ambiguity)
    """
    if not raw or not raw.strip():
        return None, "failed", "Empty manufacturer address"

    text = raw.strip()

    # Extract 6-digit Indian PIN Code
    pin_m = re.search(r"\b([1-9][0-9]{5})\b", text)
    pin_code = pin_m.group(1) if pin_m else None

    # Detect Indian State
    detected_state = None
    for state in INDIAN_STATES:
        if re.search(rf"\b{re.escape(state)}\b", text, re.IGNORECASE):
            detected_state = state
            break

    # City heuristic (word before state or before PIN code)
    city = None
    if pin_code:
        # Check token immediately before PIN code
        parts = text[:text.find(pin_code)].rstrip(", \t\n").split(",")
        if parts:
            cand = parts[-1].strip()
            # If candidate matches state, take one prior
            if cand.lower() == (detected_state or "").lower() and len(parts) > 1:
                city = parts[-2].strip()
            else:
                city = cand

    return {
        "full_address": text,
        "pin_code": pin_code,
        "state": detected_state,
        "city": city,
    }, "success" if pin_code else "ambiguous", None if pin_code else "PIN code not found in address"


def normalize_batch_number(raw: str) -> Tuple[Optional[Dict[str, Any]], str, Optional[str]]:
    """
    Normalizes batch or lot numbers.
    Examples:
      - "Batch No: B-2026-03" -> batch_number="B-2026-03"
      - "Lot 4481" -> batch_number="4481"
    Returns: (normalized_dict, status, ambiguity)
    """
    if not raw or not raw.strip():
        return None, "failed", "Empty batch number"

    cleaned = re.sub(r"^(?:Batch\s*(?:No\.?|Number)?|Lot\s*(?:No\.?|Number)?|B\.?\s*No\.?)\s*[:\-]?\s*", "", raw.strip(), flags=re.IGNORECASE).strip()
    if cleaned:
        return {"batch_number": cleaned}, "success", None
    return None, "failed", f"Empty batch number after cleaning '{raw}'"


def normalize_commodity_name(raw: str) -> Tuple[Optional[Dict[str, Any]], str, Optional[str]]:
    """Normalizes product or commodity name."""
    if not raw or not raw.strip():
        return None, "failed", "Empty commodity name"
    cleaned = raw.strip()
    return {"commodity_name": cleaned}, "success", None


def normalize_barcode(raw: str) -> Tuple[Optional[Dict[str, Any]], str, Optional[str]]:
    """Normalizes barcode value."""
    if not raw or not raw.strip():
        return None, "failed", "Empty barcode"
    digits = re.sub(r"\D", "", raw)
    b_type = "EAN-13" if len(digits) == 13 else ("UPC-A" if len(digits) == 12 else "BARCODE")
    return {"barcode": digits or raw.strip(), "type": b_type}, "success", None


# Normalizer dispatch map
NORMALIZERS = {
    "mrp": normalize_mrp,
    "net_quantity": normalize_net_quantity,
    "unit_sale_price": normalize_unit_sale_price,
    "mfg_date": normalize_date,
    "expiry_date": normalize_date,
    "best_before_date": normalize_best_before,
    "fssai_license_no": normalize_fssai,
    "consumer_care_details": normalize_consumer_care,
    "country_of_origin": normalize_country_of_origin,
    "manufacturer_name": lambda r: ({"name": r.strip()}, "success", None) if r and r.strip() else (None, "failed", "Empty name"),
    "manufacturer_address": normalize_manufacturer_address,
    "commodity_name": normalize_commodity_name,
    "product_name": normalize_commodity_name,
    "batch_number": normalize_batch_number,
    "barcode": normalize_barcode,
}

# Standard mapping of field types to default capture panels
DEFAULT_PANEL_MAP = {
    "commodity_name": "front_panel",
    "product_name": "front_panel",
    "brand_name": "front_panel",
    "mfg_date": "declaration_panel",
    "expiry_date": "declaration_panel",
    "best_before_date": "declaration_panel",
    "batch_number": "declaration_panel",
    "consumer_care_details": "declaration_panel",
    "fssai_license_no": "declaration_panel",
    "mrp": "mrp_net_quantity",
    "net_quantity": "mrp_net_quantity",
    "unit_sale_price": "mrp_net_quantity",
    "manufacturer_name": "manufacturer_address",
    "manufacturer_address": "manufacturer_address",
    "country_of_origin": "manufacturer_address",
    "barcode": "barcode",
}


# =====================================================================
# 4. Canonical Package Data Builder
# =====================================================================

CANONICAL_FIELD_KEYS = [
    "mrp",
    "net_quantity",
    "unit_sale_price",
    "mfg_date",
    "expiry_date",
    "best_before_date",
    "fssai_license_no",
    "batch_number",
    "consumer_care_details",
    "country_of_origin",
    "manufacturer_name",
    "manufacturer_address",
    "commodity_name",
]


def build_canonical_package_data(
    extracted_fields: Optional[List[Union[Dict[str, Any], Any]]] = None,
    raw_text: Optional[str] = None,
    barcode: Optional[str] = None,
    source_panel_hints: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """
    Builds the canonical normalized package data structure from raw OCR results.

    Guarantees:
    - Never hallucinates missing fields (detected=False, normalization_status='not_detected')
    - Preserves exact raw text and bounding boxes for future audit
    - Returns structured normalized values when parsing succeeds
    - Flags ambiguous or failed normalizations explicitly
    """
    fields_map: Dict[str, Dict[str, Any]] = {
        key: empty_canonical_field() for key in CANONICAL_FIELD_KEYS
    }

    other_fields: Dict[str, Dict[str, Any]] = {}

    extracted_list = extracted_fields or []

    # Map extracted items into canonical fields
    for item in extracted_list:
        if isinstance(item, dict):
            ft = item.get("field_type")
            raw_val = item.get("value") or item.get("extracted_value")
            conf = item.get("confidence") or item.get("confidence_score")
            bbox = item.get("bbox_px") or item.get("bbox")
            zone = item.get("placement_zone")
            src_panel = item.get("source_panel")
        else:
            ft = getattr(item, "field_type", None)
            raw_val = getattr(item, "extracted_value", None) or getattr(item, "value", None)
            conf = getattr(item, "confidence_score", None) or getattr(item, "confidence", None)
            bbox = getattr(item, "bbox_px", None) or getattr(item, "bbox", None)
            zone = getattr(item, "placement_zone", None)
            src_panel = getattr(item, "source_panel", None)

        if not ft:
            continue

        # Determine best source panel identifier
        resolved_panel = (
            src_panel
            or (source_panel_hints.get(ft) if source_panel_hints else None)
            or (zone if zone and zone != "unknown" else None)
            or DEFAULT_PANEL_MAP.get(ft)
        )

        # Normalize raw value if present
        raw_str = str(raw_val).strip() if raw_val is not None else ""
        norm_func = NORMALIZERS.get(ft)

        if norm_func and raw_str:
            normalized_val, norm_status, ambiguity_msg = norm_func(raw_str)
        elif raw_str:
            normalized_val = {"raw_value": raw_str}
            norm_status = "success"
            ambiguity_msg = None
        else:
            normalized_val = None
            norm_status = "failed"
            ambiguity_msg = "Field detected but contains empty text"

        field_data = {
            "raw": raw_str if raw_str else None,
            "normalized": normalized_val,
            "confidence": round(float(conf), 4) if conf is not None else None,
            "source_panel": resolved_panel,
            "bbox": bbox,
            "detected": bool(raw_str),
            "normalization_status": norm_status if raw_str else "failed",
            "ambiguity": ambiguity_msg,
        }

        if ft in fields_map:
            fields_map[ft] = field_data
        else:
            other_fields[ft] = field_data

    # Barcode canonical field
    barcode_field = empty_canonical_field()
    if barcode:
        norm_bc, bc_status, bc_amb = normalize_barcode(barcode)
        barcode_field = {
            "raw": barcode,
            "normalized": norm_bc,
            "confidence": 1.0,
            "source_panel": "barcode",
            "bbox": None,
            "detected": True,
            "normalization_status": bc_status,
            "ambiguity": bc_amb,
        }
    elif "barcode" in other_fields:
        barcode_field = other_fields.pop("barcode")

    fields_map["barcode"] = barcode_field

    # Compute high-level metadata
    detected_count = sum(1 for f in fields_map.values() if f.get("detected"))
    success_count = sum(1 for f in fields_map.values() if f.get("normalization_status") == "success")

    total_key_fields = len(CANONICAL_FIELD_KEYS)
    overall_status = "complete" if success_count >= total_key_fields else ("partial" if detected_count > 0 else "empty")

    canonical_package = {
        **fields_map,
        "other_fields": other_fields,
        "raw_text": raw_text,
        "metadata": {
            "fields_detected_count": detected_count,
            "fields_normalized_count": success_count,
            "overall_status": overall_status,
        }
    }

    return canonical_package
