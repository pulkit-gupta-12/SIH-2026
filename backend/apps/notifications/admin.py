"""
Admin registration for notifications and audit_logs.
"""
from django.contrib import admin
from .models import Notification, AuditLog


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "type", "message", "read", "created_at")
    list_filter = ("type", "read", "created_at")
    search_fields = ("user__username", "message")


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "action", "target_type", "target_id", "created_at")
    list_filter = ("action", "target_type", "created_at")
    search_fields = ("user__username", "action", "target_type", "target_id")
