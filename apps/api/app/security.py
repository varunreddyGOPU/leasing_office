"""Password hashing (stdlib scrypt) and signed session tokens (HMAC).
No external crypto deps; secret comes from SECRET_KEY env var."""
from __future__ import annotations

import base64
import hashlib
import hmac
import os
import time

from app.config import settings

SESSION_TTL_SECONDS = 7 * 24 * 3600
COOKIE_NAME = "portal_session"


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    digest = hashlib.scrypt(password.encode(), salt=salt, n=16384, r=8, p=1)
    return "scrypt$" + base64.b64encode(salt).decode() + "$" + base64.b64encode(digest).decode()


def verify_password(password: str, stored: str | None) -> bool:
    if not stored or not stored.startswith("scrypt$"):
        return False
    try:
        _, salt_b64, digest_b64 = stored.split("$")
        salt = base64.b64decode(salt_b64)
        expected = base64.b64decode(digest_b64)
    except ValueError:
        return False
    actual = hashlib.scrypt(password.encode(), salt=salt, n=16384, r=8, p=1)
    return hmac.compare_digest(actual, expected)


def make_session_token(resident_id: int) -> str:
    payload = f"{resident_id}.{int(time.time()) + SESSION_TTL_SECONDS}"
    sig = hmac.new(settings.secret_key.encode(), payload.encode(), hashlib.sha256).hexdigest()
    return f"{payload}.{sig}"


def parse_session_token(token: str) -> int | None:
    try:
        resident_id, expires, sig = token.split(".")
    except ValueError:
        return None
    payload = f"{resident_id}.{expires}"
    expected = hmac.new(settings.secret_key.encode(), payload.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(sig, expected):
        return None
    try:
        if int(expires) < time.time():
            return None
        return int(resident_id)
    except ValueError:
        return None
