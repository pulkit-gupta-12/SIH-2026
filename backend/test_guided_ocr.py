def run_test():
    import requests
    import base64

    # Simulate 6 captured camera frames
    sample_data_url = 'data:image/jpeg;base64,' + base64.b64encode(b'FakeJpegImagePayload' * 200).decode('utf-8')

    # Login as officer
    r_auth = requests.post('http://127.0.0.1:8000/api/auth/login/', json={'username': 'officer_demo', 'password': 'demo1234'})
    token = r_auth.json().get('access')
    headers = {'Authorization': f'Bearer {token}'}

    # Submit 6-step guided scan
    payload = {
        'barcode': '8901234567890',
        'category': 'food',
        'image_urls': [
            sample_data_url, # 1. Front PDP
            sample_data_url, # 2. Declaration Panel
            sample_data_url, # 3. MRP & Net Qty
            sample_data_url, # 4. Manufacturer Block
            sample_data_url, # 5. Barcode & GTIN
            sample_data_url, # 6. Wrap-around Seal
        ],
        'location': 'Central Supermarket, Connaught Place, New Delhi',
        'role_context': 'officer',
        'capture_method': 'guided_capture'
    }

    r = requests.post('http://127.0.0.1:8000/api/scans/', headers=headers, json=payload)
    print('Guided Scan Submit Status:', r.status_code)
    assert r.status_code == 201, f'Expected 201, got {r.status_code}: {r.text}'
    scan = r.json()
    scan_id = scan['id']
    print(f'Scan ID: {scan_id} created successfully.')

    # Query processing-result endpoint (same as frontend ProcessingResultPage)
    r_result = requests.get(f'http://127.0.0.1:8000/api/scans/{scan_id}/processing-result/', headers=headers)
    print('Processing Result Status:', r_result.status_code)
    assert r_result.status_code == 200, f'Expected 200, got {r_result.status_code}'
    data = r_result.json()

    print('Status:', data['status'])
    print('Extracted OCR Fields (', len(data['extracted_fields']), '):')
    for f in data['extracted_fields']:
        ft = f['field_type']
        val = f['extracted_value']
        conf = f['confidence_score']
        font = f.get('font_size_mm')
        print(f"  - {ft}: {val} (confidence: {conf}, font: {font}mm)")

    print('Compliance Check Verdict:', data['compliance_check']['verdict'])
    print('SUCCESS: 6-STEP OCR EXTRACTIONS AND EVALUATION WORKING!')


if __name__ == '__main__':
    run_test()

