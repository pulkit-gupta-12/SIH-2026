"""
Serializers for Reports app.
"""
from rest_framework import serializers
from .models import Report


class ReportSerializer(serializers.ModelSerializer):
    report_code = serializers.SerializerMethodField()
    case_id = serializers.IntegerField(source="case.id", read_only=True, allow_null=True)
    compliance_check_id = serializers.IntegerField(source="compliance_check.id", read_only=True, allow_null=True)

    class Meta:
        model = Report
        fields = [
            "id",
            "report_code",
            "case",
            "case_id",
            "compliance_check",
            "compliance_check_id",
            "file_url",
            "format",
            "signed",
            "generated_at",
        ]
        read_only_fields = ["id", "report_code", "file_url", "format", "signed", "generated_at"]

    def get_report_code(self, obj):
        return f"LMR-{obj.id:05d}"
