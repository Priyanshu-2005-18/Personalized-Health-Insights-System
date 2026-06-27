"""
routers/recommendations.py
===========================
FastAPI routes for the recommendation engine.

Endpoints:
  POST /recommendations          — full personalised recommendation report
  POST /recommendations/quick    — top 3 critical/high recommendations only
  GET  /recommendations/categories — list all supported recommendation categories
  GET  /recommendations/health   — engine health check
"""

from fastapi import APIRouter, HTTPException, status
from app.models.health import HealthMetrics
from app.schemas.health import (
    ErrorResponse,
    HealthInsightsResponse,
    HealthMetricsRequest,
    serialise_response,
)
from app.services.recommendation_service import generate_recommendations

router = APIRouter(prefix="/recommendations", tags=["Recommendations"])


# ─────────────────────────────────────────────────────────────────────────────
#  POST /recommendations — full report
# ─────────────────────────────────────────────────────────────────────────────

@router.post(
    "",
    response_model=HealthInsightsResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate personalised health recommendations",
    description="""
Submit today's health metrics and receive a fully personalised
recommendation report.

**What you get back:**
- Overall health score (0–100) with label (Excellent / Good / Fair / Poor / Critical)
- Per-metric status card (Optimal / Good / Fair / Poor / Critical) for all 6 metrics
- Up to 8 personalised recommendations ranked by urgency
- Each recommendation includes: title, summary, detailed explanation, and 2–5 action steps
- Score improvement potential if all recommendations are followed

**Health score:**
If `health_score` is supplied (e.g. from a trained ML model), it is used directly.
If omitted, the engine computes a composite score from the supplied metrics.

**Partial input is fine:**
Not all metrics are required. Supply whatever you have — rules only fire
for metrics that are present.
""",
    responses={
        200: {"description": "Recommendations generated successfully"},
        400: {"model": ErrorResponse, "description": "Invalid metric values"},
        422: {"model": ErrorResponse, "description": "Validation error"},
    },
)
async def get_recommendations(
    payload: HealthMetricsRequest,
) -> HealthInsightsResponse:
    try:
        domain_input = HealthMetrics(
            sleep_hours     = payload.sleep_hours,
            steps           = payload.steps,
            calories        = payload.calories,
            water_intake_ml = payload.water_intake_ml,
            stress_level    = payload.stress_level,
            heart_rate_bpm  = payload.heart_rate_bpm,
            health_score    = payload.health_score,
        )
        result = generate_recommendations(domain_input)
        return serialise_response(result)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Recommendation engine error: {str(e)}",
        )


# ─────────────────────────────────────────────────────────────────────────────
#  POST /recommendations/quick — top 3 only
# ─────────────────────────────────────────────────────────────────────────────

@router.post(
    "/quick",
    response_model=HealthInsightsResponse,
    summary="Quick recommendations — top 3 only",
    description="""
Same as the full endpoint but returns only the top 3 most urgent
recommendations (Critical and High priority first).
Useful for mobile notifications or dashboard widgets.
""",
)
async def get_quick_recommendations(
    payload: HealthMetricsRequest,
) -> HealthInsightsResponse:
    try:
        domain_input = HealthMetrics(
            sleep_hours     = payload.sleep_hours,
            steps           = payload.steps,
            calories        = payload.calories,
            water_intake_ml = payload.water_intake_ml,
            stress_level    = payload.stress_level,
            heart_rate_bpm  = payload.heart_rate_bpm,
            health_score    = payload.health_score,
        )
        result = generate_recommendations(domain_input)

        # Cap to top 3
        result.recommendations = result.recommendations[:3]
        result.total_count     = len(result.recommendations)

        return serialise_response(result)

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# ─────────────────────────────────────────────────────────────────────────────
#  GET /recommendations/categories
# ─────────────────────────────────────────────────────────────────────────────

@router.get(
    "/categories",
    summary="List all recommendation categories",
    description="Returns metadata for every supported recommendation category.",
)
async def get_categories() -> dict:
    return {
        "categories": [
            {
                "id":          "sleep",
                "label":       "Sleep",
                "icon":        "😴",
                "description": "Sleep duration, quality, and circadian rhythm",
                "metric":      "sleep_hours",
                "optimal":     "7–9 hours",
                "rules":       5,
            },
            {
                "id":          "activity",
                "label":       "Physical Activity",
                "icon":        "🏃",
                "description": "Daily step count and exercise recommendations",
                "metric":      "steps",
                "optimal":     "10,000 steps/day",
                "rules":       5,
            },
            {
                "id":          "nutrition",
                "label":       "Nutrition",
                "icon":        "🍽️",
                "description": "Calorie intake and dietary quality",
                "metric":      "calories",
                "optimal":     "1,600–2,400 kcal/day",
                "rules":       5,
            },
            {
                "id":          "hydration",
                "label":       "Hydration",
                "icon":        "💧",
                "description": "Daily water intake and hydration status",
                "metric":      "water_intake_ml",
                "optimal":     "2,000–3,000 ml/day",
                "rules":       4,
            },
            {
                "id":          "stress",
                "label":       "Stress Management",
                "icon":        "🧘",
                "description": "Stress level and mental wellbeing techniques",
                "metric":      "stress_level",
                "optimal":     "1–3 (low)",
                "rules":       5,
            },
            {
                "id":          "heart_rate",
                "label":       "Heart Rate",
                "icon":        "❤️",
                "description": "Resting heart rate and cardiovascular fitness",
                "metric":      "heart_rate_bpm",
                "optimal":     "55–75 bpm",
                "rules":       5,
            },
        ]
    }


# ─────────────────────────────────────────────────────────────────────────────
#  GET /recommendations/health
# ─────────────────────────────────────────────────────────────────────────────

@router.get(
    "/health",
    summary="Engine health check",
    tags=["System"],
)
async def engine_health() -> dict:
    from app.rules import ALL_RULE_SETS
    total_rules = sum(len(rules) for rules in ALL_RULE_SETS.values())
    return {
        "status":        "ok",
        "engine":        "rule-based v1",
        "categories":    len(ALL_RULE_SETS),
        "total_rules":   total_rules,
        "version":       "1.0.0",
    }
