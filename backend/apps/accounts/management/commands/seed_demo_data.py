"""
Management command: seed_demo_data
Populates realistic demo data across all tables for all 7 demo users.
Matches 05_Database_Schema.md and ties records to existing demo users.
"""
from datetime import date, timedelta
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.accounts.models import User
from apps.product_master.models import Product
from apps.scans.models import Scan, ScanImage, ExtractedField
from apps.rules_engine.models import Rule
from apps.compliance.models import ComplianceCheck, Violation, ProductComplianceHistory
from apps.cases.models import Case, ImprovementNotice, PenaltyCase
from apps.complaints.models import Complaint
from apps.inspections.models import InspectionTarget
from apps.reports.models import Report
from apps.ecommerce_integration.models import EcommerceListing
from apps.notifications.models import Notification, AuditLog


class Command(BaseCommand):
    help = "Populates realistic demo data across all platform tables for the 7 demo users."

    def handle(self, *args, **options):
        self.stdout.write("Seeding demo data across all 10 apps...")

        # Ensure demo users exist
        try:
            citizen = User.objects.get(username="citizen_demo")
            officer = User.objects.get(username="officer_demo")
            controller = User.objects.get(username="controller_demo")
            admin = User.objects.get(username="admin_demo")
            business = User.objects.get(username="business_demo")
            ecommerce = User.objects.get(username="ecommerce_demo")
            ruleadmin = User.objects.get(username="ruleadmin_demo")
        except User.DoesNotExist as e:
            self.stderr.write(self.style.ERROR(f"Missing demo user: {e}. Run `seed_roles` first."))
            return

        with transaction.atomic():
            today = date.today()
            now = timezone.now()

            # -----------------------------------------------------------------
            # 1. Product Master
            # -----------------------------------------------------------------
            self.stdout.write("  -> Seeding Products...")
            products_data = [
                {
                    "gtin_barcode": "8901234567890",
                    "brand_name": "PureFoods",
                    "product_name": "Pure Mountain Wild Honey 500g",
                    "category": "food",
                    "manufacturer_name": "PureFoods India Pvt Ltd",
                    "manufacturer_address": "Plot 42, Agro Industrial Estate, Pune, Maharashtra 411014",
                    "registered_by_business": business,
                },
                {
                    "gtin_barcode": "8902345678901",
                    "brand_name": "PureFoods",
                    "product_name": "Organic Turmeric Powder 200g",
                    "category": "food",
                    "manufacturer_name": "PureFoods India Pvt Ltd",
                    "manufacturer_address": "Plot 42, Agro Industrial Estate, Pune, Maharashtra 411014",
                    "registered_by_business": business,
                },
                {
                    "gtin_barcode": "8903456789012",
                    "brand_name": "SoundPro",
                    "product_name": "BassWave Wireless ANC Earbuds",
                    "category": "electronics",
                    "manufacturer_name": "SoundPro Electronics Ltd",
                    "manufacturer_address": "Sector 18, Electronic City, Gurugram, Haryana 122015",
                    "registered_by_business": None,
                },
                {
                    "gtin_barcode": "8904567890123",
                    "brand_name": "HealthFirst",
                    "product_name": "Infrared Non-Contact Digital Thermometer",
                    "category": "medical_device",
                    "manufacturer_name": "HealthFirst Medical Devices Corp",
                    "manufacturer_address": "Plot 12, Biotech Park, Genome Valley, Hyderabad 500078",
                    "registered_by_business": None,
                },
                {
                    "gtin_barcode": "8905678901234",
                    "brand_name": "Mediterra",
                    "product_name": "Extra Virgin Cold Pressed Olive Oil 1L",
                    "category": "import",
                    "manufacturer_name": "Olearia del Garda S.p.A., Italy (Imported by GlobalFoods Delhi)",
                    "manufacturer_address": "Via Falcone 12, 37011 Bardolino, Italy / Delhi 110020",
                    "registered_by_business": None,
                },
                {
                    "gtin_barcode": "8906789012345",
                    "brand_name": "DailyDelight",
                    "product_name": "Premium CTC Assam Tea 1kg",
                    "category": "food",
                    "manufacturer_name": "DailyDelight Beverages Pvt Ltd",
                    "manufacturer_address": "Tea Estate Road, Dibrugarh, Assam 786001",
                    "registered_by_business": None,
                },
                {
                    "gtin_barcode": "8907890123456",
                    "brand_name": "SparkleMax",
                    "product_name": "Multi-Action Detergent Powder 2kg",
                    "category": "general",
                    "manufacturer_name": "SparkleMax Hygiene Products",
                    "manufacturer_address": "GIDC Industrial Area, Vapi, Gujarat 396195",
                    "registered_by_business": None,
                },
                {
                    "gtin_barcode": "8908901234567",
                    "brand_name": "TechNova",
                    "product_name": "PulseFit Pro Smartwatch",
                    "category": "electronics",
                    "manufacturer_name": "TechNova Wearables Ltd",
                    "manufacturer_address": "Whitefield Main Road, Bengaluru, Karnataka 560066",
                    "registered_by_business": None,
                },
            ]

            products = []
            for p_dict in products_data:
                p, _ = Product.objects.update_or_create(
                    gtin_barcode=p_dict["gtin_barcode"],
                    defaults=p_dict,
                )
                products.append(p)

            p_honey, p_turmeric, p_earbuds, p_thermo, p_olive, p_tea, p_detergent, p_watch = products

            # -----------------------------------------------------------------
            # 2. Scans, ScanImages, ExtractedFields
            # -----------------------------------------------------------------
            self.stdout.write("  -> Seeding Scans and OCR Extractions...")
            # Scan 1: Officer scan on PureFoods Honey (Non-compliant: missing mfg_date & net_quantity font small)
            scan1 = Scan.objects.create(
                product=p_honey,
                performed_by=officer,
                role_context="officer",
                location="Connaught Place Retail Store, New Delhi",
                capture_method="guided_capture",
                status="reviewed",
            )
            ScanImage.objects.create(
                scan=scan1,
                image_url="https://images.unsplash.com/photo-1587049352846-4a222e784d38?w=800",
                angle_type="front_panel",
                quality_check_passed=True,
            )
            ScanImage.objects.create(
                scan=scan1,
                image_url="https://images.unsplash.com/photo-1587049352846-4a222e784d38?w=800",
                angle_type="declaration_panel",
                quality_check_passed=True,
            )
            ExtractedField.objects.create(
                scan=scan1, field_type="mrp", extracted_value="₹350 (Incl. of all taxes)",
                confidence_score=0.95, font_size_mm=3.2, placement_zone="declaration_panel"
            )
            ExtractedField.objects.create(
                scan=scan1, field_type="net_quantity", extracted_value="500g",
                confidence_score=0.91, font_size_mm=1.5, placement_zone="declaration_panel"  # too small (<2.0mm)
            )
            ExtractedField.objects.create(
                scan=scan1, field_type="manufacturer_name", extracted_value="PureFoods India Pvt Ltd",
                confidence_score=0.98, font_size_mm=2.5, placement_zone="declaration_panel"
            )
            ExtractedField.objects.create(
                scan=scan1, field_type="manufacturer_address",
                extracted_value="Plot 42, Agro Industrial Estate, Pune, Maharashtra",
                confidence_score=0.94, font_size_mm=2.2, placement_zone="declaration_panel"
            )
            ExtractedField.objects.create(
                scan=scan1, field_type="consumer_care_details",
                extracted_value="care@purefoods.in, Toll-Free: 1800-111-222",
                confidence_score=0.89, font_size_mm=2.0, placement_zone="declaration_panel"
            )

            # Scan 2: Citizen scan on Mediterra Olive Oil (Non-compliant: missing country of origin)
            scan2 = Scan.objects.create(
                product=p_olive,
                performed_by=citizen,
                role_context="citizen",
                location="Supermarket Bandra, Mumbai",
                capture_method="single_image",
                status="processed",
            )
            ScanImage.objects.create(
                scan=scan2,
                image_url="https://images.unsplash.com/photo-1474979266404-7eaacbcd87c5?w=800",
                angle_type="front_panel",
                quality_check_passed=True,
            )
            ExtractedField.objects.create(
                scan=scan2, field_type="mrp", extracted_value="₹1,250",
                confidence_score=0.93, font_size_mm=4.0, placement_zone="front_panel"
            )
            ExtractedField.objects.create(
                scan=scan2, field_type="net_quantity", extracted_value="1 Litre",
                confidence_score=0.96, font_size_mm=3.5, placement_zone="front_panel"
            )

            # Scan 3: Officer scan on SoundPro Earbuds (Compliant)
            scan3 = Scan.objects.create(
                product=p_earbuds,
                performed_by=officer,
                role_context="officer",
                location="Electronics Hub, Nehru Place, New Delhi",
                capture_method="guided_capture",
                status="reviewed",
            )
            ScanImage.objects.create(
                scan=scan3,
                image_url="https://images.unsplash.com/photo-1590658268037-6bf12165a8df?w=800",
                angle_type="declaration_panel",
                quality_check_passed=True,
            )
            ExtractedField.objects.create(
                scan=scan3, field_type="mrp", extracted_value="₹2,499 (Incl. of all taxes)",
                confidence_score=0.97, font_size_mm=3.0, placement_zone="declaration_panel"
            )
            ExtractedField.objects.create(
                scan=scan3, field_type="mfg_date", extracted_value="02/2026",
                confidence_score=0.94, font_size_mm=2.5, placement_zone="declaration_panel"
            )
            ExtractedField.objects.create(
                scan=scan3, field_type="net_quantity", extracted_value="1 Unit (Earbuds with Case)",
                confidence_score=0.95, font_size_mm=2.8, placement_zone="declaration_panel"
            )
            ExtractedField.objects.create(
                scan=scan3, field_type="manufacturer_name", extracted_value="SoundPro Electronics Ltd",
                confidence_score=0.98, font_size_mm=2.6, placement_zone="declaration_panel"
            )
            ExtractedField.objects.create(
                scan=scan3, field_type="manufacturer_address",
                extracted_value="Sector 18, Electronic City, Gurugram, Haryana",
                confidence_score=0.96, font_size_mm=2.2, placement_zone="declaration_panel"
            )
            ExtractedField.objects.create(
                scan=scan3, field_type="consumer_care_details",
                extracted_value="support@soundpro.com, Tel: 011-4567890",
                confidence_score=0.91, font_size_mm=2.1, placement_zone="declaration_panel"
            )

            # -----------------------------------------------------------------
            # 3. Compliance Checks, Violations, History
            # -----------------------------------------------------------------
            self.stdout.write("  -> Seeding Compliance Checks and Violations...")
            rule_mfg = Rule.objects.filter(rule_id_code__icontains="MFGDATE-V2").first() or Rule.objects.first()
            rule_font = Rule.objects.filter(rule_id_code__icontains="NETQTY-FONTSIZE").first() or Rule.objects.first()
            rule_coo = Rule.objects.filter(rule_id_code__icontains="COO-IMPORT").first() or Rule.objects.first()

            # Check 1 on Scan 1 (Non-compliant)
            cc1 = ComplianceCheck.objects.create(
                scan=scan1,
                verdict="non_compliant",
                overall_confidence=0.92,
                evaluated_against_rule_set_date=today,
                reviewed_by_officer=officer,
            )
            v1 = Violation.objects.create(
                compliance_check=cc1,
                rule=rule_mfg,
                description="Month and year of manufacture is missing on package declaration panel.",
                evidence_image=scan1.images.first(),
            )
            v2 = Violation.objects.create(
                compliance_check=cc1,
                rule=rule_font,
                description="Net quantity numeral font size is 1.5mm, which is below the mandatory minimum of 2.0mm.",
                evidence_image=scan1.images.first(),
            )

            # Check 2 on Scan 2 (Non-compliant)
            cc2 = ComplianceCheck.objects.create(
                scan=scan2,
                verdict="non_compliant",
                overall_confidence=0.88,
                evaluated_against_rule_set_date=today,
                reviewed_by_officer=None,
            )
            v3 = Violation.objects.create(
                compliance_check=cc2,
                rule=rule_coo,
                description="Imported food package lacks mandatory Country of Origin declaration.",
                evidence_image=scan2.images.first(),
            )

            # Check 3 on Scan 3 (Compliant)
            cc3 = ComplianceCheck.objects.create(
                scan=scan3,
                verdict="compliant",
                overall_confidence=0.96,
                evaluated_against_rule_set_date=today,
                reviewed_by_officer=officer,
            )

            # -----------------------------------------------------------------
            # 4. Cases, Improvement Notices, Penalty Cases
            # -----------------------------------------------------------------
            self.stdout.write("  -> Seeding Enforcement Cases...")
            # Case 1: First-time procedural violation for PureFoods Honey -> Improvement Notice
            case1 = Case.objects.create(
                violation=v1,
                product=p_honey,
                classification="first_time",
                status="notice_sent",
                opened_by=officer,
            )
            ProductComplianceHistory.objects.create(
                product=p_honey,
                violation=v1,
                is_first_time=True,
                case=case1,
            )
            ProductComplianceHistory.objects.create(
                product=p_honey,
                violation=v2,
                is_first_time=True,
                case=case1,
            )
            ImprovementNotice.objects.create(
                case=case1,
                issued_by=officer,
                rectification_deadline=today + timedelta(days=30),
                business_response="We have recalled non-compliant batch and updated the label die to 2.5mm font height.",
                verified_by=None,
                outcome="pending",
            )

            # Case 2: Repeat violation for SparkleMax Detergent -> Escalated Penalty Case
            case2 = Case.objects.create(
                product=p_detergent,
                classification="repeat",
                status="escalated",
                opened_by=officer,
            )
            ProductComplianceHistory.objects.create(
                product=p_detergent,
                violation=None,
                is_first_time=False,
                case=case2,
            )
            PenaltyCase.objects.create(
                case=case2,
                escalated_by=officer,
                approved_by_controller=controller,
                payment_status="pending",
                appeal_status="none",
            )

            # -----------------------------------------------------------------
            # 5. Complaints
            # -----------------------------------------------------------------
            self.stdout.write("  -> Seeding Citizen Complaints...")
            complaint1 = Complaint.objects.create(
                filed_by=citizen,
                product=p_tea,
                description="The tea packet purchased at local grocery does not have MRP printed clearly; shopkeeper charged ₹450 instead of standard rate.",
                photo_urls=[
                    "https://images.unsplash.com/photo-1544787219-7f47ccb76574?w=800"
                ],
                location="Sector 62, Noida, Uttar Pradesh",
                risk_score=78.5,
                routed_to_state="Uttar Pradesh",
                status="under_investigation",
            )
            complaint2 = Complaint.objects.create(
                filed_by=citizen,
                product=p_turmeric,
                description="Purchased turmeric powder packet with no manufacturing date or best before date.",
                photo_urls=[],
                location="Karol Bagh, New Delhi",
                risk_score=65.0,
                routed_to_state="Delhi",
                status="open",
            )

            # -----------------------------------------------------------------
            # 6. Inspection Targets
            # -----------------------------------------------------------------
            self.stdout.write("  -> Seeding Inspection Targets...")
            InspectionTarget.objects.create(
                product=p_tea,
                assigned_to=officer,
                source="complaint",
                priority_score=85.0,
                complaint=complaint1,
                status="in_progress",
            )
            InspectionTarget.objects.create(
                product=p_watch,
                assigned_to=officer,
                source="risk_engine",
                priority_score=92.4,
                complaint=None,
                status="pending",
            )
            InspectionTarget.objects.create(
                product=p_olive,
                assigned_to=officer,
                source="ecommerce_flag",
                priority_score=74.0,
                complaint=None,
                status="pending",
            )

            # -----------------------------------------------------------------
            # 7. Reports
            # -----------------------------------------------------------------
            self.stdout.write("  -> Seeding Reports...")
            Report.objects.create(
                case=case1,
                file_url="https://storage.legalmetro.gov.in/reports/case_1_notice.pdf",
                format="pdf",
                signed=True,
            )
            Report.objects.create(
                case=case2,
                file_url="https://storage.legalmetro.gov.in/reports/case_2_penalty_packet.pdf",
                format="pdf",
                signed=False,
            )

            # -----------------------------------------------------------------
            # 8. E-commerce Listings
            # -----------------------------------------------------------------
            self.stdout.write("  -> Seeding E-commerce Listings...")
            EcommerceListing.objects.create(
                platform_name="QuickCart",
                product=p_honey,
                raw_listing_data={
                    "seller_name": "Organic Greens Retail",
                    "listing_mrp": 350,
                    "unit_sale_price": "₹0.70 / g",
                    "country_of_origin": "India",
                    "url": "https://quickcart.in/p/purefoods-honey-500g",
                },
                screening_result="compliant",
            )
            EcommerceListing.objects.create(
                platform_name="QuickCart",
                product=p_olive,
                raw_listing_data={
                    "seller_name": "EuroImports Direct",
                    "listing_mrp": 1250,
                    "unit_sale_price": "₹1.25 / ml",
                    "country_of_origin": "Unknown",
                    "url": "https://quickcart.in/p/mediterra-olive-oil-1l",
                },
                screening_result="flagged",
                flagged_reason="Missing mandatory Country of Origin on digital product display page.",
            )
            EcommerceListing.objects.create(
                platform_name="QuickCart",
                product=p_thermo,
                raw_listing_data={
                    "seller_name": "HealthPlus MedStore",
                    "listing_mrp": 1999,
                    "url": "https://quickcart.in/p/healthfirst-thermometer",
                },
                screening_result="pending",
            )

            # -----------------------------------------------------------------
            # 9. Notifications
            # -----------------------------------------------------------------
            self.stdout.write("  -> Seeding Notifications...")
            notifications_data = [
                (business, "notice", "Improvement Notice #1 served for Pure Mountain Wild Honey 500g. 30 days to rectify."),
                (officer, "inspection_assigned", "New high-priority inspection assigned for Premium CTC Assam Tea 1kg."),
                (controller, "penalty", "Penalty Case #2 for SparkleMax Detergent escalated for Controller review and approval."),
                (citizen, "complaint_update", "Your complaint #1 regarding Assam Tea is now Under Investigation by Delhi Field Unit."),
                (admin, "system", "National Compliance index increased by 2.4% following automated e-commerce screening."),
                (ecommerce, "notice", "1 listing flagged for Legal Metrology compliance review on QuickCart marketplace."),
                (ruleadmin, "rule_published", "Rule PCR2025-MEDDEV-PDP-EXEMPT successfully activated in the Rules Repository."),
            ]
            for u, n_type, msg in notifications_data:
                Notification.objects.create(
                    user=u,
                    type=n_type,
                    message=msg,
                    read=False,
                )

            # -----------------------------------------------------------------
            # 10. Audit Logs
            # -----------------------------------------------------------------
            self.stdout.write("  -> Seeding Audit Logs...")
            audit_events = [
                (ruleadmin, "publish", "Rule", rule_mfg.pk, {"rule_id_code": rule_mfg.rule_id_code}),
                (officer, "create_scan", "Scan", scan1.pk, {"product": p_honey.product_name, "verdict": "non_compliant"}),
                (officer, "issue_notice", "Case", case1.pk, {"deadline_days": 30, "action": "Improvement Notice Served"}),
                (citizen, "file_complaint", "Complaint", complaint1.pk, {"risk_score": 78.5, "state": "Uttar Pradesh"}),
                (controller, "approve_escalation", "PenaltyCase", case2.penalty_case.pk, {"case_id": case2.pk}),
                (ecommerce, "bulk_upload", "EcommerceListing", 3, {"total_screened": 3, "flagged": 1}),
            ]
            for user_obj, action, t_type, t_id, meta in audit_events:
                AuditLog.objects.create(
                    user=user_obj,
                    action=action,
                    target_type=t_type,
                    target_id=str(t_id),
                    metadata=meta,
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"\nDemo data seeding complete! Summary:\n"
                f"  - Products: {Product.objects.count()}\n"
                f"  - Scans: {Scan.objects.count()}\n"
                f"  - Scan Images: {ScanImage.objects.count()}\n"
                f"  - Extracted Fields: {ExtractedField.objects.count()}\n"
                f"  - Compliance Checks: {ComplianceCheck.objects.count()}\n"
                f"  - Violations: {Violation.objects.count()}\n"
                f"  - Compliance History: {ProductComplianceHistory.objects.count()}\n"
                f"  - Cases: {Case.objects.count()}\n"
                f"  - Improvement Notices: {ImprovementNotice.objects.count()}\n"
                f"  - Penalty Cases: {PenaltyCase.objects.count()}\n"
                f"  - Complaints: {Complaint.objects.count()}\n"
                f"  - Inspection Targets: {InspectionTarget.objects.count()}\n"
                f"  - Reports: {Report.objects.count()}\n"
                f"  - E-commerce Listings: {EcommerceListing.objects.count()}\n"
                f"  - Notifications: {Notification.objects.count()}\n"
                f"  - Audit Logs: {AuditLog.objects.count()}\n"
            )
        )
