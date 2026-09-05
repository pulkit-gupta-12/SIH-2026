"""
Legal Metrology Inspection PDF Report Generation Service.
Uses ReportLab Platypus to construct statutory inspection reports pulling real ORM data.
"""
# Legal Metrology Inspection PDF Report Generation Service (ReportLab 5.x).
import os
import io
import logging
from datetime import datetime, date
from django.conf import settings
from django.utils import timezone
from PIL import Image as PILImage

try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import inch
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import (
        SimpleDocTemplate,
        Paragraph,
        Spacer,
        Table,
        TableStyle,
        Image as RLImage,
        KeepTogether,
        HRFlowable,
    )
    from reportlab.pdfgen import canvas
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    colors = None
    canvas = None

from apps.reports.models import Report
from apps.scans.services import resolve_image_bytes

logger = logging.getLogger(__name__)

BaseCanvas = canvas.Canvas if canvas and hasattr(canvas, "Canvas") else object


class NumberedCanvas(BaseCanvas):
    """
    Two-pass canvas to dynamically compute and render total page count
    and government header/footer on each page.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748b"))

        # Running header (pages > 1)
        if self._pageNumber > 1:
            self.drawString(40, 810, "Legal Metrology Inspection Report — Government of India")
            self.setStrokeColor(colors.HexColor("#cbd5e1"))
            self.setLineWidth(0.5)
            self.line(40, 804, 555, 804)

        # Running footer (all pages)
        self.setStrokeColor(colors.HexColor("#cbd5e1"))
        self.setLineWidth(0.5)
        self.line(40, 42, 555, 42)
        self.drawString(40, 30, "National Legal Metrology Compliance Platform | Confidential Official Record")
        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(555, 30, page_str)
        self.restoreState()


def build_pdf_report(report_id, scan, product, officer, compliance_check=None, case=None) -> bytes:
    """
    Constructs the complete 9-section Legal Metrology Inspection PDF using ReportLab Platypus.
    Returns the generated PDF as raw bytes.
    """
    if not REPORTLAB_AVAILABLE:
        raise RuntimeError(
            "ReportLab is not installed in the active Python environment. "
            "Please run: pip install reportlab"
        )

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=40,
        rightMargin=40,
        topMargin=45,
        bottomMargin=55,
    )

    styles = getSampleStyleSheet()
    
    # Custom Typography Palette
    c_primary = colors.HexColor("#1e3a8a")     # Deep Navy
    c_dark = colors.HexColor("#0f172a")        # Slate Dark
    c_slate = colors.HexColor("#475569")       # Slate Medium
    c_border = colors.HexColor("#cbd5e1")      # Slate Light
    c_bg_light = colors.HexColor("#f8fafc")    # Off-white
    c_pass = colors.HexColor("#15803d")        # Forest Green
    c_fail = colors.HexColor("#b91c1c")        # Crimson Red

    style_gov_title = ParagraphStyle(
        "GovTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#475569"),
        alignment=1,  # Center
    )
    style_main_title = ParagraphStyle(
        "MainTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=17,
        leading=22,
        textColor=c_primary,
        alignment=1,
    )
    style_section_h = ParagraphStyle(
        "SectionH",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=15,
        textColor=c_primary,
        spaceBefore=10,
        spaceAfter=4,
    )
    style_label = ParagraphStyle(
        "LabelStyle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8.5,
        leading=11,
        textColor=c_dark,
    )
    style_val = ParagraphStyle(
        "ValStyle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=11,
        textColor=c_slate,
    )
    style_table_h = ParagraphStyle(
        "TableH",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8,
        leading=10,
        textColor=colors.white,
    )
    style_table_cell = ParagraphStyle(
        "TableCell",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=10,
        textColor=c_dark,
    )
    style_cert_body = ParagraphStyle(
        "CertBody",
        parent=styles["Normal"],
        fontName="Helvetica-Oblique",
        fontSize=8.5,
        leading=12,
        textColor=c_dark,
    )

    story = []

    # -------------------------------------------------------------
    # 1. HEADER SECTION
    # -------------------------------------------------------------
    story.append(Paragraph("GOVERNMENT OF INDIA | MINISTRY OF CONSUMER AFFAIRS, FOOD & PUBLIC DISTRIBUTION", style_gov_title))
    story.append(Paragraph("DEPARTMENT OF CONSUMER AFFAIRS | LEGAL METROLOGY DIVISION", style_gov_title))
    story.append(Spacer(1, 4))
    story.append(Paragraph("LEGAL METROLOGY INSPECTION REPORT", style_main_title))
    story.append(Spacer(1, 6))

    now_str = timezone.now().strftime("%d %b %Y, %I:%M %p IST")
    report_code = f"LMR-{report_id:05d}"

    header_meta_data = [
        [
            Paragraph(f"<b>Report ID:</b> {report_code}", style_val),
            Paragraph(f"<b>Generated At:</b> {now_str}", style_val),
            Paragraph(f"<b>Statutory Basis:</b> Legal Metrology Act, 2009", style_val),
        ]
    ]
    t_header = Table(header_meta_data, colWidths=[160, 180, 175])
    t_header.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), c_bg_light),
        ("BOX", (0, 0), (-1, -1), 0.5, c_border),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(t_header)
    story.append(Spacer(1, 10))

    # -------------------------------------------------------------
    # 2. OFFICER DETAILS & 3. INSPECTION DETAILS (Two Column Grid)
    # -------------------------------------------------------------
    officer_name = "N/A"
    officer_uname = "N/A"
    officer_state = "National Jurisdiction"
    if officer:
        officer_name = officer.get_full_name() or officer.username
        officer_uname = officer.username
        role_assign = officer.role_assignments.filter(role__name__in=["field_officer", "state_controller", "national_admin"]).first()
        if role_assign and role_assign.state:
            officer_state = role_assign.state

    scan_id_str = f"SCAN-{scan.id}" if scan else "N/A"
    scan_date_str = scan.created_at.strftime("%d %b %Y, %I:%M %p") if scan and scan.created_at else date.today().strftime("%d %b %Y")
    scan_loc = (scan.location if scan and scan.location else "Field Inspection Site")
    scan_method = (scan.get_capture_method_display() if scan and hasattr(scan, "get_capture_method_display") else (scan.capture_method if scan else "guided_capture"))

    details_grid_data = [
        [
            Paragraph("<b>OFFICER DETAILS</b>", style_label),
            Paragraph("<b>INSPECTION DETAILS</b>", style_label)
        ],
        [
            Paragraph(f"<b>Name:</b> {officer_name}", style_val),
            Paragraph(f"<b>Scan ID:</b> {scan_id_str}", style_val),
        ],
        [
            Paragraph(f"<b>Username / ID:</b> {officer_uname}", style_val),
            Paragraph(f"<b>Inspection Date:</b> {scan_date_str}", style_val),
        ],
        [
            Paragraph(f"<b>Assigned Jurisdiction:</b> {officer_state}", style_val),
            Paragraph(f"<b>Location:</b> {scan_loc}", style_val),
        ],
        [
            Paragraph(f"<b>Role Context:</b> {scan.get_role_context_display() if scan and hasattr(scan, 'get_role_context_display') else 'Field Officer'}", style_val),
            Paragraph(f"<b>Capture Method:</b> {scan_method}", style_val),
        ],
    ]
    t_details = Table(details_grid_data, colWidths=[255, 260])
    t_details.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, 0), colors.HexColor("#f1f5f9")),
        ("BACKGROUND", (1, 0), (1, 0), colors.HexColor("#f1f5f9")),
        ("BOX", (0, 0), (-1, -1), 0.5, c_border),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(t_details)
    story.append(Spacer(1, 10))

    # -------------------------------------------------------------
    # 4. PRODUCT / BUSINESS DETAILS
    # -------------------------------------------------------------
    story.append(Paragraph("PRODUCT & BUSINESS DETAILS", style_section_h))
    
    prod_name = product.product_name if product else "Unregistered Package"
    prod_brand = product.brand_name if product else "Generic"
    prod_barcode = product.gtin_barcode if product else (scan.canonical_data.get("barcode") if scan and scan.canonical_data else "N/A")
    prod_cat = product.get_category_display() if product and hasattr(product, "get_category_display") else (product.category if product else "General")
    mfg_name = product.manufacturer_name if product else "Not Specified"
    mfg_addr = product.manufacturer_address if product else "Not Specified"

    prod_table_data = [
        [
            Paragraph("<b>Product Name:</b>", style_label),
            Paragraph(prod_name, style_val),
            Paragraph("<b>Brand:</b>", style_label),
            Paragraph(prod_brand, style_val),
        ],
        [
            Paragraph("<b>GTIN / Barcode:</b>", style_label),
            Paragraph(prod_barcode or "N/A", style_val),
            Paragraph("<b>Category:</b>", style_label),
            Paragraph(str(prod_cat).title(), style_val),
        ],
        [
            Paragraph("<b>Manufacturer:</b>", style_label),
            Paragraph(mfg_name, style_val),
            Paragraph("<b>Mfg Address:</b>", style_label),
            Paragraph(mfg_addr, style_val),
        ],
    ]
    t_prod = Table(prod_table_data, colWidths=[85, 170, 85, 175])
    t_prod.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.5, c_border),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ("BACKGROUND", (0, 0), (-1, -1), c_bg_light),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(t_prod)
    story.append(Spacer(1, 10))

    # -------------------------------------------------------------
    # 5. EXTRACTED FIELDS TABLE
    # -------------------------------------------------------------
    story.append(Paragraph("EXTRACTED MANDATORY DECLARATIONS", style_section_h))

    # Collect extracted fields from Scan
    extracted_rows = []
    if scan:
        extracted_rows = list(scan.extracted_fields.all().order_by("field_type"))

    # Collect set of failed fields from violations to mark Pass/Fail accurately
    violations_list = []
    if compliance_check:
        violations_list = list(compliance_check.violations.select_related("rule", "evidence_image").all())
    elif case and case.violation:
        violations_list = [case.violation]

    failed_field_keywords = set()
    for v in violations_list:
        v_desc = (v.description or "").lower()
        if "mrp" in v_desc or "price" in v_desc:
            failed_field_keywords.add("mrp")
        if "net quantity" in v_desc or "weight" in v_desc or "volume" in v_desc or "font" in v_desc:
            failed_field_keywords.add("net_quantity")
        if "date" in v_desc or "mfg" in v_desc:
            failed_field_keywords.add("mfg_date")
        if "consumer care" in v_desc or "helpline" in v_desc or "email" in v_desc:
            failed_field_keywords.add("consumer_care_details")
        if "address" in v_desc or "manufacturer" in v_desc:
            failed_field_keywords.add("manufacturer_address")
        if "origin" in v_desc or "country" in v_desc:
            failed_field_keywords.add("country_of_origin")

    ext_header = [
        Paragraph("Field Type", style_table_h),
        Paragraph("Extracted Value", style_table_h),
        Paragraph("Confidence", style_table_h),
        Paragraph("Font Size", style_table_h),
        Paragraph("Zone", style_table_h),
        Paragraph("Result", style_table_h),
    ]
    ext_table_data = [ext_header]

    if extracted_rows:
        for f in extracted_rows:
            f_type_str = f.field_type.replace("_", " ").title()
            val_str = f.extracted_value[:60] + ("..." if len(f.extracted_value) > 60 else "")
            conf_str = f"{f.confidence_score * 100:.1f}%"
            font_str = f"{f.font_size_mm:.1f} mm" if f.font_size_mm is not None else "N/A"
            zone_str = (f.placement_zone or "N/A").replace("_", " ").title()

            is_fail = f.field_type.lower() in failed_field_keywords
            status_html = (
                '<font color="#b91c1c"><b>FAIL</b></font>'
                if is_fail else
                '<font color="#15803d"><b>PASS</b></font>'
            )

            ext_table_data.append([
                Paragraph(f_type_str, style_table_cell),
                Paragraph(val_str, style_table_cell),
                Paragraph(conf_str, style_table_cell),
                Paragraph(font_str, style_table_cell),
                Paragraph(zone_str, style_table_cell),
                Paragraph(status_html, style_table_cell),
            ])
    else:
        ext_table_data.append([
            Paragraph("No raw extracted fields recorded for this inspection.", style_table_cell),
            Paragraph("—", style_table_cell),
            Paragraph("—", style_table_cell),
            Paragraph("—", style_table_cell),
            Paragraph("—", style_table_cell),
            Paragraph("N/A", style_table_cell),
        ])

    t_ext = Table(ext_table_data, colWidths=[95, 180, 55, 55, 75, 55])
    t_ext.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e293b")),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, c_bg_light]),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(t_ext)
    story.append(Spacer(1, 10))

    # -------------------------------------------------------------
    # 6. VIOLATIONS SECTION
    # -------------------------------------------------------------
    story.append(Paragraph("STATUTORY VIOLATIONS & RULE FINDINGS", style_section_h))

    if violations_list:
        v_header = [
            Paragraph("Rule Code & Citation", style_table_h),
            Paragraph("Description of Violation", style_table_h),
            Paragraph("Evidence Image Ref", style_table_h),
        ]
        v_table_data = [v_header]
        for v in violations_list:
            rule_code = v.rule.rule_id_code if v.rule else "LMR-SEC-UNKNOWN"
            sec_ref = v.rule.section_ref if v.rule else "Section Ref N/A"
            citation_html = f"<b>{rule_code}</b><br/><font color='#64748b'>{sec_ref}</font>"
            desc_html = v.description or "Mandatory statutory declaration missing or non-compliant."

            img_ref_str = "None linked"
            if v.evidence_image:
                img_ref_str = f"Image #{v.evidence_image.id} ({v.evidence_image.get_angle_type_display() if hasattr(v.evidence_image, 'get_angle_type_display') else v.evidence_image.angle_type})"

            v_table_data.append([
                Paragraph(citation_html, style_table_cell),
                Paragraph(desc_html, style_table_cell),
                Paragraph(img_ref_str, style_table_cell),
            ])

        t_viol = Table(v_table_data, colWidths=[145, 255, 115])
        t_viol.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#991b1b")),  # Crimson Red Header
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#fca5a5")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#fff1f2"), colors.white]),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ]))
        story.append(t_viol)
    else:
        # Clear "No violations found" banner as requested
        no_viol_box = [
            [
                Paragraph(
                    "<b>[COMPLIANT] No violations found.</b> The inspected packaging fully complies with all applicable provisions of the Legal Metrology Act, 2009 and the Legal Metrology (Packaged Commodities) Rules, 2011.",
                    ParagraphStyle("NoViol", parent=styles["Normal"], fontName="Helvetica", fontSize=9, textColor=c_pass, leading=13)
                )
            ]
        ]
        t_no_viol = Table(no_viol_box, colWidths=[515])
        t_no_viol.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f0fdf4")),
            ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#86efac")),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ("LEFTPADDING", (0, 0), (-1, -1), 10),
            ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ]))
        story.append(t_no_viol)

    story.append(Spacer(1, 10))

    # -------------------------------------------------------------
    # 7. CASE & ENFORCEMENT OUTCOME
    # -------------------------------------------------------------
    story.append(Paragraph("ENFORCEMENT ACTION & STATUTORY PATHWAY", style_section_h))

    if case:
        case_id_str = f"CASE-{case.id:05d}"
        case_class = case.get_classification_display() if hasattr(case, "get_classification_display") else case.classification
        case_status_str = case.get_status_display() if hasattr(case, "get_status_display") else case.status

        outcome_rows = [
            [
                Paragraph("<b>Case Reference:</b>", style_label),
                Paragraph(case_id_str, style_val),
                Paragraph("<b>Classification:</b>", style_label),
                Paragraph(f"<b>{case_class}</b>", style_val),
            ],
            [
                Paragraph("<b>Case Status:</b>", style_label),
                Paragraph(case_status_str, style_val),
                Paragraph("<b>Date Opened:</b>", style_label),
                Paragraph(case.created_at.strftime("%d %b %Y") if case.created_at else "N/A", style_val),
            ],
        ]

        if hasattr(case, "improvement_notice") and case.improvement_notice:
            impr = case.improvement_notice
            deadline_str = impr.rectification_deadline.strftime("%d %b %Y") if impr.rectification_deadline else "30 Days from Notice"
            outcome_str = impr.get_outcome_display() if hasattr(impr, "get_outcome_display") else impr.outcome
            outcome_rows.append([
                Paragraph("<b>Enforcement Track:</b>", style_label),
                Paragraph("Section 29 — Improvement Notice", style_val),
                Paragraph("<b>Rectification Window:</b>", style_label),
                Paragraph(f"Deadline: {deadline_str} ({outcome_str})", style_val),
            ])
        elif hasattr(case, "penalty_case") and case.penalty_case:
            pen = case.penalty_case
            pay_str = pen.get_payment_status_display() if hasattr(pen, "get_payment_status_display") else pen.payment_status
            app_str = pen.get_appeal_status_display() if hasattr(pen, "get_appeal_status_display") else pen.appeal_status
            outcome_rows.append([
                Paragraph("<b>Enforcement Track:</b>", style_label),
                Paragraph("Section 39 — Compounding / Penalty Case", style_val),
                Paragraph("<b>Status:</b>", style_label),
                Paragraph(f"Payment: {pay_str} | Appeal: {app_str}", style_val),
            ])

        t_case = Table(outcome_rows, colWidths=[105, 150, 110, 150])
        t_case.setStyle(TableStyle([
            ("BOX", (0, 0), (-1, -1), 0.5, c_border),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
            ("BACKGROUND", (0, 0), (-1, -1), c_bg_light),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ]))
        story.append(t_case)
    else:
        # Explicit note when no case exists
        no_case_box = [
            [
                Paragraph(
                    "<b>No formal enforcement case initiated.</b> Inspection yielded a compliant status or remains in review. No Section 29 Improvement Notice or Section 39 Penalty Case was required or created for this scan record.",
                    ParagraphStyle("NoCase", parent=styles["Normal"], fontName="Helvetica", fontSize=8.5, textColor=c_slate, leading=12)
                )
            ]
        ]
        t_no_case = Table(no_case_box, colWidths=[515])
        t_no_case.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
            ("BOX", (0, 0), (-1, -1), 0.5, c_border),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ]))
        story.append(t_no_case)

    story.append(Spacer(1, 10))

    # -------------------------------------------------------------
    # 8. EVIDENCE APPENDIX — SCAN IMAGES
    # -------------------------------------------------------------
    appendix_elements = []
    appendix_elements.append(Paragraph("EVIDENCE APPENDIX — INSPECTION CAPTURE IMAGES", style_section_h))

    scan_images = []
    if scan:
        scan_images = list(scan.images.all().order_by("created_at"))

    if scan_images:
        # Layout in rows of 2 images
        image_cells = []
        for idx, s_img in enumerate(scan_images):
            angle_str = s_img.get_angle_type_display() if hasattr(s_img, "get_angle_type_display") else s_img.angle_type
            ts_str = s_img.created_at.strftime("%d %b %Y, %I:%M %p") if s_img.created_at else "N/A"
            label_text = f"<b>Figure {idx + 1}:</b> {angle_str}<br/><font color='#64748b'>Captured: {ts_str}</font>"

            # Attempt to resolve image bytes safely
            rendered_flowable = None
            try:
                raw_bytes, fname = resolve_image_bytes(s_img.image_url)
                if raw_bytes and len(raw_bytes) > 100:
                    # Validate image decodability with PIL
                    with PILImage.open(io.BytesIO(raw_bytes)) as pil_img:
                        orig_w, orig_h = pil_img.size
                        # Max dimension in table cell: 220 pt width x 140 pt height
                        max_w = 220
                        max_h = 135
                        calc_w = min(max_w, orig_w * (max_h / orig_h)) if orig_h else max_w
                        calc_h = max_h
                        if calc_w > max_w:
                            calc_w = max_w
                            calc_h = orig_h * (max_w / orig_w) if orig_w else max_h

                        rendered_flowable = RLImage(io.BytesIO(raw_bytes), width=calc_w, height=calc_h)
            except Exception as e:
                logger.warning("Could not resolve image %s for PDF appendix: %s", s_img.id, e)
                rendered_flowable = None

            if not rendered_flowable:
                # Styled fallback box
                fallback_text = (
                    f"<b>[Image unavailable]</b><br/>"
                    f"<font color='#64748b' size='7'>{angle_str}<br/>"
                    f"ScanImage #{s_img.id}</font>"
                )
                fb_table = Table([[Paragraph(fallback_text, ParagraphStyle("FB", parent=styles["Normal"], alignment=1, leading=10))]], colWidths=[220], rowHeights=[100])
                fb_table.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f1f5f9")),
                    ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#94a3b8")),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ]))
                rendered_flowable = fb_table

            cell_content = [
                rendered_flowable,
                Spacer(1, 3),
                Paragraph(label_text, ParagraphStyle("ImgLabel", parent=styles["Normal"], fontSize=8, leading=10, alignment=1)),
            ]
            image_cells.append(cell_content)

        # Group cells into 2 per row
        grid_rows = []
        for i in range(0, len(image_cells), 2):
            pair = image_cells[i:i+2]
            if len(pair) == 1:
                grid_rows.append([pair[0], ""])
            else:
                grid_rows.append([pair[0], pair[1]])

        t_appendix = Table(grid_rows, colWidths=[255, 260])
        t_appendix.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ]))
        appendix_elements.append(t_appendix)
    else:
        appendix_elements.append(
            Paragraph("No scan imagery was attached to this inspection session.", style_val)
        )

    story.append(KeepTogether(appendix_elements))
    story.append(Spacer(1, 10))

    # -------------------------------------------------------------
    # 9. OFFICER CERTIFICATION BLOCK
    # -------------------------------------------------------------
    cert_date = scan_date_str if scan else date.today().strftime("%d %b %Y")
    cert_statement = (
        f"I, the undersigned Legal Metrology Officer, hereby certify that this inspection report "
        f"faithfully and accurately reflects the statutory findings, physical measurements, and automated "
        f"compliance verifications conducted on {cert_date} under the authority granted by the "
        f"Legal Metrology Act, 2009 and the Legal Metrology (Packaged Commodities) Rules, 2011."
    )

    cert_box_data = [
        [
            Paragraph("<b>OFFICER CERTIFICATION & ATTESTATION</b>", style_label),
            Paragraph("<b>AUTHENTICATION STATUS</b>", style_label),
        ],
        [
            Paragraph(cert_statement, style_cert_body),
            Paragraph(
                f"<b>Attesting Officer:</b> {officer_name}<br/>"
                f"<b>Designation:</b> Legal Metrology Field Officer<br/>"
                f"<b>Jurisdiction:</b> {officer_state}<br/>"
                f"<b>Signature:</b> <i>Officer confirmation on file</i><br/>"
                f"<font color='#64748b' size='7'>Internal Verification Record • Unsigned Placeholder (PyHanko pending)</font>",
                style_val
            ),
        ],
    ]
    t_cert = Table(cert_box_data, colWidths=[315, 200])
    t_cert.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f1f5f9")),
        ("BACKGROUND", (0, 1), (-1, 1), c_bg_light),
        ("BOX", (0, 0), (-1, -1), 0.5, c_border),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(KeepTogether([t_cert]))

    # Build document with NumberedCanvas for professional running header/footer
    doc.build(story, canvasmaker=NumberedCanvas)
    return buffer.getvalue()


def generate_and_save_report(case=None, compliance_check=None, officer=None) -> Report:
    """
    Orchestrates report generation:
    1. Resolves case, compliance_check, scan, product, and officer.
    2. Invents/creates a Report row to obtain a definitive primary key.
    3. Builds the ReportLab PDF byte stream.
    4. Saves the PDF to MEDIA_ROOT/reports/report_{id}_{timestamp}.pdf.
    5. Updates the Report record with the file_url and returns it.
    """
    if not case and not compliance_check:
        raise ValueError("Either case or compliance_check must be provided to generate a report.")

    # Cross-resolve models
    if case:
        if not compliance_check and case.violation:
            compliance_check = case.violation.compliance_check
        product = case.product
        officer = officer or case.opened_by
        scan = None
        if compliance_check and compliance_check.scan:
            scan = compliance_check.scan
        elif product:
            scan = product.scans.order_by("-created_at").first()
    else:
        # Generated from compliance_check directly
        scan = compliance_check.scan
        product = scan.product if scan else None
        officer = officer or compliance_check.reviewed_by_officer or (scan.performed_by if scan else None)

    # Pre-create Report row to secure Report ID
    report = Report.objects.create(
        case=case,
        compliance_check=compliance_check,
        file_url="",
        format="pdf",
        signed=False,
    )

    try:
        pdf_bytes = build_pdf_report(
            report_id=report.id,
            scan=scan,
            product=product,
            officer=officer,
            compliance_check=compliance_check,
            case=case,
        )

        reports_dir = os.path.join(settings.MEDIA_ROOT, "reports")
        os.makedirs(reports_dir, exist_ok=True)

        filename = f"report_{report.id}_{int(timezone.now().timestamp())}.pdf"
        filepath = os.path.join(reports_dir, filename)

        with open(filepath, "wb") as f:
            f.write(pdf_bytes)

        # Construct public media URL
        media_url_clean = settings.MEDIA_URL.strip("/")
        file_url = f"/{media_url_clean}/reports/{filename}"

        report.file_url = file_url
        report.save(update_fields=["file_url"])
        logger.info("Generated Legal Metrology Inspection Report #%s at %s (%d bytes)", report.id, filepath, len(pdf_bytes))
        return report

    except Exception as e:
        logger.error("Failed to generate PDF for Report #%s: %s", report.id, e)
        report.delete()
        raise e
