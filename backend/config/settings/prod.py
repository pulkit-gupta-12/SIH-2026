"""Production settings for a Render-hosted Django service."""
import os

from .base import *  # noqa: F401, F403

DEBUG = False

if SECRET_KEY.startswith("django-insecure-"):
    raise RuntimeError("DJANGO_SECRET_KEY must be set in production.")

if ALLOWED_HOSTS == ["*"]:
    render_hostname = os.environ.get("RENDER_EXTERNAL_HOSTNAME")
    if render_hostname:
        ALLOWED_HOSTS = [render_hostname]

frontend_url = os.environ.get("FRONTEND_URL")
CORS_ALLOWED_ORIGINS = [frontend_url] if frontend_url else []

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# Use WhiteNoise for static files in production
MIDDLEWARE.insert(1, "whitenoise.middleware.WhiteNoiseMiddleware")  # noqa: F405
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"
