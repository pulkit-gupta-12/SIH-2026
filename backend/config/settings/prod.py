"""
Production settings for a Render-hosted Django service.
"""

import os

from .base import *  # noqa: F401, F403


DEBUG = False


# ---------------------------------------------------------------------------
# Production security
# ---------------------------------------------------------------------------

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "")

if not SECRET_KEY or SECRET_KEY.startswith("django-insecure-"):
    raise RuntimeError("DJANGO_SECRET_KEY must be set in production.")

if not os.environ.get("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL must be set in production.")


# ---------------------------------------------------------------------------
# Allowed hosts
# ---------------------------------------------------------------------------

def _hostnames_from_env(value):
    hosts = []

    for raw_host in value.split(","):
        host = raw_host.strip().lower()

        if not host:
            continue

        if "://" in host:
            host = host.split("://", 1)[1]

        host = host.split("/", 1)[0]

        if host.count(":") == 1:
            host = host.split(":", 1)[0]

        if host and host not in hosts:
            hosts.append(host)

    return hosts


ALLOWED_HOSTS = _hostnames_from_env(
    os.environ.get("DJANGO_ALLOWED_HOSTS", "")
)

render_hostname = os.environ.get(
    "RENDER_EXTERNAL_HOSTNAME",
    "",
).strip().lower()

if render_hostname and render_hostname not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append(render_hostname)

if not ALLOWED_HOSTS:
    ALLOWED_HOSTS = [
        "localhost",
        "127.0.0.1",
        ".onrender.com",
    ]


# ---------------------------------------------------------------------------
# CORS configuration for Vercel frontend
# ---------------------------------------------------------------------------

CORS_ALLOW_CREDENTIALS = True

cors_origins = os.environ.get(
    "CORS_ALLOWED_ORIGINS",
    "",
)

if cors_origins:
    CORS_ALLOWED_ORIGINS = [
        origin.strip()
        for origin in cors_origins.split(",")
        if origin.strip()
    ]
else:
    frontend_url = os.environ.get("FRONTEND_URL")

    CORS_ALLOWED_ORIGINS = (
        [frontend_url]
        if frontend_url
        else []
    )


# ---------------------------------------------------------------------------
# HTTPS / proxy configuration
# ---------------------------------------------------------------------------

SECURE_PROXY_SSL_HEADER = (
    "HTTP_X_FORWARDED_PROTO",
    "https",
)

SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True


# ---------------------------------------------------------------------------
# CSRF trusted origins
# ---------------------------------------------------------------------------

csrf_origins = os.environ.get(
    "CSRF_TRUSTED_ORIGINS",
    "",
)

CSRF_TRUSTED_ORIGINS = (
    [
        origin.strip()
        for origin in csrf_origins.split(",")
        if origin.strip()
    ]
    if csrf_origins
    else [
        "https://*.onrender.com",
        "https://*.vercel.app",
    ]
)


# ---------------------------------------------------------------------------
# Static files with WhiteNoise
# ---------------------------------------------------------------------------

if "whitenoise.middleware.WhiteNoiseMiddleware" not in MIDDLEWARE:
    MIDDLEWARE.insert(
        1,
        "whitenoise.middleware.WhiteNoiseMiddleware",
    )


STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}