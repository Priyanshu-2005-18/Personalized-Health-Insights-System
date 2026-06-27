import uuid
from datetime import date, datetime
from typing import TYPE_CHECKING, Optional
from sqlalchemy import JSON, CheckConstraint, Date, DateTime, ForeignKey, Integer, SmallInteger, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.user import User


class SleepLog(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "sleep_logs"
    __table_args__ = (
        CheckConstraint("wake_time > bedtime", name="chk_wake_after_bed"),
        CheckConstraint("quality_score BETWEEN 1 AND 10", name="chk_sleep_quality"),
        CheckConstraint("interruptions >= 0", name="chk_interruptions"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    sleep_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    bedtime: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    wake_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    duration_min: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    quality_score: Mapped[Optional[int]] = mapped_column(SmallInteger, nullable=True)
    sleep_stages: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    interruptions: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0)
    source: Mapped[str] = mapped_column(String(30), nullable=False, default="manual")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    user: Mapped["User"] = relationship("User", back_populates="sleep_logs")

    def compute_duration(self) -> int:
        delta = self.wake_time - self.bedtime
        return int(delta.total_seconds() / 60)
