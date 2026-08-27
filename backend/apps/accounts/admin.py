from django.contrib import admin
from .models import User, Role, RoleAssignment


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("username", "email", "get_full_name", "is_active", "created_at")
    list_filter = ("is_active", "role_assignments__role__name")
    search_fields = ("username", "email", "first_name", "last_name")


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ("name", "get_name_display")


@admin.register(RoleAssignment)
class RoleAssignmentAdmin(admin.ModelAdmin):
    list_display = ("user", "role", "state", "organization")
    list_filter = ("role__name",)
