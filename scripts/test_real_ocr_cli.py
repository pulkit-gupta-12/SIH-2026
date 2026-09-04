#!/usr/bin/env python3
"""
Manual test script for Legal Metrology PaddleOCR Service (Port 8001).
Usage:
    python scripts/test_real_ocr_cli.py [path_to_image]

If no image path is provided, creates a synthetic product package label with:
- MRP
- Net Quantity
- Dates (MFD, EXP)
- FSSAI License
- Manufacturer details
- Consumer Care details
and sends it to the OCR microservice.
"""
import sys
import os
import requests
import json
import numpy as np
import cv2

OCR_SERVICE_URL = os.environ.get("OCR_SERVICE_URL", "http://localhost:8001")


def create_synthetic_product_label(output_path="sample_label.jpg") -> str:
    """Generate a realistic test packaged commodity label with standard declarations."""
    img = np.ones((550, 700, 3), dtype=np.uint8) * 255

    # Header
    cv2.rectangle(img, (20, 15), (680, 65), (40, 120, 40), -1)
    cv2.putText(img, "LEGAL METROLOGY DECLARATION PANEL", (30, 48), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

    # Declarations
    lines = [
        "Product: Pure Mustard Oil",
        "Net Qty: 1 L (910 g)",
        "MRP: Rs. 245.00 (Incl. of all taxes)",
        "Unit Sale Price: Rs. 0.24 / ml",
        "MFD: 15/01/2026",
        "EXP: 14/01/2027",
        "fssai Lic. No. 10015022003344",
        "Manufactured By: Bharat Agro Ltd",
        "Country of Origin: India",
    ]

    y = 105
    for line in lines:
        cv2.putText(img, line, (30, y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (20, 20, 20), 2)
        y += 40

    # Draw simulated barcode panel
    cv2.rectangle(img, (30, 470), (350, 520), (230, 230, 230), -1)
    cv2.putText(img, "BARCODE: 8901234567890", (40, 505), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)

    cv2.imwrite(output_path, img)
    return output_path


def main():
    if len(sys.argv) > 1 and sys.argv[1].strip():
        image_path = sys.argv[1].strip()
        if not os.path.exists(image_path):
            print(f"ERROR: Image file not found: {image_path}")
            sys.exit(1)
        generated = False
    else:
        image_path = create_synthetic_product_label("sample_label.jpg")
        generated = True
        print(f"Generated synthetic test label image: {image_path}")

    print("\n" + "=" * 50)
    print("Sending image to PaddleOCR microservice...")
    print(f"Endpoint: {OCR_SERVICE_URL}/process")
    print(f"File: {image_path}")
    print("=" * 50)

    with open(image_path, "rb") as f:
        file_bytes = f.read()

    files = [("images", (os.path.basename(image_path), file_bytes, "image/jpeg"))]
    data = {"scan_id": f"cli_test_{int(cv2.getTickCount())}", "category": "food"}

    try:
        resp = requests.post(f"{OCR_SERVICE_URL}/process", data=data, files=files, timeout=180.0)
    except requests.exceptions.ConnectionError:
        print(f"\n[ERROR] Connection failed to {OCR_SERVICE_URL}.")
        print("Please start the PaddleOCR microservice first with:")
        print("    python -m uvicorn ml_services.ocr_stub.ocr:app --host 0.0.0.0 --port 8001")
        sys.exit(1)

    print(f"HTTP Status Code: {resp.status_code}")
    if resp.status_code != 200:
        print(f"Response Error: {resp.text}")
        sys.exit(1)

    result = resp.json()

    print("\n--- OCR Processing Results ---")
    print(f"Scan ID: {result.get('scan_id')}")
    print(f"Barcode: {result.get('barcode', 'None detected')}")
    print(f"Scale Factor: {result.get('scale_factor_mm_per_px')} mm/px")

    timings = result.get("timings_ms", {})
    print(f"Timings: OCR = {timings.get('ocr_ms', 0)}ms, Total = {timings.get('total_ms', 0)}ms")

    print("\n--- Extracted Legal Metrology Fields ---")
    fields = result.get("extracted_fields", [])
    if not fields:
        print("  (No fields extracted)")
    else:
        for f in fields:
            ft = f.get("field_type")
            val = f.get("value")
            conf = f.get("confidence")
            font_mm = f.get("font_size_mm")
            zone = f.get("placement_zone")
            font_str = f"{font_mm} mm" if font_mm is not None else "N/A"
            print(f"  * {ft:<25}: {val}")
            print(f"    [Conf: {conf:.2f} | Font: {font_str} | Zone: {zone}]")

    print("\n--- Detected Words Count ---")
    words = result.get("all_words", [])
    print(f"Total tokens recognized: {len(words)}")
    for w in words[:10]:
        print(f"  - '{w.get('text')}' (conf: {w.get('confidence')})")
    if len(words) > 10:
        print(f"  ... and {len(words) - 10} more words")

    print("\n--- Raw Consolidated OCR Text ---")
    raw = result.get("raw_text") or ""
    print(raw[:400] + ("..." if len(raw) > 400 else ""))

    warnings = result.get("warnings", [])
    if warnings:
        print("\n--- Warnings ---")
        for w in warnings:
            print(f"  [!] {w}")

    print("\n==================================================")
    print("SUCCESS: Real OCR extraction test complete.")
    print("==================================================")

    # Cleanup generated sample if created
    if generated and os.path.exists(image_path):
        try:
            os.remove(image_path)
        except OSError:
            pass


if __name__ == "__main__":
    main()
