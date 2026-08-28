"""
Role-based permission classes.
One permission class per role — compose on each viewset.
"""
from rest_framework.permissions import BasePermission


class _HasRole(BasePermission):
    """Base class: checks that the user has a specific role via their RoleAssignment."""
    required_role = None

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return request.user.role_assignments.filter(
            role__name=self.required_role
        ).exists()


class IsCitizen(_HasRole):
    required_role = "citizen"
    message = "Citizen role required."


class IsFieldOfficer(_HasRole):
    required_role = "field_officer"
    message = "Field Officer role required."


class IsStateController(_HasRole):
    required_role = "state_controller"
    message = "State Controller role required."


class IsNationalAdmin(_HasRole):
    required_role = "national_admin"
    message = "National Admin role required."


class IsBusiness(_HasRole):
    required_role = "business"
    message = "Business role required."


class IsEcommercePartner(_HasRole):
    required_role = "ecommerce_partner"
    message = "E-commerce Partner role required."


class IsRuleAdmin(_HasRole):
    required_role = "rule_admin"
    message = "Rule Admin role required."


class IsCitizenOrFieldOfficer(BasePermission):
    """Allow access to citizens and field officers (e.g. shared scan endpoint)."""
    message = "Citizen or Field Officer role required."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return request.user.role_assignments.filter(
            role__name__in=["citizen", "field_officer"]
        ).exists()


class IsOfficerOrController(BasePermission):
    """Allow access to field officers, state controllers, and national admins (e.g. cases and inspections)."""
    message = "Field Officer or Controller role required."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return request.user.role_assignments.filter(
            role__name__in=["field_officer", "state_controller", "national_admin"]
        ).exists()


