"""
security.py
===========
All cryptographic operations live here:
  - bcrypt password hashing  (passlib)
  - JWT access token creation (python-jose)
  - JWT refresh token creation
  - Token decoding & validation

Design choices:
  • bcrypt work-factor 12 — balanced between brute-force resistance and latency.
  • Access tokens are SHORT-lived (15 min default) to limit exposure.
  • Refresh tokens are LONG-lived (7 days) but stored hashed in the DB;
    they are rotated on every use so theft is detectable.
  • Token type claim ("type": "access" | "refresh") prevents using a
    refresh token where an access token is expected and vice-versa.
  • iat (issued-at) is included for token age auditing.
"""

import hashlib
from datetime import datetime, timedelta, timezone
from typing import Any, Literal, Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

# ── bcrypt context ─────────────────────────────────────────────────────────────
#   schemes list keeps old hashes verifiable while new ones use bcrypt only.
#   deprecated="auto" upgrades on next login transparently.
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12)


# ─────────────────────────────────────────────────────────────────────────────
#  Password helpers
# ─────────────────────────────────────────────────────────────────────────────

def hash_password(plain_password: str) -> str:
    """Return a bcrypt hash of *plain_password*."""
    return pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Constant-time comparison of *plain_password* against *hashed_password*.
    Returns True only when they match.
    """
    return pwd_context.verify(plain_password, hashed_password)


# ─────────────────────────────────────────────────────────────────────────────
#  JWT helpers
# ─────────────────────────────────────────────────────────────────────────────

TokenType = Literal["access", "refresh"]


def _build_token(
    subject: str,
    token_type: TokenType,
    expires_delta: timedelta,
    extra_claims: dict[str, Any] | None = None,
) -> str:
    """
    Internal factory — build and sign a JWT.

    Payload fields:
      sub   — subject (user UUID as string)
      type  — "access" | "refresh"  (prevents token confusion attacks)
      exp   — expiry timestamp
      iat   — issued-at timestamp
      + any extra_claims (e.g. role)
    """
    now = datetime.now(timezone.utc)
    payload: dict[str, Any] = {
        "sub": subject,
        "type": token_type,
        "iat": now,
        "exp": now + expires_delta,
        **(extra_claims or {}),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_access_token(
    subject: str,
    extra_claims: dict[str, Any] | None = None,
) -> str:
    """
    Create a short-lived access token.

    Args:
        subject:      user UUID string
        extra_claims: optional dict merged into the payload (e.g. {"role": "admin"})
    """
    return _build_token(
        subject=subject,
        token_type="access",
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        extra_claims=extra_claims,
    )


def create_refresh_token(subject: str) -> str:
    """
    Create a long-lived refresh token.
    No extra claims — refresh tokens are only used to obtain new access tokens.
    """
    return _build_token(
        subject=subject,
        token_type="refresh",
        expires_delta=timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )


def decode_token(token: str) -> Optional[dict[str, Any]]:
    """
    Decode and validate a JWT.

    Returns the payload dict on success, None if the token is:
      - expired
      - tampered / invalid signature
      - malformed
    Callers must check the "type" claim themselves.
    """
    try:
        return jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
    except JWTError:
        return None


def hash_token(raw_token: str) -> str:
    """
    SHA-256 hash of a raw token for safe DB storage.
    Refresh tokens are never stored in plaintext.
    """
    return hashlib.sha256(raw_token.encode()).hexdigest()
