"""
FastAPI OCR/CV Stub Service.
Implements fixed contract per 03_Backend_Specification.md §OCR Stub Contract.
Runs on port 8001.
"""
from typing import List, Optional
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="Legal Metrology OCR Stub Service", version="1.0.0")


class ProcessRequest(BaseModel):
    scan_id: Optional[str] = None
    image_urls: List[str] = []
    category: Optional[str] = "general"


class ExtractedFieldItem(BaseModel):
    field_type: str
    value: str
    confidence: float
    font_size_mm: Optional[float] = None
    placement_zone: Optional[str] = None


class ProcessResponse(BaseModel):
    extracted_fields: List[ExtractedFieldItem]
    barcode: Optional[str] = None
    quality_flags: List[str] = []


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "ocr_stub"}


@app.post("/process", response_model=ProcessResponse)
def process_scan(req: ProcessRequest):
    category = (req.category or "general").lower()

    # Base extracted fields plausible for demo
    fields = [
        ExtractedFieldItem(
            field_type="manufacturer_name",
            value="Heritage Foods Ltd.",
            confidence=0.95,
            font_size_mm=3.5,
            placement_zone="declaration_panel",
        ),
        ExtractedFieldItem(
            field_type="manufacturer_address",
            value="Plot 12, Industrial Area, Pune, Maharashtra 411018",
            confidence=0.91,
            font_size_mm=2.5,
            placement_zone="declaration_panel",
        ),
        ExtractedFieldItem(
            field_type="product_name",
            value="Pure Desi Ghee",
            confidence=0.96,
            font_size_mm=5.0,
            placement_zone="principal_display_panel",
        ),
        ExtractedFieldItem(
            field_type="net_quantity",
            value="500 ml",
            confidence=0.92,
            font_size_mm=3.0,
            placement_zone="principal_display_panel",
        ),
        ExtractedFieldItem(
            field_type="mrp",
            value="₹349.00 (Incl. of all taxes)",
            confidence=0.94,
            font_size_mm=3.2,
            placement_zone="declaration_panel",
        ),
        ExtractedFieldItem(
            field_type="unit_sale_price",
            value="₹0.70 / ml",
            confidence=0.89,
            font_size_mm=2.2,
            placement_zone="declaration_panel",
        ),
        ExtractedFieldItem(
            field_type="mfg_date",
            value="01/2026",
            confidence=0.90,
            font_size_mm=2.8,
            placement_zone="declaration_panel",
        ),
        ExtractedFieldItem(
            field_type="consumer_care_details",
            value="Careline: 1800-111-222, email: care@heritage.com",
            confidence=0.88,
            font_size_mm=2.0,
            placement_zone="declaration_panel",
        ),
    ]

    # Add category-specific extracted fields
    if category == "food":
        fields.append(
            ExtractedFieldItem(
                field_type="fssai_license_no",
                value="10015022003344",
                confidence=0.93,
                font_size_mm=2.2,
                placement_zone="declaration_panel",
            )
        )
        fields.append(
            ExtractedFieldItem(
                field_type="best_before_date",
                value="09/2026",
                confidence=0.91,
                font_size_mm=2.5,
                placement_zone="declaration_panel",
            )
        )
    elif category == "import":
        fields.append(
            ExtractedFieldItem(
                field_type="country_of_origin",
                value="Japan",
                confidence=0.94,
                font_size_mm=2.5,
                placement_zone="declaration_panel",
            )
        )

    return ProcessResponse(
        extracted_fields=fields,
        barcode="8901234567890",
        quality_flags=[],
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
