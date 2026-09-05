"""
Test settings — extends dev.py with in-memory SQLite for fast, isolated CI/local testing.
"""
from .dev import *  # noqa: F401, F403

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

# Faster password hashing for test execution speed
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

# Ensure real PaddleOCR settings are active
OCR_USE_MOCK = False
OCR_TIMEOUT_SECONDS = 30.0

# Disable live LLM network calls during automated test discovery
LLM_ENABLED = False

