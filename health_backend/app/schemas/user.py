from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import EmailStr, model_validator
from app.models.user import UserRole
from app.schemas.common import BaseSchema


class UserRead(BaseSchema):
    id: UUID
    email: EmailStr
    role: UserRole
    is_active: bool
    is_verified: bool
    last_login_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    # Computed fields for frontend compatibility
    username: Optional[str] = None
    full_name: Optional[str] = None

    @model_validator(mode="after")
    def set_computed_fields(self) -> "UserRead":
        """Derive username from email prefix and set full_name."""
        if self.username is None:
            self.username = self.email.split("@")[0]
        return self


class UserUpdate(BaseSchema):
    email: Optional[EmailStr] = None
    is_active: Optional[bool] = None
