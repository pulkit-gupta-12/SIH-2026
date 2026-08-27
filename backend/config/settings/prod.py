"""
Production settings — extends base.py.
Placeholder: configure before deploying.
"""
from .base import *  # noqa: F401, F403

DEBUG = False

# TODO: Set a real secret key via environment variable
# TODO: Configure ALLOWED_HOSTS properly
# TODO: Set up HTTPS, HSTS, secure cookies

CORS_ALLOWED_ORIGINS = [
    # Add production frontend URL here
]

# Use WhiteNoise for static files in production
MIDDLEWARE.insert(1, "whitenoise.middleware.WhiteNoiseMiddleware")  # noqa: F405
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"
