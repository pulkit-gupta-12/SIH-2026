# Legal Metrology OCR Microservice – PaddleOCR Backend
# =====================================================
# Production-ready OCR microservice for packaged commodity compliance
# Port: 8001
# =====================================================

import os
import re
import time
import base64
import logging
import math
import asyncio
import importlib
from typing import List, Optional, Tuple, Dict, Any, Union
from contextlib import asynccontextmanager

import cv2
import numpy as np
from fastapi import FastAPI, HTTPException, Request, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from starlette.concurrency import run_in_threadpool

# Ensure torch is imported before paddle on Windows to avoid DLL loading issues
try:
    import torch
except Exception:
    pass

try:
    from paddleocr import PaddleOCR
except Exception as exc:
    PaddleOCR = None
    PADDLE_IMPORT_ERROR = exc
else:
    PADDLE_IMPORT_ERROR = None

# Optional pyzbar for fallback barcode detection
try:
    from pyzbar import pyzbar
    PYZBAR_AVAILABLE = True
except Exception:
    pyzbar = None
    PYZBAR_AVAILABLE = False

# Optional GLiNER zero-shot entity extraction
try:
    GLiNER = getattr(importlib.import_module("gliner"), "GLiNER")
    GLINER_AVAILABLE = True
except Exception:
    GLiNER = None
    GLINER_AVAILABLE = False

# ==========================================
# CONFIGURATION (via environment variables)
# ==========================================
STANDARD_MODULE_WIDTH_MM = float(os.getenv("STANDARD_MODULE_WIDTH_MM", "0.33"))
DEVICE = os.getenv("DEVICE", "cpu")                 # "cpu" or "gpu"
GLINER_MODEL_NAME = os.getenv("GLINER_MODEL_NAME", "urchade/gliner_base")
PADDLE_LANG = os.getenv("PADDLE_LANG", "en")        # e.g., "en", "hi", "en,hi"
OCR_CONFIDENCE_THRESHOLD = float(os.getenv("OCR_CONFIDENCE_THRESHOLD", "0.4"))
MAX_IMAGES_PER_REQUEST = int(os.getenv("MAX_IMAGES_PER_REQUEST", "10"))
MAX_IMAGE_SIZE_BYTES = int(os.getenv("MAX_IMAGE_SIZE_BYTES", str(20 * 1024 * 1024)))  # 20MB
PORT = int(os.getenv("PORT", "8001"))

LEGAL_METROLOGY_FIELDS = [
    "mrp", "net_quantity", "mfg_date", "expiry_date", "best_before_date",
    "manufacturer_name", "manufacturer_address", "consumer_care_details",
    "unit_sale_price", "fssai_license_no", "country_of_origin",
    "batch_number", "commodity_name"
]

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s"
)
logger = logging.getLogger("legal_metrology_ocr")


# ==========================================
# PYDANTIC MODELS
# ==========================================
class ExtractedFieldItem(BaseModel):
    field_type: str
    value: str
    confidence: float
    extracted_value: Optional[str] = None
    confidence_score: Optional[float] = None
    font_size_mm: Optional[float] = None
    placement_zone: Optional[str] = "unknown"
    bbox_px: Optional[List[int]] = None  # [x_min, y_min, x_max, y_max]

    def model_post_init(self, __context: Any) -> None:
        if self.extracted_value is None:
            self.extracted_value = self.value
        if self.confidence_score is None:
            self.confidence_score = self.confidence


class DetectedWord(BaseModel):
    text: str
    confidence: float
    bbox_px: List[int]
    font_size_mm: Optional[float] = None


class ProcessResponse(BaseModel):
    scan_id: Optional[str] = None
    extracted_fields: List[ExtractedFieldItem]
    barcode: Optional[str] = None
    quality_flags: List[str] = []
    raw_text: Optional[str] = None
    all_words: Optional[List[DetectedWord]] = []
    image_dimensions: Optional[Dict[str, int]] = None
    scale_factor_mm_per_px: Optional[float] = None
    barcode_info: Optional[Dict[str, Any]] = None
    warnings: List[str] = []
    timings_ms: Optional[Dict[str, float]] = None


class OCRRequest(BaseModel):
    scan_id: Optional[str] = Field(default_factory=lambda: f"scan_{int(time.time()*1000)}")
    image_base64: Optional[Union[List[str], str]] = None
    image_urls: Optional[List[str]] = None
    category: Optional[str] = "general"


ENABLE_GLINER = os.getenv("ENABLE_GLINER", "false").lower() in ("true", "1", "yes")

# ==========================================
# FASTAPI LIFESPAN
# ==========================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initialising PaddleOCR on device: %s, lang: %s", DEVICE, PADDLE_LANG)
    if PaddleOCR is None:
        raise RuntimeError(
            "PaddleOCR cannot start because its runtime is unavailable. "
            "Install a supported PaddlePaddle build for this Python environment. "
            f"Original error: {PADDLE_IMPORT_ERROR}"
        )

    try:
        # Keep model construction compatible with PaddleOCR 3.x and CPU execution on Windows.
        app.state.ocr_model = PaddleOCR(
            lang=PADDLE_LANG,
            use_doc_orientation_classify=False,
            use_doc_unwarping=False,
            use_textline_orientation=False,
            text_recognition_batch_size=8,
            device=DEVICE,
            enable_mkldnn=False,
        )
        logger.info("PaddleOCR loaded successfully into memory.")
    except Exception as e:
        logger.critical("Failed to initialize PaddleOCR: %s", e)
        raise RuntimeError(f"PaddleOCR startup failure: {e}") from e

    # Optional zero-shot GLiNER (disabled by default for fast offline startup)
    if ENABLE_GLINER and GLINER_AVAILABLE and GLiNER is not None:
        try:
            logger.info("Loading GLiNER model: %s", GLINER_MODEL_NAME)
            app.state.gliner_model = GLiNER.from_pretrained(GLINER_MODEL_NAME).to(DEVICE)
            logger.info("GLiNER loaded successfully.")
        except Exception as e:
            logger.warning("GLiNER model loading skipped or failed: %s (will use regex extractors)", e)
            app.state.gliner_model = None
    else:
        app.state.gliner_model = None

    yield
    logger.info("Shutting down Legal Metrology OCR service.")



app = FastAPI(
    title="Legal Metrology Vision OCR Service (PaddleOCR)",
    description="Real image OCR + Legal Metrology packaged commodity field extraction + barcode physical calibration",
    version="2.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==========================================
# IMAGE DECODING & VALIDATION HELPERS
# ==========================================
def decode_image_bytes(data: bytes, filename: str = "upload") -> np.ndarray:
    """Validate and decode image raw bytes to OpenCV BGR image, auto-downscaling for fast inference."""
    if not data or len(data) == 0:
        raise ValueError(f"Empty image file: '{filename}'")
    if len(data) > MAX_IMAGE_SIZE_BYTES:
        raise ValueError(f"Image '{filename}' exceeds maximum allowed size ({len(data)} > {MAX_IMAGE_SIZE_BYTES} bytes)")

    np_arr = np.frombuffer(data, np.uint8)
    image = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
    if image is None or image.size == 0:
        raise ValueError(f"Could not decode image '{filename}'. Supported formats: JPEG, PNG, WEBP.")

    # High-resolution smartphone camera optimization:
    # Downscale image if larger than 1600px on any side to prevent slow OCR on CPU.
    MAX_DIM = 1600
    h, w = image.shape[:2]
    if max(h, w) > MAX_DIM:
        scale = MAX_DIM / float(max(h, w))
        new_w, new_h = max(1, int(w * scale)), max(1, int(h * scale))
        image = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_AREA)

    return image


def decode_base64_image(b64_string: str) -> np.ndarray:
    """Decode base64 string or data URL to OpenCV BGR image."""
    if "," in b64_string:
        b64_string = b64_string.split(",", 1)[1]
    b64_string = b64_string.strip()
    padded = b64_string + "=" * ((4 - len(b64_string) % 4) % 4)

    try:
        img_bytes = base64.b64decode(padded)
    except Exception as e:
        raise ValueError(f"Invalid base64 encoding: {e}")
    return decode_image_bytes(img_bytes, "base64_data")


# ==========================================
# BARCODE & SCALE CALIBRATION
# ==========================================
def calibrate_mm_per_pixel(image: np.ndarray) -> Tuple[Optional[float], Optional[Dict[str, Any]], Optional[str], List[str]]:
    """
    Detect barcode and compute pixel-to-mm scale using standard module width.
    Returns (mm_per_pixel, barcode_info, barcode_str, warnings).
    """
    warnings = []
    barcode_info = None
    barcode_str = None
    mm_per_pixel = None

    try:
        # 1. Try OpenCV BarcodeDetector
        detector = cv2.barcode.BarcodeDetector()
        res: Any = detector.detectAndDecode(image)
        retval = False
        decoded_info = []
        decoded_type = []
        points = None
        if len(res) == 4:
            retval, decoded_info, decoded_type, points = res
        elif len(res) == 3:
            decoded_info, points, decoded_type = res
            retval = bool(points is not None and decoded_info and len(decoded_info) > 0 and decoded_info[0])

        if retval and decoded_info and len(decoded_info) > 0 and decoded_info[0]:
            barcode_str = str(decoded_info[0]).strip()
            barcode_type = str(decoded_type[0]) if decoded_type else "UNKNOWN"
            if points is None or len(points) == 0:
                raise ValueError("Barcode detected without geometry points")
            pts = points[0]
            x_coords = [p[0] for p in pts]
            y_coords = [p[1] for p in pts]
            x_min, x_max = int(min(x_coords)), int(max(x_coords))
            y_min, y_max = int(min(y_coords)), int(max(y_coords))
            w = max(1, x_max - x_min)
            h = max(1, y_max - y_min)

            barcode_info = {
                "type": barcode_type,
                "data": barcode_str,
                "rect": [x_min, y_min, w, h],
                "module_px": None
            }

            est_modules = 95 if ("EAN" in barcode_type or "UPC" in barcode_type or len(barcode_str) in (8, 12, 13)) else 110
            module_px = max(1.0, w / est_modules)
            mm_per_pixel = round(float(STANDARD_MODULE_WIDTH_MM / module_px), 6)
            barcode_info["module_px"] = round(float(module_px), 2)
            return mm_per_pixel, barcode_info, barcode_str, warnings

        # 2. Try pyzbar fallback if available
        if PYZBAR_AVAILABLE and pyzbar is not None:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            decoded = pyzbar.decode(gray)
            if not decoded:
                clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
                enhanced = clahe.apply(gray)
                decoded = pyzbar.decode(enhanced)

            if decoded:
                b = decoded[0]
                barcode_str = b.data.decode("utf-8", errors="ignore").strip()
                barcode_type = str(b.type)
                x, y, w, h = b.rect
                barcode_info = {
                    "type": barcode_type,
                    "data": barcode_str,
                    "rect": [int(x), int(y), int(w), int(h)],
                    "module_px": None
                }
                est_modules = 95 if ("EAN" in barcode_type or "UPC" in barcode_type or len(barcode_str) in (8, 12, 13)) else 110
                module_px = max(1.0, w / est_modules)
                mm_per_pixel = round(float(STANDARD_MODULE_WIDTH_MM / module_px), 6)
                barcode_info["module_px"] = round(float(module_px), 2)
                return mm_per_pixel, barcode_info, barcode_str, warnings

    except Exception as e:
        logger.warning("Barcode detection error: %s", e)
        warnings.append(f"Barcode detection error: {e}")

    warnings.append("No barcode detected for physical scale calibration; font sizes in mm will be unavailable.")
    return None, None, None, warnings


# ==========================================
# PADDLEOCR TEXT EXTRACTION
# ==========================================
def extract_words_paddle(ocr_model: Any, image: np.ndarray) -> Tuple[List[Dict[str, Any]], str]:
    """
    Run PaddleOCR and return word/line tokens:
        [{"text": str, "confidence": float, "bbox_px": [xmin, ymin, xmax, ymax]}, ...]
    and full consolidated text.
    Handles both PaddleOCR 3.x (predict API) and 2.x (ocr API).
    """
    height, width = image.shape[:2]
    words_data = []
    all_texts = []

    try:
        # PaddleOCR 3.x predict pipeline
        if hasattr(ocr_model, "predict"):
            pred_iter = ocr_model.predict(image)
            for item in pred_iter:
                # PaddleOCR 3.x returns a Result object, while some versions
                # return a plain dictionary.  Normalize both forms here.
                result = item if isinstance(item, dict) else None
                if result is None:
                    try:
                        serialized = getattr(item, "json", None)
                        serialized = serialized() if callable(serialized) else serialized
                        result = serialized if isinstance(serialized, dict) else None
                    except Exception:
                        try:
                            result = dict(item)
                        except Exception:
                            result = None

                if result is not None:
                    texts = result.get("rec_texts") or []
                    scores = result.get("rec_scores") or []
                    boxes = result.get("rec_boxes") if result.get("rec_boxes") is not None else result.get("rec_polys")
                    for idx, text in enumerate(texts):
                        text_str = str(text).strip()
                        if not text_str:
                            continue
                        score = float(scores[idx]) if idx < len(scores) else 0.90
                        if score < OCR_CONFIDENCE_THRESHOLD:
                            continue

                        bbox_px = [0, 0, width, height]
                        if boxes is not None and idx < len(boxes):
                            box = boxes[idx]
                            if hasattr(box, "tolist"):
                                box = box.tolist()
                            if len(box) == 4 and isinstance(box[0], (int, float)):
                                bbox_px = [int(box[0]), int(box[1]), int(box[2]), int(box[3])]
                            elif len(box) >= 4:
                                xs = [p[0] for p in box]
                                ys = [p[1] for p in box]
                                bbox_px = [int(min(xs)), int(min(ys)), int(max(xs)), int(max(ys))]

                        words_data.append({
                            "text": text_str,
                            "confidence": round(score, 4),
                            "bbox_px": bbox_px
                        })
                        all_texts.append(text_str)

        # PaddleOCR 2.x ocr pipeline fallback
        elif hasattr(ocr_model, "ocr"):
            result = ocr_model.ocr(image, cls=True)
            if result and result[0]:
                for line in result[0]:
                    if not line or len(line) < 2:
                        continue
                    bbox, text_conf = line[0], line[1]
                    if not text_conf or len(text_conf) < 2:
                        continue
                    text, conf = text_conf[0], text_conf[1]
                    text_str = str(text).strip()
                    conf_val = float(conf)
                    if not text_str or conf_val < OCR_CONFIDENCE_THRESHOLD:
                        continue
                    xs = [p[0] for p in bbox]
                    ys = [p[1] for p in bbox]
                    bbox_px = [max(0, int(min(xs))), max(0, int(min(ys))), min(width, int(max(xs))), min(height, int(max(ys)))]
                    words_data.append({
                        "text": text_str,
                        "confidence": round(conf_val, 4),
                        "bbox_px": bbox_px
                    })
                    all_texts.append(text_str)

    except Exception as e:
        logger.error("PaddleOCR execution error: %s", e)

    full_text = " \n ".join(all_texts)
    return words_data, full_text



def compute_font_size_mm(bbox_px: Optional[List[int]], mm_per_pixel: Optional[float]) -> Optional[float]:
    if mm_per_pixel is None or bbox_px is None or len(bbox_px) < 4:
        return None
    _, y_min, _, y_max = bbox_px
    height_px = max(1, y_max - y_min)
    return round(height_px * mm_per_pixel, 2)


# ==========================================
# DETERMINISTIC LEGAL METROLOGY FIELD EXTRACTION
# ==========================================
def extract_legal_metrology_fields(
    words_data: List[Dict[str, Any]],
    full_text: str,
    mm_per_pixel: Optional[float] = None
) -> List[ExtractedFieldItem]:
    """
    Deterministic rule-based and regular-expression extraction for Legal Metrology mandatory declarations:
    - mrp
    - net_quantity
    - mfg_date
    - expiry_date
    - best_before_date
    - unit_sale_price
    - fssai_license_no
    - consumer_care_details
    - country_of_origin
    - batch_number
    - manufacturer_name
    - manufacturer_address
    - commodity_name
    """
    if not full_text or not words_data:
        return []

    fields_dict: Dict[str, ExtractedFieldItem] = {}

    # Build indexed text with character positions
    char_pos = 0
    token_spans = []
    for w in words_data:
        t = w["text"]
        start_c = char_pos
        end_c = start_c + len(t)
        token_spans.append((start_c, end_c, w))
        char_pos = end_c + 1  # single space separator
    joined_text = " ".join(w["text"] for w in words_data)

    def find_bbox_and_confidence(start_c: int, end_c: int, default_conf: float = 0.90) -> Tuple[Optional[List[int]], float]:
        overlapping = [
            w for sc, ec, w in token_spans
            if sc < end_c and ec > start_c
        ]
        if not overlapping:
            return None, default_conf
        x_min = min(w["bbox_px"][0] for w in overlapping)
        y_min = min(w["bbox_px"][1] for w in overlapping)
        x_max = max(w["bbox_px"][2] for w in overlapping)
        y_max = max(w["bbox_px"][3] for w in overlapping)
        conf = sum(w["confidence"] for w in overlapping) / len(overlapping)
        return [x_min, y_min, x_max, y_max], round(conf, 4)

    # 1. MRP (Maximum Retail Price)
    # Variations: MRP, M.R.P., Rs, Rs., INR, ₹, Incl. of all taxes
    mrp_regexes = [
        r'(?:M\.?\s*R\.?\s*P\.?|MAX(?:IMUM|\.)?\s*RETAIL\s*PRICE)\s*(?:IS|\:|\-)?\s*(?:Rs\.?|INR|₹)?\s*([0-9]+(?:\.[0-9]{1,2})?)\b(?:\s*\(?(?:incl|inclusive)\.?\s*(?:of)?\s*all\s*taxes\)?)?',
        r'(?:(?:Rs\.?|INR|₹)\s*([0-9]+(?:\.[0-9]{1,2})?))\s*\(?(?:incl|inclusive)\.?\s*(?:of)?\s*all\s*taxes\)?',
        r'\b(?:Rs\.?|INR|₹)\s*([0-9]+(?:\.[0-9]{1,2})?)\b'
    ]
    for pattern in mrp_regexes:
        m = re.search(pattern, joined_text, re.IGNORECASE)
        if m:
            raw_matched = m.group(0).strip()
            bbox, conf = find_bbox_and_confidence(m.start(), m.end(), default_conf=0.92)
            fields_dict["mrp"] = ExtractedFieldItem(
                field_type="mrp",
                value=raw_matched,
                confidence=conf,
                font_size_mm=compute_font_size_mm(bbox, mm_per_pixel),
                placement_zone="declaration_panel",
                bbox_px=bbox
            )
            break

    # 2. Net Quantity
    # Variations: Net Qty, Net Wt, Net Contents, Netto, g, kg, ml, l, mg, pcs
    net_qty_regexes = [
        r'(?:NET\s*(?:QTY|QUANTITY|WT|WEIGHT|CONTENTS?|VOLUME)|NETTO)\s*[:\-]?\s*([0-9]+(?:\.[0-9]+)?\s*(?:kg|g|gm|gms|mg|l|ltr|liter|litres?|ml|piece|pc|pcs|units?|n|number))\b',
        r'\b([0-9]+(?:\.[0-9]+)?\s*(?:kg|g|gm|gms|mg|l|ltr|liter|litres?|ml))\b(?:\s*(?:net\s*wt|when\s*packed))?'
    ]
    for pattern in net_qty_regexes:
        m = re.search(pattern, joined_text, re.IGNORECASE)
        if m:
            val = m.group(0).strip()
            bbox, conf = find_bbox_and_confidence(m.start(), m.end(), default_conf=0.91)
            fields_dict["net_quantity"] = ExtractedFieldItem(
                field_type="net_quantity",
                value=val,
                confidence=conf,
                font_size_mm=compute_font_size_mm(bbox, mm_per_pixel),
                placement_zone="principal_display_panel",
                bbox_px=bbox
            )
            break

    # 3. Unit Sale Price (USP)
    # Variations: Unit Sale Price, USP, Rs. X / g or ml
    usp_regexes = [
        r'(?:UNIT\s*SALE\s*PRICE|USP)\s*[:\-]?\s*(?:Rs\.?|INR|₹)?\s*([0-9]+(?:\.[0-9]{1,2})?\s*(?:\/|per)\s*(?:kg|g|gm|ml|l|ltr|piece|pc|unit|m|cm))\b',
        r'(?:Rs\.?|INR|₹)\s*([0-9]+(?:\.[0-9]{1,2})?\s*(?:\/|per)\s*(?:kg|g|gm|ml|l|ltr|pc|unit))\b'
    ]
    for pattern in usp_regexes:
        m = re.search(pattern, joined_text, re.IGNORECASE)
        if m:
            val = m.group(0).strip()
            bbox, conf = find_bbox_and_confidence(m.start(), m.end(), default_conf=0.89)
            fields_dict["unit_sale_price"] = ExtractedFieldItem(
                field_type="unit_sale_price",
                value=val,
                confidence=conf,
                font_size_mm=compute_font_size_mm(bbox, mm_per_pixel),
                placement_zone="declaration_panel",
                bbox_px=bbox
            )
            break

    # 4. Manufacturing Date (MFD / MFG / PKD)
    mfg_regexes = [
        r'(?:MFD|MFG|MANUFACTURED|PKD|PACKED|DATE\s*OF\s*(?:MFG|MFD|PACKING))\s*[:\-.]?\s*([0-3]?[0-9][\/\.\-][0-1]?[0-9][\/\.\-][12][0-9]{3}|[0-1]?[0-9][\/\.\-][12][0-9]{3}|[0-3]?[0-9][\/\.\-][0-1]?[0-9][\/\.\-][2][0-9]|[0-1]?[0-9][\/\.\-][2][0-9]|(?:JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC)[a-z]*[\s\.\,\-]*[12][0-9]{3})\b',
        r'\b(?:MFD|MFG|PKD)\s*[:\-.]?\s*([0-1]?[0-9][\/\.\-][12][0-9]{3})\b'
    ]
    for pattern in mfg_regexes:
        m = re.search(pattern, joined_text, re.IGNORECASE)
        if m:
            val = m.group(0).strip()
            bbox, conf = find_bbox_and_confidence(m.start(), m.end(), default_conf=0.90)
            fields_dict["mfg_date"] = ExtractedFieldItem(
                field_type="mfg_date",
                value=val,
                confidence=conf,
                font_size_mm=compute_font_size_mm(bbox, mm_per_pixel),
                placement_zone="declaration_panel",
                bbox_px=bbox
            )
            break

    # 5. Expiry Date (EXP / Expiry / Use By)
    exp_regexes = [
        r'(?:EXP|EXPIRY|EXP\.\s*DATE|USE\s*BY|DATE\s*OF\s*EXPIRY)\s*[:\-.]?\s*([0-3]?[0-9][\/\.\-][0-1]?[0-9][\/\.\-][12][0-9]{3}|[0-1]?[0-9][\/\.\-][12][0-9]{3}|[0-3]?[0-9][\/\.\-][0-1]?[0-9][\/\.\-][2][0-9]|[0-1]?[0-9][\/\.\-][2][0-9]|(?:JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC)[a-z]*[\s\.\,\-]*[12][0-9]{3})\b'
    ]
    for pattern in exp_regexes:
        m = re.search(pattern, joined_text, re.IGNORECASE)
        if m:
            val = m.group(0).strip()
            bbox, conf = find_bbox_and_confidence(m.start(), m.end(), default_conf=0.90)
            fields_dict["expiry_date"] = ExtractedFieldItem(
                field_type="expiry_date",
                value=val,
                confidence=conf,
                font_size_mm=compute_font_size_mm(bbox, mm_per_pixel),
                placement_zone="declaration_panel",
                bbox_px=bbox
            )
            break

    # 6. Best Before Date
    best_before_regexes = [
        r'(?:BEST\s*BEFORE|BEST\s*BY)\s*[:\-.]?\s*([0-9]+\s*(?:MONTHS?|DAYS?|WEEKS?|YEARS?)\s*(?:FROM\s*(?:MFG|MFD|PACKING|MANUFACTURE|DATE))?|[0-3]?[0-9][\/\.\-][0-1]?[0-9][\/\.\-][12][0-9]{3}|[0-1]?[0-9][\/\.\-][12][0-9]{3}|(?:JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC)[a-z]*[\s\.\,\-]*[12][0-9]{3})\b'
    ]
    for pattern in best_before_regexes:
        m = re.search(pattern, joined_text, re.IGNORECASE)
        if m:
            val = m.group(0).strip()
            bbox, conf = find_bbox_and_confidence(m.start(), m.end(), default_conf=0.88)
            fields_dict["best_before_date"] = ExtractedFieldItem(
                field_type="best_before_date",
                value=val,
                confidence=conf,
                font_size_mm=compute_font_size_mm(bbox, mm_per_pixel),
                placement_zone="declaration_panel",
                bbox_px=bbox
            )
            break

    # 7. FSSAI License Number (14 digits)
    fssai_regexes = [
        r'(?:FSSAI|LIC(?:\.|\s+)?NO(?:\.|\s+)?)\s*[:\-]?\s*([0-9]{14})\b',
        r'\b(1[0-9]{13})\b'
    ]
    for pattern in fssai_regexes:
        m = re.search(pattern, joined_text, re.IGNORECASE)
        if m:
            val = m.group(0).strip()
            bbox, conf = find_bbox_and_confidence(m.start(), m.end(), default_conf=0.96)
            fields_dict["fssai_license_no"] = ExtractedFieldItem(
                field_type="fssai_license_no",
                value=val,
                confidence=conf,
                font_size_mm=compute_font_size_mm(bbox, mm_per_pixel),
                placement_zone="declaration_panel",
                bbox_px=bbox
            )
            break

    # 8. Batch / Lot Number
    batch_regexes = [
        r'(?:BATCH\s*(?:NO|NUMBER|\.)?|LOT\s*(?:NO|NUMBER|\.)?|B\.?\s*NO\.?)\s*[:\-]?\s*([A-Za-z0-9\-\/]{3,20})\b'
    ]
    for pattern in batch_regexes:
        m = re.search(pattern, joined_text, re.IGNORECASE)
        if m:
            val = m.group(0).strip()
            bbox, conf = find_bbox_and_confidence(m.start(), m.end(), default_conf=0.88)
            fields_dict["batch_number"] = ExtractedFieldItem(
                field_type="batch_number",
                value=val,
                confidence=conf,
                font_size_mm=compute_font_size_mm(bbox, mm_per_pixel),
                placement_zone="declaration_panel",
                bbox_px=bbox
            )
            break

    # 9. Consumer Care Details (Phone, email, or careline)
    care_match = re.search(
        r'(?:CONSUMER\s*CARE|CUSTOMER\s*CARE|FOR\s*FEEDBACK|HELPLINE|CARELINE|CONTACT\s*US)\s*[:\-]?\s*([^\n\r]{5,90})',
        joined_text,
        re.IGNORECASE
    )
    if care_match:
        val = care_match.group(0).strip()
        bbox, conf = find_bbox_and_confidence(care_match.start(), care_match.end(), default_conf=0.89)
        fields_dict["consumer_care_details"] = ExtractedFieldItem(
            field_type="consumer_care_details",
            value=val,
            confidence=conf,
            font_size_mm=compute_font_size_mm(bbox, mm_per_pixel),
            placement_zone="declaration_panel",
            bbox_px=bbox
        )
    else:
        # Fallback to phone / email detection
        contact_match = re.search(
            r'(?:1800[\s\-]?\d{3,4}[\s\-]?\d{3,4}|\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b)',
            joined_text
        )
        if contact_match:
            val = contact_match.group(0).strip()
            bbox, conf = find_bbox_and_confidence(contact_match.start(), contact_match.end(), default_conf=0.87)
            fields_dict["consumer_care_details"] = ExtractedFieldItem(
                field_type="consumer_care_details",
                value=f"Customer Care: {val}",
                confidence=conf,
                font_size_mm=compute_font_size_mm(bbox, mm_per_pixel),
                placement_zone="declaration_panel",
                bbox_px=bbox
            )

    # 10. Country of Origin
    origin_match = re.search(
        r'(?:COUNTRY\s*OF\s*ORIGIN|MADE\s*IN|PRODUCED\s*IN|PRODUCT\s*OF)\s*[:\-]?\s*([A-Za-z\s]{3,30})\b',
        joined_text,
        re.IGNORECASE
    )
    if origin_match:
        val = origin_match.group(0).strip()
        bbox, conf = find_bbox_and_confidence(origin_match.start(), origin_match.end(), default_conf=0.91)
        fields_dict["country_of_origin"] = ExtractedFieldItem(
            field_type="country_of_origin",
            value=val,
            confidence=conf,
            font_size_mm=compute_font_size_mm(bbox, mm_per_pixel),
            placement_zone="declaration_panel",
            bbox_px=bbox
        )

    # 11. Manufacturer Name & Address
    mfg_name_match = re.search(
        r'(?:MFD(?:\.|\s+)?BY|MFG(?:\.|\s+)?BY|MANUFACTURED\s*BY|PACKED\s*BY|MARKETED\s*BY|PRODUCED\s*BY)\s*[:\-]?\s*([A-Za-z0-9\s\,\.\&\(\)\-]{4,60}?)(?:,|\n|Plot|Survey|Gate|Industrial|Phase|Sector|Village|Taluka|Dist|Road|Street|Near|Pin|Pincode|\d{6}|$)',
        joined_text,
        re.IGNORECASE
    )
    if mfg_name_match:
        val = mfg_name_match.group(0).strip()
        bbox, conf = find_bbox_and_confidence(mfg_name_match.start(), mfg_name_match.end(), default_conf=0.88)
        fields_dict["manufacturer_name"] = ExtractedFieldItem(
            field_type="manufacturer_name",
            value=val,
            confidence=conf,
            font_size_mm=compute_font_size_mm(bbox, mm_per_pixel),
            placement_zone="declaration_panel",
            bbox_px=bbox
        )

    address_match = re.search(
        r'(?:Plot|Survey|Gate|Industrial\s*Area|Phase|Sector|Village|Taluka|Dist|Road|Street|Near)\s*[A-Za-z0-9\s\,\.\-\/]{6,100}?(?:\b[1-9][0-9]{5}\b|[A-Za-z]{2,}\b|\d{6})',
        joined_text,
        re.IGNORECASE
    )
    if address_match:
        val = address_match.group(0).strip()
        bbox, conf = find_bbox_and_confidence(address_match.start(), address_match.end(), default_conf=0.86)
        fields_dict["manufacturer_address"] = ExtractedFieldItem(
            field_type="manufacturer_address",
            value=val,
            confidence=conf,
            font_size_mm=compute_font_size_mm(bbox, mm_per_pixel),
            placement_zone="declaration_panel",
            bbox_px=bbox
        )

    # 12. Commodity / Generic Product Name
    commodity_match = re.search(
        r'(?:COMMODITY|GENERIC\s*NAME|PRODUCT\s*NAME|NAME\s*OF\s*THE\s*COMMODITY)\s*[:\-]?\s*([A-Za-z0-9\s\,\.\-]{3,45})\b',
        joined_text,
        re.IGNORECASE
    )
    if commodity_match:
        val = commodity_match.group(0).strip()
        bbox, conf = find_bbox_and_confidence(commodity_match.start(), commodity_match.end(), default_conf=0.90)
        fields_dict["commodity_name"] = ExtractedFieldItem(
            field_type="commodity_name",
            value=val,
            confidence=conf,
            font_size_mm=compute_font_size_mm(bbox, mm_per_pixel),
            placement_zone="principal_display_panel",
            bbox_px=bbox
        )

    return list(fields_dict.values())


# ==========================================
# SINGLE IMAGE PROCESSING PIPELINE
# ==========================================
def process_single_image(
    image: np.ndarray,
    scan_id: str,
    ocr_model: Any,
    gliner_model: Any = None
) -> Dict[str, Any]:
    """Process one image: barcode calibration → OCR → legal metrology extraction."""
    t_start = time.time()
    height, width = image.shape[:2]

    # Barcode & Scale Calibration
    mm_per_pixel, barcode_info, barcode_str, cal_warnings = calibrate_mm_per_pixel(image)

    # Text Detection & Recognition via PaddleOCR
    words_data, full_text = extract_words_paddle(ocr_model, image)
    ocr_elapsed_ms = round((time.time() - t_start) * 1000, 2)

    extracted_fields = []
    detected_words = []

    if words_data:
        extracted_fields = extract_legal_metrology_fields(words_data, full_text, mm_per_pixel)
        detected_words = [
            DetectedWord(
                text=w["text"],
                confidence=w["confidence"],
                bbox_px=w["bbox_px"],
                font_size_mm=compute_font_size_mm(w["bbox_px"], mm_per_pixel)
            )
            for w in words_data
        ]

    total_elapsed_ms = round((time.time() - t_start) * 1000, 2)

    return {
        "image_dimensions": {"width": width, "height": height},
        "fields": extracted_fields,
        "all_words": detected_words,
        "raw_text": full_text,
        "scale_factor_mm_per_px": mm_per_pixel,
        "barcode": barcode_str,
        "barcode_detected": barcode_info is not None,
        "barcode_info": barcode_info,
        "warnings": cal_warnings,
        "timings_ms": {
            "ocr_ms": ocr_elapsed_ms,
            "total_ms": total_elapsed_ms
        }
    }


def merge_multi_image_results(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Merge OCR results from multiple image angles."""
    merged_fields: Dict[str, ExtractedFieldItem] = {}
    scale_factor = None
    barcode_val = None
    barcode_info = None
    all_warnings = []
    all_raw_texts = []
    all_words = []
    image_dims = None

    for res in results:
        if image_dims is None and res.get("image_dimensions"):
            image_dims = res["image_dimensions"]

        if scale_factor is None and res.get("scale_factor_mm_per_px") is not None:
            scale_factor = res["scale_factor_mm_per_px"]

        if barcode_val is None and res.get("barcode"):
            barcode_val = res["barcode"]
            barcode_info = res.get("barcode_info")

        all_warnings.extend(res.get("warnings", []))
        if res.get("raw_text"):
            all_raw_texts.append(res["raw_text"])
        all_words.extend(res.get("all_words", []))

        for field in res.get("fields", []):
            ft = field.field_type
            if ft not in merged_fields or field.confidence > merged_fields[ft].confidence:
                merged_fields[ft] = field

    if scale_factor is not None:
        for f in merged_fields.values():
            if f.font_size_mm is None and f.bbox_px:
                f.font_size_mm = compute_font_size_mm(f.bbox_px, scale_factor)

    unique_warnings = list(dict.fromkeys(all_warnings))

    return {
        "image_dimensions": image_dims,
        "fields": list(merged_fields.values()),
        "scale_factor_mm_per_px": scale_factor,
        "barcode": barcode_val,
        "barcode_info": barcode_info,
        "raw_text": "\n\n".join(all_raw_texts) if all_raw_texts else None,
        "all_words": all_words,
        "warnings": unique_warnings,
        "timings_ms": {
            "ocr_ms": round(sum(r.get("timings_ms", {}).get("ocr_ms", 0) for r in results), 2),
            "total_ms": round(sum(r.get("timings_ms", {}).get("total_ms", 0) for r in results), 2)
        }
    }


# ==========================================
# FASTAPI ENDPOINTS
# ==========================================
@app.get("/health")
async def health_check(request: Request):
    """Health check endpoint displaying PaddleOCR model status and device info."""
    ocr_loaded = hasattr(request.app.state, "ocr_model") and request.app.state.ocr_model is not None
    return {
        "status": "ok" if ocr_loaded else "initializing",
        "service": "paddleocr",
        "device": DEVICE,
        "models": {
            "paddleocr_loaded": ocr_loaded,
            "pyzbar_available": PYZBAR_AVAILABLE,
            "gliner_available": GLINER_AVAILABLE and getattr(request.app.state, "gliner_model", None) is not None
        }
    }


@app.post("/process", response_model=ProcessResponse)
async def process_scan_endpoint(
    request: Request,
    scan_id: Optional[str] = Form(None),
    category: Optional[str] = Form("general"),
    images: List[UploadFile] = File(default=[])
):
    """
    Primary endpoint called by Django backend.
    Accepts multipart/form-data with one or more image files.
    Also handles JSON fallback if application/json content-type is posted.
    """
    t_start = time.time()
    cv_images: List[np.ndarray] = []
    final_scan_id = scan_id or f"scan_{int(time.time()*1000)}"

    content_type = request.headers.get("content-type", "")

    # 1. Handle JSON request fallback
    if "application/json" in content_type:
        try:
            body = await request.json()
            json_req = OCRRequest(**body)
            final_scan_id = json_req.scan_id or final_scan_id
            b64_list = json_req.image_base64
            if isinstance(b64_list, str):
                b64_list = [b64_list]
            if b64_list:
                for b64 in b64_list:
                    cv_images.append(decode_base64_image(b64))
        except Exception as e:
            logger.error("JSON payload decode error: %s", e)
            raise HTTPException(status_code=422, detail=f"Invalid JSON request: {e}")

    # 2. Handle Multipart/form-data upload
    else:
        if not images:
            raise HTTPException(status_code=422, detail="No image files provided in multipart request.")
        if len(images) > MAX_IMAGES_PER_REQUEST:
            raise HTTPException(status_code=422, detail=f"Maximum {MAX_IMAGES_PER_REQUEST} images allowed.")

        for idx, file in enumerate(images):
            try:
                data = await file.read()
                cv_img = decode_image_bytes(data, filename=file.filename or f"image_{idx}")
                cv_images.append(cv_img)
            except ValueError as e:
                logger.error("Image file error: %s", e)
                raise HTTPException(status_code=422, detail=str(e))
            except Exception as e:
                logger.error("Unexpected upload error: %s", e)
                raise HTTPException(status_code=500, detail=f"Image upload processing error: {e}")

    if not cv_images:
        raise HTTPException(status_code=422, detail="No valid images available to process.")

    ocr_model = getattr(request.app.state, "ocr_model", None)
    if ocr_model is None:
        raise HTTPException(status_code=503, detail="PaddleOCR engine is still initializing.")

    # Process all image angles cleanly without CPU thread thrashing
    results = []
    gliner_m = getattr(request.app.state, "gliner_model", None)
    for img in cv_images:
        res = await run_in_threadpool(
            process_single_image,
            img,
            final_scan_id,
            ocr_model,
            gliner_m
        )
        results.append(res)

    merged = merge_multi_image_results(results)
    merged["timings_ms"]["total_ms"] = round((time.time() - t_start) * 1000, 2)

    # Empty text warning
    if not merged["fields"] and not merged.get("raw_text"):
        merged["warnings"].append("No text detected in uploaded image(s).")

    return ProcessResponse(
        scan_id=final_scan_id,
        extracted_fields=merged["fields"],
        barcode=merged["barcode"],
        quality_flags=[],
        raw_text=merged["raw_text"],
        all_words=merged["all_words"],
        image_dimensions=merged["image_dimensions"],
        scale_factor_mm_per_px=merged["scale_factor_mm_per_px"],
        barcode_info=merged["barcode_info"],
        warnings=merged["warnings"],
        timings_ms=merged["timings_ms"]
    )


@app.post("/extract", response_model=ProcessResponse)
async def extract_endpoint(request: OCRRequest, req: Request):
    """Backwards-compatible base64 JSON endpoint."""
    t_start = time.time()
    cv_images: List[np.ndarray] = []

    b64_list = request.image_base64
    if isinstance(b64_list, str):
        b64_list = [b64_list]

    if not b64_list:
        raise HTTPException(status_code=422, detail="At least one base64 image required.")

    for b64 in b64_list:
        try:
            cv_images.append(decode_base64_image(b64))
        except ValueError as e:
            raise HTTPException(status_code=422, detail=str(e))

    ocr_model = getattr(req.app.state, "ocr_model", None)
    if ocr_model is None:
        raise HTTPException(status_code=503, detail="PaddleOCR engine is not initialized.")

    tasks = [
        run_in_threadpool(
            process_single_image,
            img,
            request.scan_id or f"scan_{int(time.time() * 1000)}",
            ocr_model,
            getattr(req.app.state, "gliner_model", None)
        )
        for img in cv_images
    ]
    results = await asyncio.gather(*tasks)
    merged = merge_multi_image_results(results)
    merged["timings_ms"]["total_ms"] = round((time.time() - t_start) * 1000, 2)

    return ProcessResponse(
        scan_id=request.scan_id,
        extracted_fields=merged["fields"],
        barcode=merged["barcode"],
        quality_flags=[],
        raw_text=merged["raw_text"],
        all_words=merged["all_words"],
        image_dimensions=merged["image_dimensions"],
        scale_factor_mm_per_px=merged["scale_factor_mm_per_px"],
        barcode_info=merged["barcode_info"],
        warnings=merged["warnings"],
        timings_ms=merged["timings_ms"]
    )


# ==========================================
# ENTRY POINT
# ==========================================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT)