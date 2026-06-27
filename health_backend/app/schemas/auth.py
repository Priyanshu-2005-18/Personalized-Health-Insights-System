from typing import Optional
from pydantic import EmailStr, Field, field_validator, model_validator
from app.schemas.common import BaseSchema


class RegisterRequest(BaseSchema):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    # Support both full_name and first_name/last_name
    full_name: Optional[str] = Field(default=None, max_length=200)
    first_name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    # Optional fields from frontend (ignored by backend)
    username: Optional[str] = Field(default=None, max_length=100)
    confirm_password: Optional[str] = Field(default=None)

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v

    @model_validator(mode="after")
    def resolve_name(self) -> "RegisterRequest":
        """Resolve full_name into first_name/last_name if not explicitly provided."""
        if self.first_name is None or self.last_name is None:
            if self.full_name:
                parts = self.full_name.strip().split(" ", 1)
                self.first_name = parts[0]
                self.last_name = parts[1] if len(parts) > 1 else parts[0]
            else:
                # Use email prefix as fallback
                prefix = self.email.split("@")[0]
                self.first_name = prefix
                self.last_name = prefix
        return self


class LoginRequest(BaseSchema):
    email: EmailStr
    password: str


class TokenResponse(BaseSchema):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseSchema):
    refresh_token: str


class LogoutRequest(BaseSchema):
    refresh_token: str
