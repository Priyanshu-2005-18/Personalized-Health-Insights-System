"""
schemas/health_entry.py
=======================
Pydantic v2 schemas for health tracking endpoints.

Validation layers:
  1. Type coercion       — Pydantic enforces int/float/str types
  2. Range constraints   — Field(ge=, le=) applied to every metric
  3. Custom validators   — cross-field logic (e.g. can't submit with zero fields)
  4. DB CHECK constraints — last line of defence at the PostgreSQL level

Metric reference:
  ┌─────────────────────┬────────────┬────────────┬──────────────────────────┐
  │ Metric              │ Min        │ Max        │ Unit                     │
  ├─────────────────────┼────────────┼────────────┼──────────────────────────┤
  │ sleep_hours         │ 0.0        │ 24.0       │ hours (supports 0.5 h)   │
  │ steps               │ 0          │ 100 000    │ steps/day                │
  │ calories_consumed   │ 0          │ 10 000     │ kcal                     │
  │ water_intake_ml     │ 0          │ 10 000     │ millilitres              │
  │ stress_level        │ 1          │ 10         │ subjective scale         │
  │ heart_rate_bpm      │ 30         │ 250        │ beats per minute         │
  └─────────────────────┴────────────┴────────────┴──────────────────────────┘
"""

from datetime import date, datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class BaseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


# ─────────────────────────────────────────────────────────────────────────────
#  Shared metric mixin  (reused in both Create and Update)
# ─────────────────────────────────────────────────────────────────────────────

class HealthMetricsMixin(BaseModel):
    """All six health metrics, all optional so partial updates are supported."""

    sleep_hours: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=24.0,
        description="Total sleep duration in hours. Supports decimal (e.g. 7.5 = 7h 30m)",
        examples=[7.5],
    )
    steps: Optional[int] = Field(
        default=None,
        ge=0,
        le=100_000,
        description="Total steps walked or run during the day",
        examples=[8432],
    )
    calories_consumed: Optional[int] = Field(
        default=None,
        ge=0,
        le=10_000,
        description="Total dietary calories consumed in kcal",
        examples=[2100],
    )
    water_intake_ml: Optional[int] = Field(
        default=None,
        ge=0,
        le=10_000,
        description="Total water consumed in millilitres (250 ml ≈ 1 glass)",
        examples=[2500],
    )
    stress_level: Optional[int] = Field(
        default=None,
        ge=1,
        le=10,
        description="Subjective stress level: 1 = no stress, 10 = extreme stress",
        examples=[4],
    )
    heart_rate_bpm: Optional[int] = Field(
        default=None,
        ge=30,
        le=250,
        description="Resting heart rate in beats per minute",
        examples=[68],
    )
    notes: Optional[str] = Field(
        default=None,
        max_length=2000,
        description="Free-form journal notes for the day",
        examples=["Felt tired after gym. Drank extra water."],
    )
    source: str = Field(
        default="manual",
        max_length=30,
        description="Data source: manual | fitbit | apple_health | garmin | myfitnesspal",
        examples=["manual"],
    )


# ─────────────────────────────────────────────────────────────────────────────
#  Create
# ─────────────────────────────────────────────────────────────────────────────

class HealthEntryCreate(HealthMetricsMixin, BaseSchema):
    """
    Body for POST /health.
    entry_date is required. At least one metric must be provided.
    """

    entry_date: date = Field(
        ...,
        description="Calendar date this entry covers (YYYY-MM-DD)",
        examples=["2024-06-15"],
    )

    @model_validator(mode="after")
    def at_least_one_metric(self) -> "HealthEntryCreate":
        """Reject submissions with no metric data at all."""
        metrics = [
            self.sleep_hours, self.steps, self.calories_consumed,
            self.water_intake_ml, self.stress_level, self.heart_rate_bpm,
        ]
        if all(m is None for m in metrics):
            raise ValueError(
                "At least one metric (sleep_hours, steps, calories_consumed, "
                "water_intake_ml, stress_level, heart_rate_bpm) must be provided"
            )
        return self


# ─────────────────────────────────────────────────────────────────────────────
#  Update  (PATCH — partial)
# ─────────────────────────────────────────────────────────────────────────────

class HealthEntryUpdate(HealthMetricsMixin, BaseSchema):
    """
    Body for PATCH /health/{id}.
    All fields optional — only supplied fields are updated.
    """

    @model_validator(mode="after")
    def at_least_one_field(self) -> "HealthEntryUpdate":
        fields = [
            self.sleep_hours, self.steps, self.calories_consumed,
            self.water_intake_ml, self.stress_level, self.heart_rate_bpm,
            self.notes,
        ]
        if all(f is None for f in fields):
            raise ValueError("At least one field must be provided for update")
        return self


# ─────────────────────────────────────────────────────────────────────────────
#  Read  (response)
# ─────────────────────────────────────────────────────────────────────────────

class HealthEntryRead(BaseSchema):
    """Full health entry returned by GET/POST/PATCH endpoints."""

    id: UUID
    user_id: UUID
    entry_date: date

    # Core metrics
    sleep_hours: Optional[float]
    steps: Optional[int]
    calories_consumed: Optional[int]
    water_intake_ml: Optional[int]
    stress_level: Optional[int]
    heart_rate_bpm: Optional[int]

    # Computed convenience fields
    sleep_minutes: Optional[int] = Field(
        default=None,
        description="sleep_hours converted to whole minutes",
    )
    water_intake_glasses: Optional[float] = Field(
        default=None,
        description="water_intake_ml converted to 250 ml glasses",
    )
    stress_label: Optional[str] = Field(
        default=None,
        description="Human-readable stress label (Low / Mild / Moderate / High / Extreme)",
    )
    heart_rate_zone: Optional[str] = Field(
        default=None,
        description="Resting HR zone classification",
    )

    notes: Optional[str]
    source: str
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_orm_with_computed(cls, entry) -> "HealthEntryRead":
        """Build response including computed properties from the ORM model."""
        return cls(
            id=entry.id,
            user_id=entry.user_id,
            entry_date=entry.entry_date,
            sleep_hours=float(entry.sleep_hours) if entry.sleep_hours is not None else None,
            steps=entry.steps,
            calories_consumed=entry.calories_consumed,
            water_intake_ml=entry.water_intake_ml,
            stress_level=entry.stress_level,
            heart_rate_bpm=entry.heart_rate_bpm,
            sleep_minutes=entry.sleep_minutes,
            water_intake_glasses=entry.water_intake_glasses,
            stress_label=entry.stress_label,
            heart_rate_zone=entry.heart_rate_zone,
            notes=entry.notes,
            source=entry.source,
            created_at=entry.created_at,
            updated_at=entry.updated_at,
        )


# ─────────────────────────────────────────────────────────────────────────────
#  Summary / analytics response
# ─────────────────────────────────────────────────────────────────────────────

class HealthSummary(BaseSchema):
    """
    Aggregated statistics over a date range.
    Returned by GET /health/summary.
    """

    period_start: date
    period_end: date
    total_entries: int

    # Sleep
    avg_sleep_hours: Optional[float]
    min_sleep_hours: Optional[float]
    max_sleep_hours: Optional[float]

    # Steps
    avg_steps: Optional[float]
    total_steps: Optional[int]
    max_steps: Optional[int]

    # Calories
    avg_calories_consumed: Optional[float]
    total_calories_consumed: Optional[int]

    # Water
    avg_water_intake_ml: Optional[float]
    total_water_intake_ml: Optional[int]

    # Stress
    avg_stress_level: Optional[float]
    min_stress_level: Optional[int]
    max_stress_level: Optional[int]

    # Heart rate
    avg_heart_rate_bpm: Optional[float]
    min_heart_rate_bpm: Optional[int]
    max_heart_rate_bpm: Optional[int]


# ─────────────────────────────────────────────────────────────────────────────
#  Paginated list response
# ─────────────────────────────────────────────────────────────────────────────

class PaginatedHealthEntries(BaseSchema):
    items: list[HealthEntryRead]
    total: int
    page: int
    size: int
    pages: int


# ─────────────────────────────────────────────────────────────────────────────
#  Auth schemas (minimal — for built-in signup/login)
# ─────────────────────────────────────────────────────────────────────────────

class MessageResponse(BaseSchema):
    message: str


class UserSignup(BaseSchema):
    email: str = Field(..., examples=["user@example.com"])
    username: str = Field(..., min_length=3, max_length=50, examples=["john_doe"])
    password: str = Field(..., min_length=8, max_length=128)
    full_name: Optional[str] = Field(default=None, examples=["John Doe"])


class UserLogin(BaseSchema):
    email: str
    password: str


class TokenResponse(BaseSchema):
    access_token: str
    token_type: str = "bearer"
