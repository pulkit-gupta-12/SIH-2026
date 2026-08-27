"""
Accounts views — JWT endpoints + registration + user profile.
"""
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)
from .models import User
from .serializers import (
    CustomTokenObtainPairSerializer,
    UserMeSerializer,
    UserRegisterSerializer,
)


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


class UserRegisterView(generics.CreateAPIView):
    """
    POST /api/auth/register/ — create new user account with role.
    Returns access + refresh JWT tokens and user payload for immediate dashboard login.
    """
    serializer_class = UserRegisterSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class UserMeView(generics.RetrieveAPIView):
    """GET /api/auth/me/ — returns current user's profile with roles."""
    serializer_class = UserMeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user
