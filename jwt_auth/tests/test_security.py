"""
tests/test_security.py
======================
Unit tests for the cryptographic functions in app/core/security.py.
These tests do NOT touch the database or HTTP layer.
"""

import time
import pytest
from jose import jwt

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    hash_token,
    verify_password,
)
from app.core.config import settings

pytestmark = pytest.mark.asyncio


# ─────────────────────────────────────────────────────────────────────────────
#  Password hashing
# ─────────────────────────────────────────────────────────────────────────────

def test_hash_password_returns_bcrypt_string():
    h = hash_password("MyPassword@1")
    assert h.startswith("$2b$")          # bcrypt prefix


def test_hash_is_not_plaintext():
    pw = "MyPassword@1"
    assert hash_password(pw) != pw


def test_hash_is_non_deterministic():
    """bcrypt uses a random salt — same input → different hash each time."""
    pw = "MyPassword@1"
    assert hash_password(pw) != hash_password(pw)


def test_verify_password_correct():
    pw = "Correct@Horse99"
    assert verify_password(pw, hash_password(pw)) is True


def test_verify_password_wrong():
    h = hash_password("Correct@Horse99")
    assert verify_password("WrongPass@99", h) is False


def test_verify_password_empty_wrong():
    h = hash_password("Valid@Password1")
    assert verify_password("", h) is False


# ─────────────────────────────────────────────────────────────────────────────
#  Access token
# ─────────────────────────────────────────────────────────────────────────────

def test_create_access_token_structure():
    token = create_access_token("user-123")
    payload = decode_token(token)
    assert payload is not None
    assert payload["sub"] == "user-123"
    assert payload["type"] == "access"
    assert "exp" in payload
    assert "iat" in payload


def test_create_access_token_with_extra_claims():
    token = create_access_token("user-abc", extra_claims={"role": "admin"})
    payload = decode_token(token)
    assert payload["role"] == "admin"


def test_access_token_expires_in_correct_window():
    token = create_access_token("user-xyz")
    payload = decode_token(token)
    window = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    remaining = payload["exp"] - payload["iat"]
    # Allow ±5 second tolerance for test execution time
    assert abs(remaining - window) <= 5


# ─────────────────────────────────────────────────────────────────────────────
#  Refresh token
# ─────────────────────────────────────────────────────────────────────────────

def test_create_refresh_token_type():
    token = create_refresh_token("user-999")
    payload = decode_token(token)
    assert payload["type"] == "refresh"


def test_refresh_token_longer_lived_than_access():
    access = create_access_token("u")
    refresh = create_refresh_token("u")
    ap = decode_token(access)
    rp = decode_token(refresh)
    assert rp["exp"] > ap["exp"]


# ─────────────────────────────────────────────────────────────────────────────
#  Token decoding
# ─────────────────────────────────────────────────────────────────────────────

def test_decode_valid_token():
    token = create_access_token("decode-me")
    payload = decode_token(token)
    assert payload is not None
    assert payload["sub"] == "decode-me"


def test_decode_invalid_token_returns_none():
    assert decode_token("not.a.token") is None


def test_decode_tampered_token_returns_none():
    token = create_access_token("tamper-test")
    # Flip a character in the signature segment
    parts = token.split(".")
    sig = parts[2]
    tampered_sig = sig[:-1] + ("X" if sig[-1] != "X" else "Y")
    bad_token = ".".join(parts[:2] + [tampered_sig])
    assert decode_token(bad_token) is None


def test_decode_wrong_secret_returns_none():
    """Token signed with a different secret must be rejected."""
    payload = {"sub": "user-1", "type": "access"}
    bad_token = jwt.encode(payload, "WRONG_SECRET", algorithm=settings.ALGORITHM)
    assert decode_token(bad_token) is None


def test_decode_expired_token_returns_none():
    """Manually craft a token with exp in the past."""
    from datetime import datetime, timezone, timedelta
    now = datetime.now(timezone.utc)
    payload = {
        "sub": "expired-user",
        "type": "access",
        "iat": now - timedelta(minutes=30),
        "exp": now - timedelta(minutes=15),  # already expired
    }
    expired_token = jwt.encode(
        payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )
    assert decode_token(expired_token) is None


# ─────────────────────────────────────────────────────────────────────────────
#  Token hash
# ─────────────────────────────────────────────────────────────────────────────

def test_hash_token_is_64_chars():
    """SHA-256 hex digest is always 64 characters."""
    h = hash_token("some-raw-token-value")
    assert len(h) == 64


def test_hash_token_is_deterministic():
    raw = "same-token"
    assert hash_token(raw) == hash_token(raw)


def test_different_tokens_have_different_hashes():
    assert hash_token("token-a") != hash_token("token-b")
