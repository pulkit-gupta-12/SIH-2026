"""
Shared mixins for viewsets.
AuditLoggedMixin — writes to audit_logs on every state-changing action.
"""


class AuditLoggedMixin:
    """
    Mixin for DRF viewsets that automatically logs create/update/delete
    actions to the audit_logs table.

    Uses the notifications app's AuditLog model (created in Phase 2).
    In Phase 1, this is a no-op stub — the mixin is wired but the actual
    AuditLog model doesn't exist yet.
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

    def _write_audit_log(self, action, instance):
        """Write an audit log entry. Gracefully skips if AuditLog model not yet available."""
        try:
            from apps.notifications.models import AuditLog

            user = self.request.user if self.request.user.is_authenticated else None
            if user:
                AuditLog.objects.create(
                    user=user,
                    action=action,
                    target_type=instance.__class__.__name__,
                    target_id=str(instance.pk),
                    metadata={},
                )
        except Exception:
            # AuditLog model may not exist yet (Phase 1) — skip silently
            pass
