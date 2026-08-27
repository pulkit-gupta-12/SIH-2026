"""
Accounts models: User, Role, RoleAssignment.
Matches schema from 05_Database_Schema.md.
"""
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Custom user extending AbstractUser.
    Fields: id, name (via first_name/last_name), email, phone, password (via AbstractUser), is_active, created_at.
    """
    phone = models.CharField(max_length=20, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "users"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.email})"

    @property
    def active_roles(self):
        """Return a list of role names this user has."""
        return list(
            self.role_assignments.values_list("role__name", flat=True)
        )


class Role(models.Model):
    """
    Predefined roles: citizen, field_officer, state_controller,
    national_admin, business, ecommerce_partner, rule_admin.
    """
    ROLE_CHOICES = [
        ("citizen", "Citizen"),
        ("field_officer", "Field Officer"),
        ("state_controller", "State Controller"),
        ("national_admin", "National Admin"),
        ("business", "Business"),
        ("ecommerce_partner", "E-commerce Partner"),
        ("rule_admin", "Rule Admin"),
    ]

    name = models.CharField(max_length=30, unique=True, choices=ROLE_CHOICES)

    class Meta:
        db_table = "roles"

    def __str__(self):
        return self.get_name_display()


class RoleAssignment(models.Model):
    """
    Links users to roles with optional metadata:
    - state: for officers/controllers (jurisdiction)
    - organization: for business/ecommerce (company name)
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="role_assignments",
    )
    role = models.ForeignKey(
        Role,
        on_delete=models.CASCADE,
        related_name="assignments",
    )
    state = models.CharField(max_length=100, blank=True, null=True)
    organization = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        db_table = "role_assignments"
        unique_together = ("user", "role")

    def __str__(self):
        extra = ""
        if self.state:
            extra = f" [{self.state}]"
        elif self.organization:
            extra = f" [{self.organization}]"
        return f"{self.user.username} → {self.role.name}{extra}"
