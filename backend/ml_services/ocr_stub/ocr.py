# Legal Metrology OCR Microservice & Web Interface
# Dependencies:
# fastapi>=0.100.0
# uvicorn[standard]>=0.23.0
# pydantic>=2.0.0
# opencv-python>=4.8.0
# numpy>=1.24.0
# python-doctr[torch]>=0.7.0
# pyzbar>=0.1.9
# gliner>=0.1.7

import os
import re
import time
import base64
import logging
import math
from typing import List, Optional, Tuple, Dict, Any
from contextlib import asynccontextmanager

import cv2
import numpy as np
from fastapi import FastAPI, HTTPException, Request, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator
from starlette.concurrency import run_in_threadpool

from doctr.models import ocr_predictor
from pyzbar import pyzbar
from gliner import GLiNER

# ==========================================
# CONFIGURATION & CONSTANTS
# ==========================================
STANDARD_MODULE_WIDTH_MM = float(os.getenv("STANDARD_MODULE_WIDTH_MM", "0.33"))
DEVICE = os.getenv("DEVICE", "cpu")  # "cpu" or "cuda"
GLINER_MODEL_NAME = os.getenv("GLINER_MODEL_NAME", "urchade/gliner_base")

LEGAL_METROLOGY_FIELDS = [
    "mrp", "net_quantity", "mfg_date", "expiry_date", "best_before",
    "address", "fssai_license", "unit_sale_price", "consumer_care",
    "country_of_origin", "batch_number", "commodity_name"
]

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s"
)
logger = logging.getLogger("legal_metrology_ocr")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")
SAMPLES_DIR = os.path.join(BASE_DIR, "samples")

os.makedirs(STATIC_DIR, exist_ok=True)
os.makedirs(TEMPLATES_DIR, exist_ok=True)
os.makedirs(SAMPLES_DIR, exist_ok=True)


# ==========================================
# PYDANTIC CONTRACTS
# ==========================================
class ExtractedField(BaseModel):
    field_type: str
    extracted_value: str
    confidence_score: float
    font_size_mm: Optional[float] = None
    placement_zone: str = "unknown"
    bbox_px: Optional[List[int]] = None  # [x_min, y_min, x_max, y_max]

class DetectedWord(BaseModel):
    text: str
    confidence: float
    bbox_px: List[int]
    font_size_mm: Optional[float] = None

class OCRRequest(BaseModel):
    scan_id: str = Field(default_factory=lambda: f"scan_{int(time.time()*1000)}")
    image_base64: str

    @field_validator("image_base64")
    @classmethod
    def validate_image_base64(cls, v: str) -> str:
        # Strip Data URL header prefix if present (e.g. "data:image/jpeg;base64,")
        if "," in v:
            v = v.split(",", 1)[1]
        v = v.strip()
        # Ensure correct base64 padding
        padded = v + "=" * ((4 - len(v) % 4) % 4)
        try:
            base64.b64decode(padded)
        except Exception as e:
            raise ValueError(f"Provided string is not valid base64: {e}")
        return padded

class OCRResponse(BaseModel):
    scan_id: str
    image_dimensions: Optional[Dict[str, int]] = None
    fields: List[ExtractedField]
    scale_factor_mm_per_px: Optional[float] = None
    barcode_detected: bool = False
    barcode_info: Optional[Dict[str, Any]] = None
    raw_text: Optional[str] = None
    all_words: Optional[List[DetectedWord]] = []
    warnings: List[str] = []
    timings_ms: Optional[Dict[str, float]] = None


# ==========================================
# FASTAPI LIFESPAN
# ==========================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing ML models on device: %s...", DEVICE)
    try:
        # Load docTR OCR predictor
        app.state.doctr_model = ocr_predictor(pretrained=True).to(DEVICE)
        logger.info("docTR initialized successfully.")
        
        # Load GLiNER entity extraction model
        app.state.gliner_model = GLiNER.from_pretrained(GLINER_MODEL_NAME).to(DEVICE)
        logger.info("GLiNER initialized successfully.")
    except Exception as e:
        logger.critical(f"Failed to load ML models: {e}")
        raise RuntimeError(f"Model loading failed: {e}") from e
        
    yield
    logger.info("Shutting down service.")


app = FastAPI(
    title="Legal Metrology Vision OCR Microservice",
    description="End-to-End Packaged Commodity Vision Verification Pipeline: Webcam -> Image -> docTR OCR -> pyzbar Calibration -> GLiNER NER -> Output",
    lifespan=lifespan
)

# Enable CORS for browser integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


# ==========================================
# PIPELINE FUNCTIONS
# ==========================================
def preprocess_image(b64_string: str) -> np.ndarray:
    """Decodes base64 string (with or without data URL header) to a valid OpenCV BGR image."""
    if "," in b64_string:
        b64_string = b64_string.split(",", 1)[1]
    b64_string = b64_string.strip()
    padded = b64_string + "=" * ((4 - len(b64_string) % 4) % 4)
    
    img_bytes = base64.b64decode(padded)
    np_arr = np.frombuffer(img_bytes, np.uint8)
    image = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
    
    if image is None or image.size == 0:
        raise ValueError("Decoded byte array could not be interpreted as an image.")
    return image


def calibrate_mm_per_pixel(image: np.ndarray) -> Tuple[Optional[float], Optional[Dict[str, Any]], List[str]]:
    """
    Calculates physical scale (mm per pixel) using a detected barcode.
    Returns (mm_per_pixel, barcode_info, warnings).
    """
    warnings = []
    try:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        decoded = pyzbar.decode(gray)
        
        # Fallback: if no barcode found on raw grayscale, try CLAHE contrast enhancement
        if not decoded:
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            enhanced = clahe.apply(gray)
            decoded = pyzbar.decode(enhanced)
        
        if not decoded:
            return None, None, ["No barcode detected for physical scale calibration."]
            
        barcode = decoded[0]
        x, y, w, h = barcode.rect
        barcode_type = str(barcode.type)
        barcode_data = barcode.data.decode("utf-8", errors="ignore")
        
        barcode_info = {
            "type": barcode_type,
            "data": barcode_data,
            "rect": [int(x), int(y), int(w), int(h)],
            "module_px": None
        }
        
        margin = 5
        x_min, y_min = max(0, x - margin), max(0, y - margin)
        x_max, y_max = min(gray.shape[1], x + w + margin), min(gray.shape[0], y + h + margin)
        crop = gray[y_min:y_max, x_min:x_max]
        
        if crop.size == 0 or crop.shape[0] < 10 or crop.shape[1] < 10:
            return None, barcode_info, ["Degenerate or small barcode crop."]

        # Inverted Otsu Thresholding (bars become white / 255)
        _, crop_thresh = cv2.threshold(crop, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)
        h_crop, w_crop = crop_thresh.shape
        
        y_center = h_crop // 2
        strip = crop_thresh[max(0, y_center - 2):min(h_crop, y_center + 3), :]
        
        # Robust scanline using median across strip
        scanline = np.median(strip, axis=0)
        
        # Keep center 40% (discard outer margins)
        start_idx = int(w_crop * 0.3)
        end_idx = int(w_crop * 0.7)
        if start_idx >= end_idx:
            center_scanline = scanline
        else:
            center_scanline = scanline[start_idx:end_idx]
        
        # Find runs of black/white bars
        runs = []
        current_run = 0
        for val in center_scanline:
            if val >= 128:  # thresholded binary bar
                current_run += 1
            elif current_run > 0:
                runs.append(current_run)
                current_run = 0
        if current_run > 0:
            runs.append(current_run)
            
        # Filter anti-aliasing / subpixel noise
        valid_runs = [r for r in runs if r >= 2]
        
        if not valid_runs:
            # Fallback: estimate from total width divided by standard module count (~95 for EAN-13, ~100 for Code128)
            est_modules = 95 if "EAN" in barcode_type or "UPC" in barcode_type else 110
            estimated_module_px = max(1.0, w / est_modules)
            mm_per_pixel = STANDARD_MODULE_WIDTH_MM / estimated_module_px
            barcode_info["module_px"] = round(float(estimated_module_px), 2)
            return round(float(mm_per_pixel), 6), barcode_info, ["Scale estimated from total barcode geometry."]
            
        module_width_px = min(valid_runs)
        barcode_info["module_px"] = round(float(module_width_px), 2)
        mm_per_pixel = STANDARD_MODULE_WIDTH_MM / module_width_px
        
        return round(float(mm_per_pixel), 6), barcode_info, []
        
    except Exception as e:
        logger.error(f"Barcode calibration exception: {e}")
        return None, None, [f"Barcode calibration error: {e}"]


def extract_words_doctr(predictor, image: np.ndarray) -> Tuple[List[Dict[str, Any]], str]:
    """Runs docTR on the image and returns words with bounding boxes and reconstructed full text."""
    height, width = image.shape[:2]
    rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    
    result = predictor([rgb_image])
    
    words_data = []
    lines_text = []
    
    for page in result.pages:
        for block in page.blocks:
            for line in block.lines:
                line_words = []
                for word in line.words:
                    if not word.value.strip():
                        continue
                    (x_min_rel, y_min_rel), (x_max_rel, y_max_rel) = word.geometry
                    bbox_px = [
                        int(round(x_min_rel * width)),
                        int(round(y_min_rel * height)),
                        int(round(x_max_rel * width)),
                        int(round(y_max_rel * height))
                    ]
                    words_data.append({
                        "text": word.value,
                        "confidence": float(word.confidence),
                        "bbox_px": bbox_px
                    })
                    line_words.append(word.value)
                if line_words:
                    lines_text.append(" ".join(line_words))
                    
    full_text = "\n".join(lines_text) if lines_text else ""
    return words_data, full_text


def compute_font_size_mm(bbox_px: List[int], mm_per_pixel: Optional[float]) -> Optional[float]:
    """Computes real-world font height in millimeters using bounding box height."""
    if mm_per_pixel is None:
        return None
    _, y_min, _, y_max = bbox_px
    height_px = max(1, y_max - y_min)
    return round(height_px * mm_per_pixel, 2)


def supplement_heuristic_fields(
    gliner_input_text: str, 
    words_data: List[Dict[str, Any]], 
    existing_fields: List[ExtractedField],
    mm_per_pixel: Optional[float]
) -> List[ExtractedField]:
    """
    Supplements zero-shot GLiNER extractions with regex-based Legal Metrology pattern detectors.
    Uses character offsets for bounding box accuracy.
    """
    supplemented = list(existing_fields)
    existing_types = {f.field_type for f in existing_fields}
    existing_values = {f.extracted_value.lower() for f in existing_fields}

    def get_bbox_for_span(start_c: int, end_c: int):
        matched = [w for w in words_data if w.get("start_char", 0) < end_c and w.get("end_char", 0) > start_c]
        if not matched:
            return None, None
        bbox = [
            min(w["bbox_px"][0] for w in matched),
            min(w["bbox_px"][1] for w in matched),
            max(w["bbox_px"][2] for w in matched),
            max(w["bbox_px"][3] for w in matched)
        ]
        fs = compute_font_size_mm(bbox, mm_per_pixel)
        return bbox, fs

    # 1. FSSAI License Pattern (14 digits)
    if "fssai_license" not in existing_types or not any(re.search(r'\d{14}', f.extracted_value) for f in existing_fields if f.field_type == "fssai_license"):
        fssai_match = re.search(r'(?:fssai|lic(?:\.|\s+)?no(?:\.|\s+)?)\s*[:\-]?\s*([0-9]{14})', gliner_input_text, re.IGNORECASE)
        if not fssai_match:
            fssai_match = re.search(r'\b(1[0-9]{13})\b', gliner_input_text)
            
        if fssai_match:
            val = fssai_match.group(0)
            if val.lower() not in existing_values:
                bbox, fs = get_bbox_for_span(fssai_match.start(), fssai_match.end())
                supplemented.append(ExtractedField(
                    field_type="fssai_license",
                    extracted_value=val,
                    confidence_score=0.98,
                    font_size_mm=fs,
                    bbox_px=bbox
                ))

    # 2. MRP Pattern (Rs. / ₹ / INR)
    if "mrp" not in existing_types:
        mrp_match = re.search(r'(?:MRP|M\.R\.P\.?)\s*[:\-]?\s*(?:Rs\.?|INR|₹)?\s*([0-9]+(?:\.[0-9]{1,2})?)', gliner_input_text, re.IGNORECASE)
        if mrp_match:
            val = mrp_match.group(0)
            if val.lower() not in existing_values:
                bbox, fs = get_bbox_for_span(mrp_match.start(), mrp_match.end())
                supplemented.append(ExtractedField(
                    field_type="mrp",
                    extracted_value=val,
                    confidence_score=0.92,
                    font_size_mm=fs,
                    bbox_px=bbox
                ))

    # 3. Consumer Care Helpline / Phone / Email
    if "consumer_care" not in existing_types:
        care_match = re.search(r'(?:1800[\s\-]?\d{3,4}[\s\-]?\d{3,4}|\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b)', gliner_input_text)
        if care_match:
            val = care_match.group(0)
            bbox, fs = get_bbox_for_span(care_match.start(), care_match.end())
            supplemented.append(ExtractedField(
                field_type="consumer_care",
                extracted_value=val,
                confidence_score=0.90,
                font_size_mm=fs,
                bbox_px=bbox
            ))

    return supplemented


def classify_fields_gliner(
    gliner_model, 
    words_data: List[Dict[str, Any]], 
    full_text: str,
    mm_per_pixel: Optional[float]
) -> List[ExtractedField]:
    """Uses GLiNER over OCR text to classify Legal Metrology entities and links them back to physical coordinates."""
    if not words_data:
        return []

    # 1. Join tokens and compute exact character offsets
    text_parts = []
    char_idx = 0
    for w in words_data:
        text_parts.append(w["text"])
        w["start_char"] = char_idx
        w["end_char"] = char_idx + len(w["text"])
        char_idx += len(w["text"]) + 1  # space
        
    gliner_input_text = " ".join(text_parts)
    
    # 2. GLiNER zero-shot entity prediction
    entities = gliner_model.predict_entities(gliner_input_text, LEGAL_METROLOGY_FIELDS)
    
    # 3. Map entities back to word coordinates
    extracted_fields = []
    for ent in entities:
        ent_start, ent_end = ent["start"], ent["end"]
        
        intersecting_words = [
            w for w in words_data 
            if w["start_char"] < ent_end and w["end_char"] > ent_start
        ]
        
        if not intersecting_words:
            continue
            
        total_ocr_conf = sum(w["confidence"] for w in intersecting_words)
        avg_ocr_conf = total_ocr_conf / len(intersecting_words)
        combined_conf = math.sqrt(max(0.0, avg_ocr_conf * ent["score"]))
        
        # Encompassing bounding box in pixels [x_min, y_min, x_max, y_max]
        x_min = min(w["bbox_px"][0] for w in intersecting_words)
        y_min = min(w["bbox_px"][1] for w in intersecting_words)
        x_max = max(w["bbox_px"][2] for w in intersecting_words)
        y_max = max(w["bbox_px"][3] for w in intersecting_words)
        entity_bbox = [x_min, y_min, x_max, y_max]
        
        font_size_mm = compute_font_size_mm(entity_bbox, mm_per_pixel)
        
        extracted_fields.append(ExtractedField(
            field_type=ent["label"],
            extracted_value=ent["text"],
            confidence_score=round(float(combined_conf), 4),
            font_size_mm=font_size_mm,
            placement_zone="unknown",
            bbox_px=entity_bbox
        ))
        
    # 4. Supplement with regex heuristics for missing mandatory declarations
    final_fields = supplement_heuristic_fields(gliner_input_text, words_data, extracted_fields, mm_per_pixel)
    return final_fields


def process_image_pipeline(
    image: np.ndarray, 
    scan_id: str, 
    doctr_model, 
    gliner_model
) -> OCRResponse:
    """Complete end-to-end Legal Metrology Vision Pipeline."""
    t_start = time.time()
    logger.info(f"[{scan_id}] Starting OCR pipeline on image shape {image.shape}.")
    warnings = []
    
    height, width = image.shape[:2]
    
    # 1. Barcode Calibration
    t_cal0 = time.time()
    mm_per_pixel, barcode_info, cal_warnings = calibrate_mm_per_pixel(image)
    t_cal = round((time.time() - t_cal0) * 1000, 2)
    if cal_warnings:
        warnings.extend(cal_warnings)
    
    # 2. OCR (docTR)
    t_ocr0 = time.time()
    words_data, full_text = extract_words_doctr(doctr_model, image)
    t_ocr = round((time.time() - t_ocr0) * 1000, 2)
    
    if not words_data:
        warnings.append("No text detected in image.")
        return OCRResponse(
            scan_id=scan_id,
            image_dimensions={"width": width, "height": height},
            fields=[],
            scale_factor_mm_per_px=mm_per_pixel,
            barcode_detected=barcode_info is not None,
            barcode_info=barcode_info,
            raw_text="",
            all_words=[],
            warnings=warnings,
            timings_ms={"calibration": t_cal, "ocr": t_ocr, "ner": 0, "total": round((time.time() - t_start) * 1000, 2)}
        )
        
    # 3. Entity Classification (GLiNER + Metrology Heuristics)
    t_ner0 = time.time()
    fields = classify_fields_gliner(gliner_model, words_data, full_text, mm_per_pixel)
    t_ner = round((time.time() - t_ner0) * 1000, 2)
    
    # Prepare all_words output
    detected_words = [
        DetectedWord(
            text=w["text"],
            confidence=round(w["confidence"], 4),
            bbox_px=w["bbox_px"],
            font_size_mm=compute_font_size_mm(w["bbox_px"], mm_per_pixel)
        )
        for w in words_data
    ]
    
    t_total = round((time.time() - t_start) * 1000, 2)
    logger.info(f"[{scan_id}] Pipeline completed in {t_total}ms. Extracted {len(fields)} fields.")
    
    return OCRResponse(
        scan_id=scan_id,
        image_dimensions={"width": width, "height": height},
        fields=fields,
        scale_factor_mm_per_px=mm_per_pixel,
        barcode_detected=barcode_info is not None,
        barcode_info=barcode_info,
        raw_text=full_text,
        all_words=detected_words,
        warnings=warnings,
        timings_ms={
            "calibration_ms": t_cal,
            "ocr_ms": t_ocr,
            "ner_ms": t_ner,
            "total_ms": t_total
        }
    )


# ==========================================
# API & FRONTEND ROUTES
# ==========================================
@app.get("/", response_class=HTMLResponse)
async def serve_demo_ui():
    """Serves the interactive Webcam OCR Metrology demo frontend."""
    index_path = os.path.join(TEMPLATES_DIR, "index.html")
    if os.path.exists(index_path):
        with open(index_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(content="<h1>Legal Metrology Vision OCR Service Ready</h1><p>Visit /health or POST /extract</p>")


@app.get("/health")
async def health_check(request: Request):
    """Health check endpoint returning model statuses and hardware info."""
    doctr_loaded = hasattr(request.app.state, "doctr_model")
    gliner_loaded = hasattr(request.app.state, "gliner_model")
    
    status = "healthy" if (doctr_loaded and gliner_loaded) else "initializing"
    return {
        "status": status,
        "device": DEVICE,
        "models": {
            "doctr_loaded": doctr_loaded,
            "gliner_loaded": gliner_loaded,
            "gliner_model_name": GLINER_MODEL_NAME
        }
    }


@app.post("/extract", response_model=OCRResponse)
async def extract_info(request: OCRRequest, req: Request):
    """
    Main extraction endpoint.
    Takes a base64 encoded image (with or without data URI header), performs OCR, 
    spatial scale calibration via barcode, and extracts structured legal metrology fields.
    """
    try:
        image = preprocess_image(request.image_base64)
    except ValueError as e:
        logger.error(f"[{request.scan_id}] Image decode failed: {e}")
        raise HTTPException(status_code=422, detail=str(e))
        
    response = await run_in_threadpool(
        process_image_pipeline,
        image,
        request.scan_id,
        req.app.state.doctr_model,
        req.app.state.gliner_model
    )
    return response


@app.post("/extract-file", response_model=OCRResponse)
async def extract_info_file(req: Request, file: UploadFile = File(...)):
    """Endpoint for direct multipart file upload."""
    contents = await file.read()
    np_arr = np.frombuffer(contents, np.uint8)
    image = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
    
    if image is None or image.size == 0:
        raise HTTPException(status_code=422, detail="Uploaded file is not a valid image.")
        
    scan_id = f"file_{int(time.time()*1000)}"
    response = await run_in_threadpool(
        process_image_pipeline,
        image,
        scan_id,
        req.app.state.doctr_model,
        req.app.state.gliner_model
    )
    return response


@app.get("/samples/{filename}")
async def get_sample_image(filename: str):
    """Serves bundled test sample images."""
    file_path = os.path.join(SAMPLES_DIR, filename)
    if os.path.exists(file_path):
        return FileResponse(file_path)
    raise HTTPException(status_code=404, detail="Sample image not found.")


@app.get("/api/samples")
async def list_sample_images():
    """Lists available sample test images."""
    if not os.path.exists(SAMPLES_DIR):
        return []
    return [f for f in os.listdir(SAMPLES_DIR) if f.endswith(('.png', '.jpg', '.jpeg'))]


# ==========================================
# RUNTIME ENTRY POINT
# ==========================================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)