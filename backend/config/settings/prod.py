"""
Production settings — extends base.py for cloud deployment (Render).
"""
import os
from .base import *

DEBUG = False

# 1. Secret key from Render environment variable
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", SECRET_KEY)

# 2. Allowed hosts (Render assigns *.onrender.com)
ALLOWED_HOSTS = os.environ.get(
    "DJANGO_ALLOWED_HOSTS", 
    "localhost,127.0.0.1,.onrender.com"
).split(",")

# 3. Trust Render's reverse proxy for HTTPS redirect / scheme detection
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# 4. CORS & CSRF configuration for Vercel
CORS_ALLOW_CREDENTIALS = True
cors_origins = os.environ.get("CORS_ALLOWED_ORIGINS", "")
if cors_origins:
    CORS_ALLOWED_ORIGINS = [o.strip() for o in cors_origins.split(",") if o.strip()]
else:
    CORS_ALLOW_ALL_ORIGINS = True  # Useful for initial verification

csrf_origins = os.environ.get("CSRF_TRUSTED_ORIGINS", "")
if csrf_origins:
    CSRF_TRUSTED_ORIGINS = [o.strip() for o in csrf_origins.split(",") if o.strip()]
else:
    CSRF_TRUSTED_ORIGINS = ["https://*.onrender.com", "https://*.vercel.app"]

# 5. Static files with WhiteNoise (Django 5.1 standard syntax)
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
