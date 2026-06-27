"""
schemas/auth.py
===============
Pydantic v2 schemas for every auth endpoint.

Naming convention:
  *Request  — incoming body validated on entry
  *Response — outgoing body, never exposes secrets

Security notes:
  • Passwords are validated for strength here, before hashing.
  • Tokens are never echoed back in error responses.
  • Email is normalised to lowercase to prevent duplicate accounts.
"""

import re
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    field_validator,
    model_validator,
)

# Minimum password requirements:
#   ≥ 8 chars, ≥ 1 uppercase, ≥ 1 lowercase, ≥ 1 digit, ≥ 1 special char
_PASSWORD_RE = re.compile(
    r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&_\-#^])[A-Za-z\d@$!%*?&_\-#^]{8,128}$"
)


class BaseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


# ─────────────────────────────────────────────────────────────────────────────
#  Sign-up
# ─────────────────────────────────────────────────────────────────────────────

class SignupRequest(BaseSchema):
    """Body accepted by POST /auth/signup."""

    email: EmailStr = Field(
        ...,
        examples=["user@example.com"],
        description="Valid email address — will be normalised to lowercase",
    )
    username: str = Field(
        ...,
        min_length=3,
        max_length=50,
        pattern=r"^[a-zA-Z0-9_\-]+$",
        examples=["john_doe"],
        description="3–50 chars, alphanumeric, underscores and hyphens only",
    )
    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        examples=["Str0ng@Pass!"],
        description="≥ 8 chars with upper, lower, digit, and special character",
    )
    confirm_password: str = Field(..., examples=["Str0ng@Pass!"])
    full_name: Optional[str] = Field(
        default=None,
        max_length=200,
        examples=["John Doe"],
    )

    @field_validator("email", mode="before")
    @classmethod
    def normalise_email(cls, v: str) -> str:
        return v.strip().lower()

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        if not _PASSWORD_RE.match(v):
            raise ValueError(
                "Password must be 8–128 characters and contain at least one "
                "uppercase letter, one lowercase letter, one digit, and one "
                "special character (@$!%*?&_-#^)"
            )
        return v

    @model_validator(mode="after")
    def passwords_must_match(self) -> "SignupRequest":
        if self.password != self.confirm_password:
            raise ValueError("Passwords do not match")
        return self


class SignupResponse(BaseSchema):
    """Returned after a successful registration."""
    id: UUID
    email: str
    username: str
    full_name: Optional[str]
    role: str
    is_active: bool
    is_verified: bool
    created_at: datetime
    # Tokens are issued immediately so the user can start using the API
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


# ─────────────────────────────────────────────────────────────────────────────
#  Login
# ─────────────────────────────────────────────────────────────────────────────

class LoginRequest(BaseSchema):
    """Body accepted by POST /auth/login."""
    email: EmailStr
    password: str = Field(..., min_length=1, max_length=128)

    @field_validator("email", mode="before")
    @classmethod
    def normalise_email(cls, v: str) -> str:
        return v.strip().lower()


class TokenResponse(BaseSchema):
    """Standard token pair response."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


# ─────────────────────────────────────────────────────────────────────────────
#  Token rotation / logout
# ─────────────────────────────────────────────────────────────────────────────

class RefreshRequest(BaseSchema):
    """Body accepted by POST /auth/refresh."""
    refresh_token: str = Field(..., min_length=10)


class LogoutRequest(BaseSchema):
    """Body accepted by POST /auth/logout."""
    refresh_token: str = Field(..., min_length=10)


# ─────────────────────────────────────────────────────────────────────────────
#  Password change
# ─────────────────────────────────────────────────────────────────────────────

class ChangePasswordRequest(BaseSchema):
    """Body accepted by POST /auth/change-password (authenticated route)."""
    current_password: str = Field(..., min_length=1, max_length=128)
    new_password: str = Field(..., min_length=8, max_length=128)
    confirm_new_password: str = Field(...)

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, v: str) -> str:
        if not _PASSWORD_RE.match(v):
            raise ValueError(
                "New password must be 8–128 characters with upper, lower, "
                "digit, and special character"
            )
        return v

    @model_validator(mode="after")
    def new_passwords_must_match(self) -> "ChangePasswordRequest":
        if self.new_password != self.confirm_new_password:
            raise ValueError("New passwords do not match")
        return self


# ─────────────────────────────────────────────────────────────────────────────
#  User read schema (safe — no password_hash exposed)
# ─────────────────────────────────────────────────────────────────────────────

class UserResponse(BaseSchema):
    """Safe representation of a user — never includes credentials."""
    id: UUID
    email: str
    username: str
    full_name: Optional[str]
    role: str
    is_active: bool
    is_verified: bool
    last_login_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime


class MessageResponse(BaseSchema):
    message: str
