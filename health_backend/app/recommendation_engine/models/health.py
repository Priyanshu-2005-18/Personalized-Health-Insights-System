from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional


class Category(str, Enum):
    SLEEP      = "sleep"
    ACTIVITY   = "activity"
    NUTRITION  = "nutrition"
    HYDRATION  = "hydration"
    STRESS     = "stress"
    HEART_RATE = "heart_rate"
    GENERAL    = "general"


class Priority(str, Enum):
    CRITICAL = "critical"
    HIGH     = "high"
    MEDIUM   = "medium"
    LOW      = "low"


class HealthScoreLabel(str, Enum):
    EXCELLENT = "Excellent"
    GOOD      = "Good"
    FAIR      = "Fair"
    POOR      = "Poor"
    CRITICAL  = "Critical"


@dataclass
class HealthMetrics:
    sleep_hours:     Optional[float] = None
    steps:           Optional[int]   = None
    calories:        Optional[int]   = None
    water_intake_ml: Optional[int]   = None
    stress_level:    Optional[int]   = None
    heart_rate_bpm:  Optional[int]   = None
    health_score:    Optional[float] = None


@dataclass
class ActionStep:
    order:       int
    description: str
    duration:    Optional[str] = None
    frequency:   Optional[str] = None


@dataclass
class Recommendation:
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


@dataclass
class MetricStatus:
    name:          str
    value:         Optional[float]
    unit:          str
    status:        str
    status_label:  str
    target:        str
    score:         float


@dataclass
class RecommendationResponse:
    health_score:         float
    health_score_label:   HealthScoreLabel
    overall_summary:      str
    metric_statuses:      List[MetricStatus]
    recommendations:      List[Recommendation]
    total_count:          int
    critical_count:       int
    high_count:           int
    score_improvement_potential: float
    generated_at:         str
