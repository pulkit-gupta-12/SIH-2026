"""
Accounts serializers — JWT customization and user detail.
"""
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import User, Role, RoleAssignment


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Extends the JWT token to include user's roles and name in the response.
    This avoids an extra /me endpoint call on every login.
    """

    def validate(self, attrs):
        data = super().validate(attrs)
        user = self.user
        data["user"] = {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "name": user.get_full_name() or user.username,
            "roles": user.active_roles,
        }
        return data


class RoleSerializer(serializers.ModelSerializer):
    display_name = serializers.CharField(source="get_name_display", read_only=True)

    class Meta:
        model = Role
        fields = ["id", "name", "display_name"]


class RoleAssignmentSerializer(serializers.ModelSerializer):
    role = RoleSerializer(read_only=True)

    class Meta:
        model = RoleAssignment
        fields = ["id", "role", "state", "organization"]


class UserSerializer(serializers.ModelSerializer):
    roles = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id", "username", "email", "first_name", "last_name",
            "phone", "is_active", "roles", "created_at",
        ]
        read_only_fields = ["id", "created_at"]

    def get_roles(self, obj):
        return obj.active_roles


class UserMeSerializer(serializers.ModelSerializer):
    """Full user detail including role assignments with metadata."""
    role_assignments = RoleAssignmentSerializer(many=True, read_only=True)
    roles = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id", "username", "email", "first_name", "last_name",
            "phone", "is_active", "roles", "role_assignments", "created_at",
        ]

    def get_roles(self, obj):
        return obj.active_roles
