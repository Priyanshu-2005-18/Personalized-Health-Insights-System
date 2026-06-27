import uuid
import enum
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import JSON, Date, Enum, ForeignKey, Numeric, String, Uuid, func, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.user import User


class GenderType(str, enum.Enum):
    male = "male"
    female = "female"
    non_binary = "non_binary"
    prefer_not_to_say = "prefer_not_to_say"


class ActivityLevel(str, enum.Enum):
    sedentary = "sedentary"
    lightly_active = "lightly_active"
    moderately_active = "moderately_active"
    very_active = "very_active"
    extra_active = "extra_active"


class UserProfile(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "user_profiles"

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    date_of_birth: Mapped[Optional[datetime]] = mapped_column(Date, nullable=True)
    gender: Mapped[Optional[GenderType]] = mapped_column(Enum(GenderType), nullable=True)
    height_cm: Mapped[Optional[float]] = mapped_column(Numeric(5, 2), nullable=True)
    weight_kg: Mapped[Optional[float]] = mapped_column(Numeric(5, 2), nullable=True)
    activity_level: Mapped[Optional[ActivityLevel]] = mapped_column(
        Enum(ActivityLevel), nullable=True
    )
    health_goals: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    medical_conditions: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    avatar_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    timezone: Mapped[str] = mapped_column(String(60), nullable=False, default="UTC")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    user: Mapped["User"] = relationship("User", back_populates="profile")

    def __repr__(self) -> str:
        return f"<UserProfile user_id={self.user_id} name={self.first_name} {self.last_name}>"
