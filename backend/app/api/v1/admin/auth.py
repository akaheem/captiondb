"""
Admin authentication.

Self-contained credential verification and signed-token handling for the
admin console. Credentials are supplied via environment configuration
(ADMIN__EMAIL / ADMIN__PASSWORD_HASH) — never hardcoded.

Token format: HMAC-signed, stateless, independent of the (stubbed) user
auth providers so the admin console works without the full auth stack.
"""
import base64
import hashlib
import hmac
import json
import secrets
import time
from typing import Optional

from fastapi import Depends, HTTPException, Request, status

from app.core.config import get_settings


# ── Password verification (PBKDF2) ───────────────────────────────

def verify_admin_password(password: str, stored_hash: str) -> bool:
    """
    Verifies a password against a stored hash of the form:
        pbkdf2_sha256$<iterations>$<salt_hex>$<hash_hex>
    """
    try:
        algorithm, iterations, salt_hex, hash_hex = stored_hash.split("$")
        if algorithm != "pbkdf2_sha256":
            return False
        computed = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            bytes.fromhex(salt_hex),
            int(iterations),
        ).hex()
        return hmac.compare_digest(computed, hash_hex)
    except (ValueError, AttributeError):
        return False


# ── Signed admin token (HMAC, stateless) ─────────────────────────

def _sign(payload: bytes, secret: str) -> str:
    return hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()


def create_admin_token(email: str, expires_in_seconds: int) -> str:
    """Creates a compact HMAC-signed admin token: base64(payload).signature"""
    settings = get_settings()
    payload = json.dumps(
        {
            "sub": email,
            "scope": "admin",
            "exp": int(time.time()) + expires_in_seconds,
            "jti": secrets.token_hex(8),
        }
    ).encode("utf-8")
    encoded = base64.urlsafe_b64encode(payload).decode("ascii").rstrip("=")
    signature = _sign(payload, settings.security.secret_key)
    return f"{encoded}.{signature}"


def verify_admin_token(token: str) -> Optional[str]:
    """Verifies an admin token. Returns the admin email if valid, else None."""
    settings = get_settings()
    try:
        encoded, signature = token.rsplit(".", 1)
        padding = "=" * (-len(encoded) % 4)
        payload = base64.urlsafe_b64decode(encoded + padding)
        expected = _sign(payload, settings.security.secret_key)
        if not hmac.compare_digest(signature, expected):
            return None
        claims = json.loads(payload)
        if claims.get("scope") != "admin":
            return None
        if int(claims.get("exp", 0)) < int(time.time()):
            return None
        return claims.get("sub")
    except (ValueError, KeyError, json.JSONDecodeError):
        return None


# ── FastAPI dependency ───────────────────────────────────────────

def require_admin(request: Request) -> str:
    """
    Dependency guarding admin endpoints.
    Expects 'Authorization: Bearer <admin token>'.
    """
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "MISSING_TOKEN", "message": "Admin token required."},
            headers={"WWW-Authenticate": "Bearer"},
        )
    email = verify_admin_token(auth_header.removeprefix("Bearer ").strip())
    if email is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "INVALID_TOKEN", "message": "Admin token is invalid or expired."},
            headers={"WWW-Authenticate": "Bearer"},
        )
    return email
