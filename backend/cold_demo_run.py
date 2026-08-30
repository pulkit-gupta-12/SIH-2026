"""
Phase 6 Cold Demo Run: Full end-to-end trace from clean session.
Executes Citizen -> Officer -> Rule Admin flows through official API endpoints with zero Django admin intervention.
"""
import os
import sys
import json
import time
from datetime import date
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev')
django.setup()

from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from apps.product_master.models import Product
from apps.rules_engine.models import RuleNotification

User = get_user_model()
client = APIClient()

demo_trace = {}

print("=================================================================")
print("           PHASE 6 COLD DEMO RUN — 3 DASHBOARD SUITE            ")
print("=================================================================")

# -----------------------------------------------------------------
# 1. CITIZEN DEMO WORKFLOW
# -----------------------------------------------------------------
print("\n>>> STEP 1: CITIZEN WORKFLOW (citizen_demo) <<<")
citizen = User.objects.filter(role_assignments__role__name='citizen').first() or User.objects.get(username='citizen_demo')
client.force_authenticate(user=citizen)

# 1a. Query never-scanned barcode without image
fresh_barcode = f"890999{int(time.time()) % 10000000:07d}"
resp_1a = client.post('/api/scans/', {
    'barcode': fresh_barcode,
    'category': 'food',
}, format='json')
print(f"1a. First scan without photo -> HTTP {resp_1a.status_code}")
print(f"    Payload response: {resp_1a.json()}")
demo_trace['citizen_first_scan_no_photo'] = resp_1a.json()

# 1b. First scan WITH photo (runs OCR pipeline + records snapshot)
resp_1b = client.post('/api/scans/', {
    'barcode': fresh_barcode,
    'category': 'food',
    'image_urls': ['http://localhost:8000/media/demo_pure_ghee.jpg'],
}, format='json')
print(f"1b. First scan with photo -> HTTP {resp_1b.status_code}")
snapshot_data = resp_1b.json()
product_id = snapshot_data['product_id']
print(f"    Product Created/Resolved: {snapshot_data['product_name']} (ID: {product_id})")
print(f"    Compliance Verdict: {snapshot_data['verdict']}")
demo_trace['citizen_first_scan_with_photo'] = snapshot_data

# 1c. File a complaint for this product
resp_1c = client.post('/api/complaints/', {
    'product': product_id,
    'description': 'Overcharging observed at retail outlet: Net quantity numeral height smudged and unreadable.',
    'location': 'Connaught Place, New Delhi, Delhi',
    'photo_urls': ['http://localhost:8000/media/complaint_ghee.jpg'],
}, format='json')
print(f"1c. File Citizen Complaint -> HTTP {resp_1c.status_code}")
complaint_data = resp_1c.json()
complaint_id = complaint_data['id']
print(f"    Complaint ID: {complaint_id} | Risk Score: {complaint_data['risk_score']} | State: {complaint_data['routed_to_state']}")
demo_trace['citizen_filed_complaint'] = complaint_data

# -----------------------------------------------------------------
# 2. FIELD OFFICER DEMO WORKFLOW
# -----------------------------------------------------------------
print("\n>>> STEP 2: FIELD OFFICER WORKFLOW (officer_demo) <<<")
officer = User.objects.filter(role_assignments__role__name='field_officer').first() or User.objects.get(username='officer_demo')
client.force_authenticate(user=officer)

# 2a. Inspection Queue verification
resp_2a = client.get('/api/inspections/queue/')
print(f"2a. Fetch Officer Inspection Queue -> HTTP {resp_2a.status_code}")
queue_items = resp_2a.json()
queue_list = queue_items.get('results', queue_items) if isinstance(queue_items, dict) else queue_items
complaint_in_queue = next((item for item in queue_list if item.get('complaint') == complaint_id or item.get('id') == f"cmp-{complaint_id}"), None)
print(f"    Total Queue Items: {len(queue_list)}")
print(f"    Citizen Complaint found in queue: {complaint_in_queue is not None}")
if complaint_in_queue:
    print(f"    -> Item ID: {complaint_in_queue['id']} | Source: {complaint_in_queue['source']} | Priority: {complaint_in_queue['priority_score']}")
demo_trace['officer_queue_item'] = complaint_in_queue

# 2b. Officer performs guided capture scan on another product
officer_barcode = f"890888{int(time.time()) % 10000000:07d}"
resp_2b = client.post('/api/scans/', {
    'barcode': officer_barcode,
    'category': 'food',
    'capture_method': 'guided_capture',
    'location': 'INA Market, New Delhi',
    'image_urls': [
        'http://localhost:8000/media/officer_front.jpg',
        'http://localhost:8000/media/officer_back.jpg',
    ],
}, format='json')
print(f"2b. Guided Capture Scan -> HTTP {resp_2b.status_code}")
scan_data = resp_2b.json()
scan_id = scan_data['id']
check_id = scan_data['compliance_check']['id']
officer_product_id = scan_data['product'] if isinstance(scan_data['product'], int) else scan_data['product']['id']
print(f"    Scan ID: {scan_id} | Check ID: {check_id} | Product ID: {officer_product_id} | Verdict: {scan_data['compliance_check']['verdict']}")
demo_trace['officer_scan'] = scan_data

# 2c. Officer reviews & confirms findings
resp_2c = client.post(f'/api/compliance-checks/{check_id}/confirm/')
print(f"2c. Officer Confirm Findings -> HTTP {resp_2c.status_code}")
demo_trace['officer_confirm_check'] = resp_2c.json()

# 2d. Officer checks Violation History Timeline
resp_2d = client.get(f'/api/products/{officer_product_id}/violation-history/')
print(f"2d. Product Violation History Timeline -> HTTP {resp_2d.status_code}")
history_data = resp_2d.json()
print(f"    Violation events count: {len(history_data.get('history', []))}")
demo_trace['officer_violation_history'] = history_data

# 2e. Officer opens Statutory Case (spawns Section 29 or 39 Notice)
violation_id = None
if scan_data['compliance_check'].get('violations'):
    violation_id = scan_data['compliance_check']['violations'][0]['id']

resp_2e = client.post('/api/cases/', {
    'product': officer_product_id,
    'violation': violation_id,
    'rectification_days': 30,
}, format='json')
print(f"2e. Officer Case Creation -> HTTP {resp_2e.status_code}")
case_data = resp_2e.json()
print(f"    Case ID: {case_data['id']} | Classification: {case_data['classification']} | Status: {case_data['status']}")
if case_data.get('improvement_notice'):
    print(f"    -> Section 29 Improvement Notice ID: {case_data['improvement_notice']['id']} (Deadline: {case_data['improvement_notice']['rectification_deadline']})")
if case_data.get('penalty_case'):
    print(f"    -> Section 39 Penalty Case ID: {case_data['penalty_case']['id']}")
demo_trace['officer_created_case'] = case_data

# -----------------------------------------------------------------
# 3. RULE ENGINE ADMIN DEMO WORKFLOW
# -----------------------------------------------------------------
print("\n>>> STEP 3: RULE ENGINE ADMIN WORKFLOW (admin_demo) <<<")
admin = User.objects.filter(role_assignments__role__name='national_admin').first() or User.objects.get(username='admin_demo')
client.force_authenticate(user=admin)

# 3a. Ingest/Fetch incoming notifications
resp_3a = client.get('/api/rules/incoming-notifications/')
print(f"3a. Incoming Notifications -> HTTP {resp_3a.status_code}")
notif_data = resp_3a.json()
notifications = notif_data.get('results', notif_data) if isinstance(notif_data, dict) else notif_data
first_notif = notifications[0]
print(f"    Notification: {first_notif['notification_no']} - {first_notif['title'][:50]}...")
demo_trace['admin_notification'] = first_notif

# 3b. Generate AI Rule Draft
resp_3b = client.post('/api/rules/draft/', {
    'notification_id': first_notif['id'],
}, format='json')
print(f"3b. AI Draft Generation -> HTTP {resp_3b.status_code}")
draft_data = resp_3b.json()
draft_id = draft_data['id']
print(f"    Draft ID: {draft_id} | Rule Code: {draft_data['rule_id_code']} | Supersedes Rule: {draft_data.get('supersedes_rule_code')}")
demo_trace['admin_generated_draft'] = draft_data

# 3c. Revise Draft in-place
resp_3c = client.post(f'/api/rules/{draft_id}/revise/', {
    'new_clause_text': draft_data['new_clause_text'] + ' (Revised with PDP prominent display requirements)',
    'comment': 'Admin updated clause wording following legal review.',
}, format='json')
print(f"3c. Revise Draft In-Place -> HTTP {resp_3c.status_code}")
revised_data = resp_3c.json()
print(f"    Draft Status: {revised_data['status']} | Comments: {len(revised_data['comments'])}")
demo_trace['admin_revised_draft'] = revised_data

# 3d. Approve Draft
resp_3d = client.post(f'/api/rules/{draft_id}/approve/', {
    'effective_date': '2026-05-01',
    'comment': 'Approved by National Admin with effective date 2026-05-01.',
}, format='json')
print(f"3d. Approve Draft -> HTTP {resp_3d.status_code}")
demo_trace['admin_approved_draft'] = resp_3d.json()

# 3e. Run Sandbox Simulation
resp_3e = client.post(f'/api/rules/{draft_id}/simulate/')
print(f"3e. Run Read-Only Simulation -> HTTP {resp_3e.status_code}")
sim_data = resp_3e.json()
print(f"    Evaluated Scans: {sim_data['total_scans_evaluated']} | Before: {sim_data['before_compliance_rate']}% | After: {sim_data['after_compliance_rate']}%")
demo_trace['admin_simulation'] = sim_data

# 3f. Publish Live Rule
resp_3f = client.post(f'/api/rules/{draft_id}/publish/')
print(f"3f. Publish Live Rule -> HTTP {resp_3f.status_code}")
pub_data = resp_3f.json()
print(f"    Live Rule ID: {pub_data['id']} | Status: {pub_data['status']} | Effective From: {pub_data['effective_from']}")
demo_trace['admin_published_rule'] = pub_data

# 3g. Admin Dashboard summary convergence check
resp_3g = client.get('/api/rules/admin-dashboard/')
print(f"3g. Admin Dashboard Analytics -> HTTP {resp_3g.status_code}")
admin_dash = resp_3g.json()
print(f"    Total Active Rules: {admin_dash['kpis']['total_active_rules']}")
print(f"    Total Cases: {admin_dash['kpis']['total_cases']} | Open Cases: {admin_dash['kpis']['open_cases']}")
print(f"    Regional Violations (Delhi): {next((r for r in admin_dash['violations_by_region'] if r['region'] == 'Delhi'), None)}")
demo_trace['admin_dashboard_summary'] = admin_dash

with open('cold_demo_trace.json', 'w') as f:
    json.dump(demo_trace, f, indent=2)

print("\n=================================================================")
print("[SUCCESS] COLD DEMO RUN FINISHED SUCCESSFULLY WITH ZERO DJANGO ADMIN EDITS")
print("=================================================================")
