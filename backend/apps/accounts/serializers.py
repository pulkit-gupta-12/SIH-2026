"""
Accounts serializers — JWT customization, registration, and user detail.
"""
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken
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


class UserRegisterSerializer(serializers.ModelSerializer):
    """
    Serializer for creating a new user account with role assignment.
    Returns access/refresh JWT tokens upon creation.
    """
    password = serializers.CharField(write_only=True, min_length=6)
    role = serializers.ChoiceField(
        choices=Role.ROLE_CHOICES,
        default="citizen",
        write_only=True,
    )
    state = serializers.CharField(
        max_length=100,
        required=False,
        allow_blank=True,
        write_only=True,
    )
    organization = serializers.CharField(
        max_length=255,
        required=False,
        allow_blank=True,
        write_only=True,
    )

    class Meta:
        model = User
        fields = [
            "id", "username", "password", "email", "first_name", "last_name",
            "phone", "role", "state", "organization",
        ]

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("A user with this username already exists.")
        return value

    def create(self, validated_data):
        role_name = validated_data.pop("role", "citizen")
        state = validated_data.pop("state", "") or None
        organization = validated_data.pop("organization", "") or None
        password = validated_data.pop("password")

        user = User.objects.create_user(
            password=password,
            **validated_data,
        )

        role, _ = Role.objects.get_or_create(name=role_name)
        RoleAssignment.objects.create(
            user=user,
            role=role,
            state=state,
            organization=organization,
        )

        return user

    def to_representation(self, instance):
        refresh = RefreshToken.for_user(instance)
        # Custom claims
        refresh["roles"] = instance.active_roles
        refresh["name"] = instance.get_full_name() or instance.username

        return {
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "user": {
                "id": instance.id,
                "username": instance.username,
                "email": instance.email,
                "name": instance.get_full_name() or instance.username,
                "roles": instance.active_roles,
            },
        }
