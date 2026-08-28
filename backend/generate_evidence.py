import json
import os
import sys
import django

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev')
django.setup()

from datetime import date
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from apps.rules_engine.models import RuleNotification, RuleDraft, RuleSimulationResult, Rule

User = get_user_model()
admin = User.objects.filter(role_assignments__role__name='national_admin').first() or User.objects.get(username='admin_demo')

client = APIClient()
client.force_authenticate(user=admin)

print('=== 1. NOTIFICATION INGESTION (Step A) ===')
r1 = client.get('/api/rules/incoming-notifications/')
notifs = r1.json()
target_notif = notifs['results'][0] if 'results' in notifs else notifs[0]
print(f"Notification ID: {target_notif['id']}")
print(f"Notification No: {target_notif['notification_no']}")
print(f"Title: {target_notif['title']}")
print(f"Status: {target_notif['status']}")

print('\n=== 2. AI DRAFT GENERATION (Step B) ===')
r2 = client.post('/api/rules/draft/', {'notification_id': target_notif['id']}, format='json')
draft_data = r2.json()
draft_id = draft_data['id']
print(f"Draft ID: {draft_id}")
print(f"Rule ID Code: {draft_data['rule_id_code']}")
print(f"Section Ref: {draft_data['section_ref']}")
print(f"Proposed Condition: {json.dumps(draft_data['proposed_condition'])}")
print(f"Status: {draft_data['status']}")

print('\n=== 3. ADMIN REVIEW & REVISE (Steps C, D, E) ===')
r3 = client.post(f"/api/rules/{draft_id}/revise/", {
    'new_clause_text': 'The minimum height of numeral in declarations shall be 2.5 mm for packs up to 1000g, and 6.5 mm for packs exceeding 1000g on Principal Display Panel.',
    'proposed_condition': {
        'type': 'font_size_check',
        'field': 'net_quantity',
        'min_height_mm': 2.5,
        'min_height_mm_large_pack': 6.5,
        'pack_size_threshold_g': 1000
    },
    'comment': 'Admin updated threshold to 2.5mm / 6.5mm with explicit PDP reference per legal council review.'
}, format='json')
revised_data = r3.json()
print(f"Revised Status: {revised_data['status']}")
print(f"Comments count: {len(revised_data['comments'])}")
print(f"Latest Comment: {revised_data['comments'][-1]['comment']}")

print('\n=== 4. ADMIN APPROVE (Step F) ===')
r4 = client.post(f"/api/rules/{draft_id}/approve/", {
    'effective_date': '2026-04-01',
    'comment': 'Approved by National Admin with effective date 2026-04-01.'
}, format='json')
approved_data = r4.json()
print(f"Approved Status: {approved_data['status']}")
print(f"Effective Date: {approved_data['effective_date']}")

print('\n=== 5. SANDBOX SIMULATION (Steps H6-H7) ===')
r5 = client.post(f"/api/rules/{draft_id}/simulate/")
sim_data = r5.json()
print(f"Simulation ID: {sim_data['id']}")
print(f"Evaluated Scans: {sim_data['total_scans_evaluated']}")
print(f"Before Compliance Rate: {sim_data['before_compliance_rate']}%")
print(f"After Compliance Rate: {sim_data['after_compliance_rate']}%")
print(f"Projected Violation Diff: {sim_data['projected_violation_diff']}")
print(f"Impact Summary: {sim_data['metrics'].get('impact_summary')}")

print('\n=== 6. PUBLISH LIVE (Step G) ===')
r6 = client.post(f"/api/rules/{draft_id}/publish/", format='json')
published_data = r6.json()
print(f"Live Rule ID: {published_data['id']}")
print(f"Rule ID Code: {published_data['rule_id_code']}")
print(f"Status: {published_data['status']}")
print(f"Effective From: {published_data['effective_from']}")
print(f"Superseded By Code: {published_data.get('superseded_by_code')}")

print('\n=== 7. ADMIN DASHBOARD & INSPECTION WEIGHTS (Steps H & I) ===')
r7 = client.get('/api/rules/admin-dashboard/')
dash_data = r7.json()
print(f"Total Active Rules: {dash_data['kpis']['total_active_rules']}")
print(f"National Compliance Rate: {dash_data['kpis']['national_compliance_rate']}%")

r8 = client.post('/api/rules/inspection-weights/', {
    'risk_engine_weight': 0.45,
    'complaint_weight': 0.35,
    'ecommerce_weight': 0.20,
    'repeat_offense_multiplier': 2.0
}, format='json')
weights_data = r8.json()
print(f"Updated Inspection Weights: Risk={weights_data['risk_engine_weight']}, Complaint={weights_data['complaint_weight']}, Ecom={weights_data['ecommerce_weight']}")

print('\n=== 8. COMPLETE LIVE CYCLE JSON DUMP ===')
full_evidence = {
    "notification": target_notif,
    "draft": draft_data,
    "revised_draft": revised_data,
    "approved_draft": approved_data,
    "simulation": sim_data,
    "published_rule": published_data,
    "dashboard_kpis": dash_data['kpis'],
    "inspection_weights": weights_data,
}
with open('live_phase43_evidence.json', 'w') as f:
    json.dump(full_evidence, f, indent=2)
print("Saved live_phase43_evidence.json successfully!")
