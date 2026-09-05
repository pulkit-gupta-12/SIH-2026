from datetime import date, timedelta
from .models import Case, ImprovementNotice, PenaltyCase
from apps.compliance.models import ProductComplianceHistory
from apps.complaints.models import Complaint

def auto_create_enforcement_case(product, violation=None, opened_by=None, complaint_id=None, rectification_days=30):
    """
    Creates a Case (and its related ImprovementNotice or PenaltyCase) based on the 
    ProductComplianceHistory.
    """
    history_entry = None
    if violation:
        history_entry = ProductComplianceHistory.objects.filter(
            product=product, violation=violation
        ).first()
    if not history_entry:
        history_entry = ProductComplianceHistory.objects.filter(product=product).first()

    is_first_time = history_entry.is_first_time if history_entry else True

    if is_first_time:
        # 1st Offense -> Section 29 Improvement Notice (30-day rectification window)
        case = Case.objects.create(
            product=product,
            violation=violation,
            complaint_id=complaint_id,
            classification="first_time",
            status="notice_sent",
            opened_by=opened_by,
        )
        deadline = date.today() + timedelta(days=rectification_days)
        ImprovementNotice.objects.create(
            case=case,
            issued_by=opened_by,
            rectification_deadline=deadline,
            outcome="pending",
        )
    else:
        # Repeat Offense -> Section 39 Penalty Case
        case = Case.objects.create(
            product=product,
            violation=violation,
            complaint_id=complaint_id,
            classification="repeat",
            status="escalated",
            opened_by=opened_by,
        )
        PenaltyCase.objects.create(
            case=case,
            escalated_by=opened_by,
            payment_status="pending",
            appeal_status="none",
        )

    # Link case back to the compliance history entry without creating any duplicate entry
    if history_entry and not history_entry.case:
        history_entry.case = case
        history_entry.save(update_fields=["case"])

    # If opened from a citizen complaint, update complaint status to 'under_investigation'
    if complaint_id:
        Complaint.objects.filter(id=complaint_id).update(status="under_investigation")
        
    return case
