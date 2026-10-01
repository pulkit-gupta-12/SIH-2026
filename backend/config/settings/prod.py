"""Production settings for a Render-hosted Django service."""
import os

from .base import *  # noqa: F401, F403

DEBUG = False

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "")
if not SECRET_KEY or SECRET_KEY.startswith("django-insecure-"):`r`n    raise RuntimeError("DJANGO_SECRET_KEY must be set in production.")`r`n`r`nif not os.environ.get("DATABASE_URL"):`r`n    raise RuntimeError("DATABASE_URL must be set in production.")

allowed_hosts = os.environ.get("DJANGO_ALLOWED_HOSTS")
if allowed_hosts:
    ALLOWED_HOSTS = [host.strip() for host in allowed_hosts.split(",") if host.strip()]
else:
    render_hostname = os.environ.get("RENDER_EXTERNAL_HOSTNAME")
    ALLOWED_HOSTS = ["localhost", "127.0.0.1", ".onrender.com"]
    if render_hostname:
        ALLOWED_HOSTS.append(render_hostname)

CORS_ALLOW_CREDENTIALS = True
cors_origins = os.environ.get("CORS_ALLOWED_ORIGINS", "")
if cors_origins:
    CORS_ALLOWED_ORIGINS = [
        origin.strip() for origin in cors_origins.split(",") if origin.strip()
    ]
else:
    frontend_url = os.environ.get("FRONTEND_URL")
    CORS_ALLOWED_ORIGINS = [frontend_url] if frontend_url else []

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

csrf_origins = os.environ.get("CSRF_TRUSTED_ORIGINS", "")
CSRF_TRUSTED_ORIGINS = (
    [origin.strip() for origin in csrf_origins.split(",") if origin.strip()]
    if csrf_origins
    else ["https://*.onrender.com", "https://*.vercel.app"]
)

if "whitenoise.middleware.WhiteNoiseMiddleware" not in MIDDLEWARE:
    MIDDLEWARE.insert(1, "whitenoise.middleware.WhiteNoiseMiddleware")

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

