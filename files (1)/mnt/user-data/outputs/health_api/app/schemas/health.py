"""
Pydantic schemas for request / response validation.
All field ranges are grounded in published clinical reference ranges.
"""

from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Optional
from enum import Enum


class RiskLevel(str, Enum):
    LOW      = "low"
    MODERATE = "moderate"
    HIGH     = "high"
    CRITICAL = "critical"


# ── Input ──────────────────────────────────────────────────────────────────────

class HealthMetricsInput(BaseModel):
    """
    Health metrics submitted by the client for scoring.
    All fields are validated against physiologically plausible ranges.
    """

    # Sleep
    sleep_hours: float = Field(
        ..., ge=0.0, le=24.0,
        description="Average nightly sleep duration in hours (0–24)",
        examples=[7.5],
    )
    sleep_quality: float = Field(
        ..., ge=1.0, le=10.0,
        description="Self-rated sleep quality score (1 = very poor, 10 = excellent)",
        examples=[7.0],
    )

    # Activity
    steps_daily: float = Field(
        ..., ge=0.0, le=100_000.0,
        description="Average daily step count",
        examples=[9500.0],
    )
    active_minutes: float = Field(
        ..., ge=0.0, le=1440.0,
        description="Weekly active minutes (moderate-to-vigorous exercise)",
        examples=[180.0],
    )

    # Cardiovascular
    resting_hr: float = Field(
        ..., ge=30.0, le=200.0,
        description="Resting heart rate in beats per minute",
        examples=[64.0],
    )
    hrv: float = Field(
        ..., ge=1.0, le=300.0,
        description="Heart-rate variability in milliseconds (RMSSD)",
        examples=[58.0],
    )

    # Stress & lifestyle
    stress_index: float = Field(
        ..., ge=0.0, le=100.0,
        description="Stress index (0 = no stress, 100 = maximum stress)",
        examples=[35.0],
    )
    water_intake: float = Field(
        ..., ge=0.0, le=20.0,
        description="Daily water intake in litres",
        examples=[2.2],
    )
    bmi: float = Field(
        ..., ge=10.0, le=70.0,
        description="Body-mass index (kg / m²)",
        examples=[23.5],
    )

    # Optional metadata (not used in prediction; stored for audit)
    user_id: Optional[str] = Field(
        None,
        description="Opaque user identifier for audit logging",
        examples=["usr_abc123"],
    )

    @field_validator("sleep_hours")
    @classmethod
    def warn_extreme_sleep(cls, v: float) -> float:
        # >16 hrs is physiologically unusual; still accepted but flagged downstream
        return v

    @model_validator(mode="after")
    def cross_field_check(self) -> "HealthMetricsInput":
        """Ensure active_minutes is consistent with a 7-day window."""
        if self.active_minutes > self.steps_daily * 0.1 + 400:
            raise ValueError(
                "active_minutes seems inconsistent with steps_daily. "
                "Please verify your inputs."
            )
        return self

    model_config = {
        "json_schema_extra": {
            "example": {
                "sleep_hours": 7.5,
                "sleep_quality": 7.0,
                "steps_daily": 9500.0,
                "active_minutes": 180.0,
                "resting_hr": 64.0,
                "hrv": 58.0,
                "stress_index": 35.0,
                "water_intake": 2.2,
                "bmi": 23.5,
                "user_id": "usr_abc123",
            }
        }
    }


# ── Sub-objects in response ────────────────────────────────────────────────────

class DomainScores(BaseModel):
    """Decomposed score per health domain (0–100 each)."""
    sleep:     float = Field(..., description="Sleep quality and duration sub-score")
    activity:  float = Field(..., description="Physical activity sub-score")
    cardio:    float = Field(..., description="Cardiovascular health sub-score")
    stress:    float = Field(..., description="Stress management sub-score")
    lifestyle: float = Field(..., description="Hydration and BMI sub-score")


class HealthRecommendation(BaseModel):
    domain:  str = Field(..., description="Health domain the recommendation targets")
    message: str = Field(..., description="Actionable recommendation text")
    priority: str = Field(..., description="Priority level: high | medium | low")


# ── Output ─────────────────────────────────────────────────────────────────────

class HealthScoreResponse(BaseModel):
    """Full API response for a health score prediction."""

    # Core prediction
    health_score:  float      = Field(..., description="Predicted health score (0–100)")
    risk_level:    RiskLevel  = Field(..., description="Risk classification")
    confidence:    float      = Field(..., description="Model confidence (0–1)")

    # Decomposed insight
    domain_scores:     DomainScores             = Field(..., description="Per-domain breakdown")
    recommendations:   list[HealthRecommendation] = Field(..., description="Personalised action items")

    # Meta
    model_version: str  = Field(..., description="Model artifact version string")
    user_id:       Optional[str] = Field(None, description="Echoed from request if supplied")

    model_config = {"use_enum_values": True}


class BatchHealthMetricsInput(BaseModel):
    """Up to 50 records for batch scoring."""
    records: list[HealthMetricsInput] = Field(
        ..., min_length=1, max_length=50,
        description="List of health metric records (1–50)",
    )


class BatchHealthScoreResponse(BaseModel):
    results: list[HealthScoreResponse]
    total:   int


class ModelInfoResponse(BaseModel):
    model_version:  str
    feature_names:  list[str]
    mae:            float
    r2:             float
    cv_r2_mean:     float
    train_samples:  int
    test_samples:   int
    status:         str


class ErrorResponse(BaseModel):
    detail:    str
    error_code: str
