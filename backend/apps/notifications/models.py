"""
Notifications & Audit Log models: Notification, AuditLog.
Matches schema from 05_Database_Schema.md.
"""
from django.conf import settings
from django.db import models


class Notification(models.Model):
    """
    Notifications table.
    Fields: id, user_id (FK), type, message, read (bool), created_at.
    """
    TYPE_CHOICES = [
        ("notice", "Improvement Notice"),
        ("penalty", "Penalty Notice"),
        ("complaint_update", "Complaint Update"),
        ("inspection_assigned", "Inspection Assigned"),
        ("rule_published", "New Rule Published"),
        ("system", "System Notification"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    type = models.CharField(max_length=50, choices=TYPE_CHOICES, default="system")
    message = models.TextField()
    read = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "notifications"
        ordering = ["-created_at"]

    def __str__(self):
        read_status = "Read" if self.read else "Unread"
        return f"Notification for {self.user.username}: {self.message[:40]} [{read_status}]"


class AuditLog(models.Model):
    """
    Audit Logs table.
    Fields: id, user_id (FK, nullable), action, target_type, target_id, metadata (JSONB), created_at.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_logs",
    )
    action = models.CharField(max_length=100, db_index=True)
    target_type = models.CharField(max_length=100, db_index=True)
    target_id = models.CharField(max_length=100, db_index=True)
    metadata = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "audit_logs"
        ordering = ["-created_at"]

    def __str__(self):
        user_str = self.user.username if self.user else "System"
        return f"[{self.created_at.strftime('%Y-%m-%d %H:%M')}] {user_str} performed '{self.action}' on {self.target_type}#{self.target_id}"
