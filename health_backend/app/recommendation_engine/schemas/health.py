from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field, model_validator


class HealthMetricsRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "sleep_hours": 5.5,
                "steps": 3200,
                "calories": 2800,
                "water_intake_ml": 1200,
                "stress_level": 8,
                "heart_rate_bpm": 88,
                "health_score": 42.0,
            }
        }
    )

    sleep_hours: Optional[float] = Field(
        default=None, ge=0.0, le=24.0,
        description="Total sleep last night in hours (0–24). Supports decimals (7.5 = 7h 30m).",
    )
    steps: Optional[int] = Field(
        default=None, ge=0, le=100_000,
        description="Total steps taken today (0–100,000).",
    )
    calories: Optional[int] = Field(
        default=None, ge=0, le=10_000,
        description="Total dietary calories consumed today in kcal (0–10,000).",
    )
    water_intake_ml: Optional[int] = Field(
        default=None, ge=0, le=10_000,
        description="Total water consumed today in millilitres (0–10,000).",
    )
    stress_level: Optional[int] = Field(
        default=None, ge=1, le=10,
        description="Subjective stress level: 1 = no stress, 10 = extreme stress.",
    )
    heart_rate_bpm: Optional[int] = Field(
        default=None, ge=30, le=250,
        description="Resting heart rate in beats per minute (30–250).",
    )
    health_score: Optional[float] = Field(
        default=None, ge=0.0, le=100.0,
        description=(
            "Pre-computed health score from the ML model (0–100). "
            "If omitted, the engine computes it from the supplied metrics."
        ),
    )

    @model_validator(mode="after")
    def at_least_one_metric(self) -> "HealthMetricsRequest":
        metrics = [
            self.sleep_hours, self.steps, self.calories,
            self.water_intake_ml, self.stress_level, self.heart_rate_bpm,
        ]
        if all(v is None for v in metrics) and self.health_score is None:
            raise ValueError(
                "At least one metric must be provided. "
                "Supply any of: sleep_hours, steps, calories, water_intake_ml, "
                "stress_level, heart_rate_bpm, or health_score."
            )
        return self


class ActionStepResponse(BaseModel):
    order:       int
    description: str
    duration:    Optional[str] = None
    frequency:   Optional[str] = None


class RecommendationResponse(BaseModel):
    id:           str
    category:     str
    priority:     str
    title:        str
    summary:      str
    detail:       str
    actions:      List[ActionStepResponse]
    metric_value: Optional[float] = None
    target_value: Optional[str]   = None
    icon:         str
    score_impact: float
    tags:         List[str]


class MetricStatusResponse(BaseModel):
    name:         str
    value:        Optional[float]
    unit:         str
    status:       str
    status_label: str
    target:       str
    score:        float


class HealthInsightsResponse(BaseModel):
    health_score:                float
    health_score_label:          str
    overall_summary:             str
    metric_statuses:             List[MetricStatusResponse]
    recommendations:             List[RecommendationResponse]
    total_count:                 int
    critical_count:              int
    high_count:                  int
    score_improvement_potential: float
    generated_at:                str


def serialise_response(domain_resp) -> HealthInsightsResponse:
    """Convert RecommendationResponse dataclass → Pydantic schema."""
    return HealthInsightsResponse(
        health_score                = domain_resp.health_score,
        health_score_label          = domain_resp.health_score_label.value,
        overall_summary             = domain_resp.overall_summary,
        metric_statuses=[
            MetricStatusResponse(
                name=ms.name, value=ms.value, unit=ms.unit,
                status=ms.status, status_label=ms.status_label,
                target=ms.target, score=ms.score,
            )
            for ms in domain_resp.metric_statuses
        ],
        recommendations=[
            RecommendationResponse(
                id=r.id, category=r.category.value,
                priority=r.priority.value, title=r.title,
                summary=r.summary, detail=r.detail,
                actions=[
                    ActionStepResponse(
                        order=a.order, description=a.description,
                        duration=a.duration, frequency=a.frequency,
                    )
                    for a in r.actions
                ],
                metric_value=r.metric_value, target_value=r.target_value,
                icon=r.icon, score_impact=r.score_impact, tags=r.tags,
            )
            for r in domain_resp.recommendations
        ],
        total_count                 = domain_resp.total_count,
        critical_count              = domain_resp.critical_count,
        high_count                  = domain_resp.high_count,
        score_improvement_potential = domain_resp.score_improvement_potential,
        generated_at                = domain_resp.generated_at,
    )


class ErrorResponse(BaseModel):
    detail:  str
    errors:  Optional[List[dict]] = None
    code:    Optional[str]        = None
