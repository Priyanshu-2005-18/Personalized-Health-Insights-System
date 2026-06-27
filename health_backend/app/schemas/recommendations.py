"""
schemas/recommendations.py
==========================
Pydantic schemas for the /api/v1/recommendations endpoint.
These exactly match the frontend's TypeScript types in src/types/index.ts.
"""
from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional
from pydantic import Field
from app.schemas.common import BaseSchema


# ── Request ──────────────────────────────────────────────────────────────────

class HealthMetricsRequest(BaseSchema):
    """Health metrics submitted by the frontend for recommendation generation."""
    sleep_hours: Optional[float] = Field(default=None, ge=0.0, le=24.0)
    steps: Optional[float] = Field(default=None, ge=0)
    calories: Optional[float] = Field(default=None, ge=0)
    water_intake_ml: Optional[float] = Field(default=None, ge=0)
    stress_level: Optional[float] = Field(default=None, ge=1, le=10)
    heart_rate_bpm: Optional[float] = Field(default=None, ge=30, le=220)
    health_score: Optional[float] = Field(default=None, ge=0, le=100)


# ── Response ─────────────────────────────────────────────────────────────────

class ActionStep(BaseSchema):
    order: int
    description: str
    duration: Optional[str] = None
    frequency: Optional[str] = None


class Recommendation(BaseSchema):
    id: str
    category: str
    priority: str  # "critical" | "high" | "medium" | "low"
    title: str
    summary: str
    detail: str
    actions: List[ActionStep]
    metric_value: Optional[float] = None
    target_value: Optional[str] = None
    icon: str
    score_impact: float
    tags: List[str]


class MetricStatus(BaseSchema):
    name: str
    value: Optional[float] = None
    unit: str
    status: str  # "optimal" | "good" | "fair" | "poor" | "critical" | "unknown"
    status_label: str
    target: str
    score: float


class HealthInsightsResponse(BaseSchema):
    health_score: float
    health_score_label: str  # "Excellent" | "Good" | "Fair" | "Poor" | "Critical"
    overall_summary: str
    metric_statuses: List[MetricStatus]
    recommendations: List[Recommendation]
    total_count: int
    critical_count: int
    high_count: int
    score_improvement_potential: float
    generated_at: str
