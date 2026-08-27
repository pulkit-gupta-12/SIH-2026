"""
Shared mixins for viewsets.
AuditLoggedMixin — writes to audit_logs on every state-changing action.
"""
from apps.notifications.models import AuditLog


class AuditLoggedMixin:
    """
    Mixin for DRF viewsets that automatically logs create/update/delete
    actions to the audit_logs table.
    """

    def perform_create(self, serializer):
        instance = serializer.save()
        self._write_audit_log("create", instance)
        return instance

    def perform_update(self, serializer):
        instance = serializer.save()
        self._write_audit_log("update", instance)
        return instance

    def perform_destroy(self, instance):
        self._write_audit_log("delete", instance)
        instance.delete()

    def _write_audit_log(self, action, instance, metadata=None):
        """Write an audit log entry."""
        user = getattr(self, "request", None) and self.request.user if getattr(self, "request", None) and self.request.user.is_authenticated else None
        AuditLog.objects.create(
            user=user,
            action=action,
            target_type=instance.__class__.__name__,
            target_id=str(instance.pk),
            metadata=metadata or {},
        )
