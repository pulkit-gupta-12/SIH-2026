"""
Services for Complaints app:
- Risk score computation based on product category, violation history, and description keywords.
- State routing determination from location strings and user profile.
"""
import re
from apps.compliance.models import ProductComplianceHistory

STATE_KEYWORDS = {
    "Delhi": ["delhi", "new delhi", "connaught place", "karol bagh", "dwarka", "saket", "rohini", "narela"],
    "Uttar Pradesh": ["uttar pradesh", "up", "noida", "greater noida", "ghaziabad", "lucknow", "kanpur", "varanasi", "agra"],
    "Maharashtra": ["maharashtra", "mumbai", "pune", "nagpur", "thane", "nashik", "aurangabad"],
    "Karnataka": ["karnataka", "bengaluru", "bangalore", "mysuru", "mysore", "hubballi", "mangalore"],
    "Tamil Nadu": ["tamil nadu", "tn", "chennai", "coimbatore", "madurai", "salem"],
    "Telangana": ["telangana", "hyderabad", "secunderabad", "warangal"],
    "Gujarat": ["gujarat", "ahmedabad", "surat", "vadodara", "rajkot", "gandhinagar"],
    "Rajasthan": ["rajasthan", "jaipur", "jodhpur", "udaipur", "kota"],
    "West Bengal": ["west bengal", "wb", "kolkata", "howrah", "darjeeling"],
    "Haryana": ["haryana", "gurugram", "gurgaon", "faridabad", "panipat", "ambala"],
    "Punjab": ["punjab", "ludhiana", "amritsar", "jalandhar", "patiala"],
    "Kerala": ["kerala", "kochi", "thiruvananthapuram", "kozhikode"],
    "Madhya Pradesh": ["madhya pradesh", "mp", "bhopal", "indore", "gwalior", "jabalpur"],
    "Bihar": ["bihar", "patna", "gaya", "muzaffarpur"],
}

CATEGORY_WEIGHTS = {
    "medical_device": 25.0,
    "food": 20.0,
    "import": 15.0,
    "electronics": 10.0,
    "general": 5.0,
}


def calculate_complaint_risk_score(product=None, description="", photo_urls=None):
    """
    Computes a realistic risk score between 30.0 and 98.0 for a complaint.
    Factors:
    - Base score: 40.0
    - Product commodity category sensitivity
    - Product prior violation history & repeat offenses
    - High-severity keywords in complaint text (overcharging, above MRP, tampering, expiry)
    - Photo evidence presence
    """
    score = 40.0
    desc_lower = (description or "").lower()

    # 1. Product category weight
    if product and product.category:
        score += CATEGORY_WEIGHTS.get(product.category, 5.0)

    # 2. Product compliance history factor
    if product:
        repeat_count = ProductComplianceHistory.objects.filter(
            product=product, is_first_time=False
        ).count()
        prior_count = ProductComplianceHistory.objects.filter(product=product).count()
        if repeat_count > 0:
            score += 20.0
        elif prior_count > 0:
            score += 10.0

    # 3. Description keyword severity
    if any(k in desc_lower for k in ["overcharg", "above mrp", "tamper", "fraud", "extort"]):
        score += 15.0
    elif any(k in desc_lower for k in ["expir", "miss", "fake", "defective", "smudge", "unclear"]):
        score += 10.0

    # 4. Photo evidence presence (increases verified severity/confidence)
    if photo_urls and len(photo_urls) > 0:
        score += 5.0

    return min(max(round(score, 1), 30.0), 98.0)


def determine_routed_state(location="", user=None):
    """
    Determines the routed jurisdiction state from complaint location string
    or the filing user's profile, defaulting to 'Delhi'.
    """
    if location:
        loc_lower = location.lower()
        for state, keywords in STATE_KEYWORDS.items():
            for kw in keywords:
                if re.search(r"\b" + re.escape(kw) + r"\b", loc_lower):
                    return state

    if user and user.is_authenticated:
        assignment = user.role_assignments.filter(state__isnull=False).exclude(state="").first()
        if assignment and assignment.state:
            # Map common 2-letter codes or full names
            state_code_map = {"DL": "Delhi", "UP": "Uttar Pradesh", "MH": "Maharashtra", "KA": "Karnataka"}
            return state_code_map.get(assignment.state, assignment.state)

    return "Delhi"
