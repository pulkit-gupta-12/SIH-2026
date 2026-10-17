from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("inspections", "0001_initial"),
        ("scans", "0003_scan_canonical_data"),
    ]

    operations = [
        migrations.AddField(
            model_name="inspectiontarget",
            name="scan",
            field=models.OneToOneField(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="inspection_target",
                to="scans.scan",
            ),
        ),
        migrations.AlterField(
            model_name="inspectiontarget",
            name="source",
            field=models.CharField(
                choices=[
                    ("risk_engine", "Risk Engine Prioritization"),
                    ("complaint", "Citizen Complaint"),
                    ("ecommerce_flag", "E-commerce Flagged Listing"),
                    ("guided_capture", "Guided Capture Verification"),
                ],
                max_length=50,
            ),
        ),
    ]
