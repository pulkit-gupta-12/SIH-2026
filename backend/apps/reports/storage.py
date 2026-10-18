"""Helpers for checking locally stored report files."""
import os
from urllib.parse import unquote, urlsplit

from django.conf import settings
from django.core.exceptions import SuspiciousFileOperation
from django.utils._os import safe_join


def report_file_exists(report) -> bool:
    if not report.file_url:
        return False

    parsed_url = urlsplit(report.file_url)
    if parsed_url.scheme or parsed_url.netloc:
        return True

    media_prefix = f"/{settings.MEDIA_URL.strip('/')}/"
    if not parsed_url.path.startswith(media_prefix):
        return False

    relative_path = unquote(parsed_url.path[len(media_prefix):])
    try:
        file_path = safe_join(str(settings.MEDIA_ROOT), relative_path)
    except SuspiciousFileOperation:
        return False

    return os.path.isfile(file_path)
