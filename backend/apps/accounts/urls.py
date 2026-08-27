"""
Accounts URL configuration.
"""
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView
from .views import CustomTokenObtainPairView, UserMeView, UserRegisterView

urlpatterns = [
    path("login/", CustomTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("register/", UserRegisterView.as_view(), name="user_register"),
    path("refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("verify/", TokenVerifyView.as_view(), name="token_verify"),
    path("me/", UserMeView.as_view(), name="user_me"),
]
