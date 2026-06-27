"""
models/health_entry.py
======================
Central health-tracking table. One row = one day's snapshot for a user.

Metrics stored:
  ┌─────────────────────┬──────────────┬────────────────────────────────┐
  │ Field               │ Type         │ Valid range                    │
  ├─────────────────────┼──────────────┼────────────────────────────────┤
  │ sleep_hours         │ NUMERIC(4,2) │ 0.0 – 24.0 hours               │
  │ steps               │ INTEGER      │ 0 – 100 000 steps/day          │
  │ calories_consumed   │ INTEGER      │ 0 – 10 000 kcal/day            │
  │ water_intake_ml     │ INTEGER      │ 0 – 10 000 ml/day              │
  │ stress_level        │ SMALLINT     │ 1 (low) – 10 (extreme)         │
  │ heart_rate_bpm      │ SMALLINT     │ 30 – 250 bpm                   │
  └─────────────────────┴──────────────┴────────────────────────────────┘

Design decisions:
  - All metric columns are nullable so users can submit partial entries
    (e.g. log steps without logging calories).
  - UNIQUE constraint on (user_id, entry_date) → one row per user per day.
  - notes TEXT column for free-form daily journaling.
  - source VARCHAR tracks where the data came from (manual / wearable / app).
  - CHECK constraints are defined at the DB level as a second line of defence
    (Pydantic validators are the first line at the API level).
"""

import uuid
from datetime import date, datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, UUIDMixin

if TYPE_CHECKING:
    from app.models.user import User


class HealthEntry(Base, UUIDMixin):
    """One daily health snapshot per user."""

    __tablename__ = "health_entries"

    __table_args__ = (
        # Only one entry per user per calendar day
        UniqueConstraint("user_id", "entry_date", name="uq_health_entry_user_date"),

        # ── DB-level CHECK constraints ────────────────────────────────────────
        CheckConstraint("sleep_hours >= 0 AND sleep_hours <= 24",
                        name="chk_sleep_hours"),
        CheckConstraint("steps >= 0 AND steps <= 100000",
                        name="chk_steps"),
        CheckConstraint("calories_consumed >= 0 AND calories_consumed <= 10000",
                        name="chk_calories"),
        CheckConstraint("water_intake_ml >= 0 AND water_intake_ml <= 10000",
                        name="chk_water"),
        CheckConstraint("stress_level >= 1 AND stress_level <= 10",
                        name="chk_stress_level"),
        CheckConstraint("heart_rate_bpm >= 30 AND heart_rate_bpm <= 250",
                        name="chk_heart_rate"),
    )

    # ── Owner ─────────────────────────────────────────────────────────────────
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # ── Date ──────────────────────────────────────────────────────────────────
    entry_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
        comment="Calendar date this entry covers (UTC)",
    )

    # ── Metric 1: Sleep ───────────────────────────────────────────────────────
    sleep_hours: Mapped[Optional[float]] = mapped_column(
        Numeric(4, 2),
        nullable=True,
        comment="Total sleep in hours (0.00 – 24.00)",
    )

    # ── Metric 2: Steps ───────────────────────────────────────────────────────
    steps: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="Total steps walked/run that day",
    )

    # ── Metric 3: Calories consumed ───────────────────────────────────────────
    calories_consumed: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="Total dietary calories consumed (kcal)",
    )

    # ── Metric 4: Water intake ────────────────────────────────────────────────
    water_intake_ml: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="Total water consumed in millilitres",
    )

    # ── Metric 5: Stress level ────────────────────────────────────────────────
    stress_level: Mapped[Optional[int]] = mapped_column(
        SmallInteger,
        nullable=True,
        comment="Subjective stress score: 1 (none) – 10 (extreme)",
    )

    # ── Metric 6: Heart rate ──────────────────────────────────────────────────
    heart_rate_bpm: Mapped[Optional[int]] = mapped_column(
        SmallInteger,
        nullable=True,
        comment="Resting heart rate in beats per minute (30 – 250)",
    )

    # ── Optional metadata ─────────────────────────────────────────────────────
    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Free-form notes or journal for the day",
    )
    source: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="manual",
        comment="Data source: manual | fitbit | apple_health | garmin | myfitnesspal",
    )

    # ── Timestamps ────────────────────────────────────────────────────────────
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(),
        onupdate=func.now(), nullable=False
    )

    # ── Relationship ──────────────────────────────────────────────────────────
    user: Mapped["User"] = relationship("User", back_populates="health_entries")

    # ── Computed properties ───────────────────────────────────────────────────

    @property
    def sleep_minutes(self) -> Optional[int]:
        """Convenience: sleep duration expressed as whole minutes."""
        if self.sleep_hours is None:
            return None
        return int(float(self.sleep_hours) * 60)

    @property
    def water_intake_glasses(self) -> Optional[float]:
        """Convenience: water intake expressed as 250 ml glasses."""
        if self.water_intake_ml is None:
            return None
        return round(self.water_intake_ml / 250, 1)

    @property
    def stress_label(self) -> Optional[str]:
        """Human-readable stress level label."""
        if self.stress_level is None:
            return None
        thresholds = {
            (1, 2): "Low",
            (3, 4): "Mild",
            (5, 6): "Moderate",
            (7, 8): "High",
            (9, 10): "Extreme",
        }
        for (lo, hi), label in thresholds.items():
            if lo <= self.stress_level <= hi:
                return label
        return "Unknown"

    @property
    def heart_rate_zone(self) -> Optional[str]:
        """Resting HR zone classification."""
        if self.heart_rate_bpm is None:
            return None
        bpm = self.heart_rate_bpm
        if bpm < 60:
            return "Athlete (< 60 bpm)"
        if bpm <= 70:
            return "Excellent (60–70 bpm)"
        if bpm <= 80:
            return "Good (71–80 bpm)"
        if bpm <= 90:
            return "Above average (81–90 bpm)"
        if bpm <= 100:
            return "High normal (91–100 bpm)"
        return "Elevated (> 100 bpm — consult a doctor)"

    def __repr__(self) -> str:
        return (
            f"<HealthEntry id={self.id} "
            f"user_id={self.user_id} "
            f"date={self.entry_date}>"
        )
