"""
models/health.py
================
Pure-Python dataclasses (no external dependencies) for the
recommendation engine's input and output contracts.

These are mirrored by Pydantic schemas in schemas/ for the FastAPI layer.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional


# ─────────────────────────────────────────────────────────────────────────────
#  Enums
# ─────────────────────────────────────────────────────────────────────────────

class Category(str, Enum):
    SLEEP      = "sleep"
    ACTIVITY   = "activity"
    NUTRITION  = "nutrition"
    HYDRATION  = "hydration"
    STRESS     = "stress"
    HEART_RATE = "heart_rate"
    GENERAL    = "general"


class Priority(str, Enum):
    CRITICAL = "critical"   # Immediate attention required
    HIGH     = "high"       # Address within today
    MEDIUM   = "medium"     # Address within the week
    LOW      = "low"        # Maintenance / optimisation


class HealthScoreLabel(str, Enum):
    EXCELLENT = "Excellent"
    GOOD      = "Good"
    FAIR      = "Fair"
    POOR      = "Poor"
    CRITICAL  = "Critical"


# ─────────────────────────────────────────────────────────────────────────────
#  Input
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class HealthMetrics:
    """
    Raw user health metrics for one day.
    All fields optional — engine handles partial data gracefully.
    """
    sleep_hours:     Optional[float] = None   # hours (0–24)
    steps:           Optional[int]   = None   # steps/day (0–100000)
    calories:        Optional[int]   = None   # kcal consumed (0–10000)
    water_intake_ml: Optional[int]   = None   # ml consumed (0–10000)
    stress_level:    Optional[int]   = None   # subjective 1–10
    heart_rate_bpm:  Optional[int]   = None   # resting BPM (30–250)
    health_score:    Optional[float] = None   # predicted score 0–100


# ─────────────────────────────────────────────────────────────────────────────
#  Output — single recommendation
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class ActionStep:
    """One concrete, actionable step within a recommendation."""
    order:       int
    description: str
    duration:    Optional[str] = None   # e.g. "5 minutes", "30 minutes"
    frequency:   Optional[str] = None   # e.g. "Daily", "3× per week"


@dataclass
class Recommendation:
    """
    A single personalised recommendation card.

    Fields:
      id           — stable unique key (used for deduplication)
      category     — which health domain this addresses
      priority     — urgency level (critical/high/medium/low)
      title        — short headline shown to the user
      summary      — 1-2 sentence explanation of WHY this matters
      detail       — deeper context and explanation
      actions      — 2-5 concrete action steps
      metric_value — the raw metric value that triggered this rule
      target_value — what to aim for (shown in UI)
      icon         — emoji used in UI
      score_impact — estimated health score improvement if followed
      tags         — searchable tags for filtering
    """
    id:           str
    category:     Category
    priority:     Priority
    title:        str
    summary:      str
    detail:       str
    actions:      List[ActionStep]
    metric_value: Optional[float] = None
    target_value: Optional[str]   = None
    icon:         str             = "💡"
    score_impact: float           = 0.0
    tags:         List[str]       = field(default_factory=list)


# ─────────────────────────────────────────────────────────────────────────────
#  Output — full recommendation response
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class MetricStatus:
    """Per-metric status summary included in the response."""
    name:          str
    value:         Optional[float]
    unit:          str
    status:        str            # "optimal" | "good" | "fair" | "poor" | "critical"
    status_label:  str
    target:        str
    score:         float          # 0–100 sub-score for this metric


@dataclass
class RecommendationResponse:
    """
    Complete personalised recommendation package returned to the user.
    """
    health_score:         float
    health_score_label:   HealthScoreLabel
    overall_summary:      str
    metric_statuses:      List[MetricStatus]
    recommendations:      List[Recommendation]
    total_count:          int
    critical_count:       int
    high_count:           int
    score_improvement_potential: float   # max possible gain if all recs followed
    generated_at:         str
