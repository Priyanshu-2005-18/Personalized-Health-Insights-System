import uuid
from datetime import date, datetime
from typing import TYPE_CHECKING, Optional
from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, Integer, Numeric, SmallInteger, Text, UniqueConstraint, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.user import User


class HealthLog(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "health_logs"
    __table_args__ = (
        UniqueConstraint("user_id", "log_date", name="uq_health_log_user_date"),
        CheckConstraint("mood_score BETWEEN 1 AND 10", name="chk_mood_score"),
        CheckConstraint("stress_level BETWEEN 1 AND 10", name="chk_stress_level"),
        CheckConstraint("energy_level BETWEEN 1 AND 10", name="chk_energy_level"),
        CheckConstraint("water_ml >= 0", name="chk_water_ml"),
        CheckConstraint("sleep_hours >= 0.0 AND sleep_hours <= 24.0", name="chk_sleep_hours"),
        CheckConstraint("steps >= 0 AND steps <= 100000", name="chk_steps"),
        CheckConstraint("calories >= 0 AND calories <= 10000", name="chk_calories"),
        CheckConstraint("heart_rate_bpm >= 30 AND heart_rate_bpm <= 250", name="chk_heart_rate"),
        CheckConstraint("health_score >= 0.0 AND health_score <= 100.0", name="chk_health_score"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    log_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    mood_score: Mapped[Optional[int]] = mapped_column(SmallInteger, nullable=True)
    stress_level: Mapped[Optional[int]] = mapped_column(SmallInteger, nullable=True)
    energy_level: Mapped[Optional[int]] = mapped_column(SmallInteger, nullable=True)
    water_ml: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    sleep_hours: Mapped[Optional[float]] = mapped_column(Numeric(4, 2), nullable=True)
    steps: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    calories: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    heart_rate_bpm: Mapped[Optional[int]] = mapped_column(SmallInteger, nullable=True)
    health_score: Mapped[Optional[float]] = mapped_column(Numeric(5, 2), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    user: Mapped["User"] = relationship("User", back_populates="health_logs")
