"""
schemas/predict.py
==================
Pydantic schemas for the /api/v1/predict endpoint.

Input  : HealthMetricsInput  — 6 raw health metrics
Output : HealthScoreResponse  — predicted score, grade, per-metric breakdown
         BatchHealthScoreResponse — list of predictions for batch endpoint
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import Field, field_validator
from app.schemas.common import BaseSchema


# ── Request schemas ───────────────────────────────────────────────────────────

class HealthMetricsInput(BaseSchema):
    """
    Single-record health metrics payload.

    All fields are optional — missing values are handled internally by the
    ML pipeline (imputer) or treated as neutral in the rule-based fallback.
    """
    sleep_hours: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=24.0,
        description="Hours of sleep per night (0–24)",
        examples=[7.5],
    )
    steps: Optional[float] = Field(
        default=None,
        ge=0,
        description="Daily step count",
        examples=[9000],
    )
    calories: Optional[float] = Field(
        default=None,
        ge=0,
        description="Daily caloric intake in kcal",
        examples=[2100],
    )
    water_intake_ml: Optional[float] = Field(
        default=None,
        ge=0,
        description="Daily water intake in millilitres",
        examples=[2500],
    )
    stress_level: Optional[float] = Field(
        default=None,
        ge=1,
        le=10,
        description="Stress level on a 1–10 scale (1 = no stress, 10 = extreme)",
        examples=[3],
    )
    heart_rate_bpm: Optional[float] = Field(
        default=None,
        ge=30,
        le=220,
        description="Resting heart rate in beats per minute",
        examples=[68],
    )

    @field_validator("sleep_hours", mode="before")
    @classmethod
    def clamp_sleep(cls, v: Any) -> Any:
        """Allow None to pass through."""
        return v


class BatchHealthMetricsInput(BaseSchema):
    """Up to 50 records for batch prediction."""
    records: List[HealthMetricsInput] = Field(
        ...,
        min_length=1,
        max_length=50,
        description="List of health metric records (1–50 items)",
    )


# ── Response schemas ──────────────────────────────────────────────────────────

class MetricFeedback(BaseSchema):
    """Feedback message for a single health metric."""
    metric:  str = Field(description="Human-readable metric name")
    status:  str = Field(description="'ok', 'low', or 'high'")
    message: str = Field(description="Actionable feedback message")


class HealthScoreResponse(BaseSchema):
    """Full health score result for one set of metrics."""
    health_score:     float = Field(
        description="Overall health score (0–100)",
        examples=[74.35],
    )
    grade:            str   = Field(
        description="Score grade string (e.g. 'B — Good')",
        examples=["B — Good"],
    )
    letter:           str   = Field(description="Grade letter: A/B/C/D/F", examples=["B"])
    label:            str   = Field(description="Grade label", examples=["Good"])
    category_scores:  Dict[str, float] = Field(
        description="Per-metric 0–100 subscores keyed by feature name",
    )
    feedback:         List[MetricFeedback] = Field(
        description="Actionable feedback for each metric",
    )
    model_used:       str = Field(
        description="'ml_pipeline' or 'rule_based_fallback'",
        examples=["ml_pipeline"],
    )
    inputs:           Dict[str, Any] = Field(
        description="Echoed input values (NaN shown as null)",
    )


class BatchHealthScoreResponse(BaseSchema):
    """Batch prediction response."""
    predictions: List[HealthScoreResponse]
    count:       int = Field(description="Number of predictions returned")
    model_used:  str = Field(description="Model used for this batch")


class ModelInfoResponse(BaseSchema):
    """Model status / metadata endpoint."""
    model_config = {"protected_namespaces": ()}
    model_loaded:    bool
    model_path:      str
    features:        List[str]
    feature_count:   int
    grade_thresholds: Dict[str, int]
