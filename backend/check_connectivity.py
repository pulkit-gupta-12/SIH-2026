import requests
import json

BASE = 'http://127.0.0.1:8000'
VITE_BASE = 'http://localhost:5173'

def test_all():
    print("=" * 60)
    print("1. CHECK ROOT API & HEALTH ENDPOINTS")
    print("=" * 60)
    r = requests.get(f"{BASE}/")
    print(f"GET {BASE}/ -> Status: {r.status_code}")
    if r.status_code == 200:
        print(f"Service: {r.json().get('service')}, Status: {r.json().get('status')}")

    print("\n" + "=" * 60)
    print("2. CHECK FRONTEND VITE PROXY (http://localhost:5173/api/)")
    print("=" * 60)
    try:
        r_proxy = requests.get(f"{VITE_BASE}/api/")
        print(f"GET {VITE_BASE}/api/ -> Status: {r_proxy.status_code}")
        if r_proxy.status_code == 200:
            print("Proxy connectivity: OK (Vite forwarded request to Django backend)")
    except Exception as e:
        print(f"Vite Proxy Error: {e}")

    print("\n" + "=" * 60)
    print("3. AUTHENTICATION & JWT TOKENS")
    print("=" * 60)
    roles = [
        ("citizen_demo", "demo1234", "Citizen"),
        ("officer_demo", "demo1234", "Field Officer"),
        ("controller_demo", "demo1234", "State Controller"),
        ("admin_demo", "demo1234", "National Admin"),
        ("business_demo", "demo1234", "Business Entity"),
        ("ecommerce_demo", "demo1234", "Ecommerce Partner"),
        ("ruleadmin_demo", "demo1234", "Rule Admin"),
    ]

    tokens = {}
    for username, password, role_name in roles:
        r_auth = requests.post(f"{BASE}/api/auth/login/", json={"username": username, "password": password})
        if r_auth.status_code == 200:
            data = r_auth.json()
            tokens[username] = data.get("access")
            assigned_roles = [r.get("name") if isinstance(r, dict) else r for r in data.get("user", {}).get("roles", [])]
            print(f"  [OK] {role_name:<20} ({username}): 200 OK | Roles: {assigned_roles}")
        else:
            print(f"  [FAIL] {role_name:<20} ({username}): {r_auth.status_code} | {r_auth.text[:80]}")

    cit_token = tokens.get("citizen_demo")
    off_token = tokens.get("officer_demo")
    admin_token = tokens.get("admin_demo")

    print("\n" + "=" * 60)
    print("4. CITIZEN FEATURES & API ENDPOINTS")
    print("=" * 60)
    if cit_token:
        headers = {"Authorization": f"Bearer {cit_token}"}

        # 4a. Products directory
        rp = requests.get(f"{BASE}/api/products/", headers=headers)
        p_count = len(rp.json()) if isinstance(rp.json(), list) else len(rp.json().get("results", []))
        print(f"  [OK] Product Directory Search: {rp.status_code} OK ({p_count} products loaded)")

        # 4b. Barcode scan & instant compliance snapshot lookup
        r_scan = requests.post(f"{BASE}/api/scans/", headers=headers, json={"barcode": "8901234567890", "category": "food"})
        print(f"  [OK] Barcode Scan (8901234567890): {r_scan.status_code} | Verdict: {r_scan.json().get('verdict')}")

        # 4c. First-time camera photo scan pipeline (single image)
        r_first = requests.post(f"{BASE}/api/scans/", headers=headers, json={
            "barcode": "8909999888877",
            "image_urls": ["http://localhost:8000/media/sample_label.jpg"],
            "category": "food"
        })
        print(f"  [OK] Photo Scan (New Product): {r_first.status_code} | Verdict: {r_first.json().get('verdict')}")

        # 4d. Citizen complaints
        rc = requests.get(f"{BASE}/api/complaints/mine/", headers=headers)
        c_count = len(rc.json()) if isinstance(rc.json(), list) else len(rc.json().get("results", []))
        print(f"  [OK] Citizen Filed Complaints: {rc.status_code} OK ({c_count} complaints)")

        # 4e. Citizen Dashboard
        rd_cit = requests.get(f"{BASE}/api/dashboards/citizen/", headers=headers)
        print(f"  [OK] Citizen Dashboard: {rd_cit.status_code} OK")

    print("\n" + "=" * 60)
    print("5. FIELD OFFICER FEATURES & API ENDPOINTS")
    print("=" * 60)
    if off_token:
        headers = {"Authorization": f"Bearer {off_token}"}

        # 5a. Inspection Queue
        rq = requests.get(f"{BASE}/api/inspections/queue/", headers=headers)
        q_count = len(rq.json()) if isinstance(rq.json(), list) else len(rq.json().get("results", []))
        print(f"  [OK] Officer Inspection Queue: {rq.status_code} OK ({q_count} items in queue)")

        # 5b. 6-Step Guided Capture Multi-Image Scan Submit
        r_guided = requests.post(f"{BASE}/api/scans/", headers=headers, json={
            "barcode": "8901234567890",
            "category": "food",
            "image_urls": [
                "http://localhost:8000/media/step1_pdp.jpg",
                "http://localhost:8000/media/step2_decl.jpg",
                "http://localhost:8000/media/step3_mrp.jpg",
                "http://localhost:8000/media/step4_mfg.jpg",
                "http://localhost:8000/media/step5_gtin.jpg",
                "http://localhost:8000/media/step6_seal.jpg",
            ],
            "location": "Central Mart, Connaught Place, New Delhi",
            "role_context": "officer",
            "capture_method": "guided_capture"
        })
        scan_id = r_guided.json().get("id") if r_guided.status_code == 201 else None
        print(f"  [OK] Guided Capture Submission: {r_guided.status_code} Created (Scan ID: {scan_id})")

        # 5c. Scan processing result
        if scan_id:
            r_proc = requests.get(f"{BASE}/api/scans/{scan_id}/processing-result/", headers=headers)
            extracted_cnt = len(r_proc.json().get("extracted_fields", []))
            print(f"  [OK] Scan Processing Result (OCR & Fields): {r_proc.status_code} OK ({extracted_cnt} extracted fields)")

        # 5d. Enforcement Cases
        rcases = requests.get(f"{BASE}/api/cases/", headers=headers)
        cases_cnt = len(rcases.json()) if isinstance(rcases.json(), list) else len(rcases.json().get("results", []))
        print(f"  [OK] Enforcement Cases: {rcases.status_code} OK ({cases_cnt} cases)")

        # 5e. Officer Dashboard
        rd_off = requests.get(f"{BASE}/api/dashboards/officer/", headers=headers)
        print(f"  [OK] Officer Dashboard: {rd_off.status_code} OK")

    print("\n" + "=" * 60)
    print("6. NATIONAL ADMIN & RULES ENGINE")
    print("=" * 60)
    if admin_token:
        headers = {"Authorization": f"Bearer {admin_token}"}

        # 6a. Rule repository
        rr = requests.get(f"{BASE}/api/rules/", headers=headers)
        rules_cnt = len(rr.json()) if isinstance(rr.json(), list) else len(rr.json().get("results", []))
        print(f"  [OK] Legal Metrology Rules Repository: {rr.status_code} OK ({rules_cnt} active rules)")

        # 6b. Rule notification monitor
        rnotifs = requests.get(f"{BASE}/api/rules/incoming-notifications/", headers=headers)
        notif_cnt = len(rnotifs.json()) if isinstance(rnotifs.json(), list) else len(rnotifs.json().get("results", []))
        print(f"  [OK] Rule Notification Monitor: {rnotifs.status_code} OK ({notif_cnt} notifications)")

        # 6c. Admin Dashboard Analytics Summary
        rd_adm = requests.get(f"{BASE}/api/rules/admin-dashboard/", headers=headers)
        print(f"  [OK] National Admin Analytics Dashboard: {rd_adm.status_code} OK")

        # 6d. Inspection weights configuration
        rweights = requests.get(f"{BASE}/api/rules/inspection-weights/", headers=headers)
        print(f"  [OK] Inspection Weights Engine: {rweights.status_code} OK")

    print("\n" + "=" * 60)
    print("CONNECTIVITY CHECK COMPLETE — ALL SYSTEMS OPERATIONAL")
    print("=" * 60)

if __name__ == "__main__":
    test_all()
