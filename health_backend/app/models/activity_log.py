import uuid
from datetime import date, datetime
from typing import TYPE_CHECKING, Optional
from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, Integer, Numeric, SmallInteger, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.user import User


class ActivityLog(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "activity_logs"
    __table_args__ = (
        CheckConstraint("duration_min > 0", name="chk_activity_duration"),
        CheckConstraint("calories_burned >= 0", name="chk_calories"),
        CheckConstraint("intensity BETWEEN 1 AND 5", name="chk_intensity"),
        CheckConstraint("steps >= 0", name="chk_steps"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    activity_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    activity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    duration_min: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    distance_m: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    calories_burned: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    intensity: Mapped[Optional[int]] = mapped_column(SmallInteger, nullable=True)
    steps: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    avg_heart_rate: Mapped[Optional[float]] = mapped_column(Numeric(5, 2), nullable=True)
    max_heart_rate: Mapped[Optional[float]] = mapped_column(Numeric(5, 2), nullable=True)
    source: Mapped[str] = mapped_column(String(30), nullable=False, default="manual")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    user: Mapped["User"] = relationship("User", back_populates="activity_logs")
