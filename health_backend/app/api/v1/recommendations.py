"""
api/v1/recommendations.py
=========================
Recommendations endpoint that wraps the ML predictor and returns a
HealthInsightsResponse matching the frontend's expected schema exactly.

Routes
------
POST /api/v1/recommendations        — generate insights (authenticated)
POST /api/v1/recommendations/quick  — quick insights (authenticated)
"""
from __future__ import annotations

import math
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

from fastapi import APIRouter, status

from app.core.deps import CurrentUser
from app.ml.predictor import HealthScorePredictor, FEATURES, _OPTIMAL_RANGES
from app.schemas.recommendations import (
    HealthMetricsRequest,
    HealthInsightsResponse,
    MetricStatus,
    Recommendation,
    ActionStep,
)

router = APIRouter()


def _sanitise(v: Any) -> Any:
    if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
        return None
    return v


def _score_to_status(score: float) -> str:
    if score >= 90:
        return "optimal"
    if score >= 70:
        return "good"
    if score >= 50:
        return "fair"
    if score >= 30:
        return "poor"
    return "critical"


def _build_metric_statuses(
    category_scores: Dict[str, float],
    inputs: Dict[str, Any],
) -> List[MetricStatus]:
    units = {
        "sleep_hours": "hours",
        "steps": "steps",
        "calories": "kcal",
        "water_intake_ml": "ml",
        "stress_level": "/10",
        "heart_rate_bpm": "bpm",
    }
    targets = {
        "sleep_hours": "7–9 hours",
        "steps": "8,000–12,000 steps",
        "calories": "1,800–2,200 kcal",
        "water_intake_ml": "2,000–3,500 ml",
        "stress_level": "1–3 (low)",
        "heart_rate_bpm": "60–80 bpm",
    }
    labels = {
        "sleep_hours": "Sleep Duration",
        "steps": "Daily Steps",
        "calories": "Caloric Intake",
        "water_intake_ml": "Water Intake",
        "stress_level": "Stress Level",
        "heart_rate_bpm": "Heart Rate",
    }
    statuses = []
    for feat in FEATURES:
        score = category_scores.get(feat, 50.0)
        val = inputs.get(feat)
        status_str = _score_to_status(score)
        lo, hi = _OPTIMAL_RANGES.get(feat, (0, 100))
        statuses.append(MetricStatus(
            name=labels.get(feat, feat),
            value=_sanitise(val),
            unit=units.get(feat, ""),
            status=status_str,
            status_label=status_str.capitalize(),
            target=targets.get(feat, ""),
            score=round(score, 1),
        ))
    return statuses


def _build_recommendations(feedback: List[Dict], category_scores: Dict[str, float]) -> List[Recommendation]:
    """Convert predictor feedback into frontend Recommendation objects."""
    category_map = {
        "Sleep Duration": "sleep",
        "Daily Steps": "activity",
        "Caloric Intake": "nutrition",
        "Water Intake": "hydration",
        "Stress Level": "stress",
        "Heart Rate": "heart_rate",
    }
    icon_map = {
        "sleep": "😴",
        "activity": "🏃",
        "nutrition": "🍽️",
        "hydration": "💧",
        "stress": "🧘",
        "heart_rate": "❤️",
        "general": "💡",
    }
    feat_map = {
        "Sleep Duration": "sleep_hours",
        "Daily Steps": "steps",
        "Caloric Intake": "calories",
        "Water Intake": "water_intake_ml",
        "Stress Level": "stress_level",
        "Heart Rate": "heart_rate_bpm",
    }

    # Priority based on status
    def get_priority(fb: dict) -> str:
        stat = fb.get("status", "ok")
        feat = feat_map.get(fb.get("metric", ""), "")
        score = category_scores.get(feat, 50.0)
        if score < 30:
            return "high"
        if score < 50:
            return "medium"
        if stat == "ok":
            return "low"
        return "medium"

    # Action tips per metric
    action_tips = {
        "sleep_hours": {
            "low": ["Set a consistent bedtime 30 minutes earlier", "Avoid screens 1 hour before bed", "Keep bedroom temperature between 18–20°C"],
            "high": ["Investigate cause of excessive sleep", "Limit naps to 20–30 minutes", "Consult a doctor if fatigue persists"],
            "ok": ["Maintain your sleep schedule", "Keep a consistent wake-up time", "Avoid caffeine after 2 PM"],
        },
        "steps": {
            "low": ["Take a 15-minute walk after each meal", "Use stairs instead of lifts", "Park farther away from destinations"],
            "high": ["Keep up the excellent activity!", "Ensure adequate rest and recovery", "Stay hydrated during activity"],
            "ok": ["Maintain your activity level", "Try adding variety like cycling or swimming", "Set weekly step goals"],
        },
        "calories": {
            "low": ["Ensure balanced meals with adequate portions", "Add healthy calorie-dense foods like nuts", "Track your meals for one week"],
            "high": ["Practice mindful eating", "Reduce portion sizes gradually", "Replace processed snacks with vegetables"],
            "ok": ["Continue balanced eating habits", "Focus on food quality", "Stay hydrated between meals"],
        },
        "water_intake_ml": {
            "low": ["Keep a water bottle on your desk at all times", "Drink a full glass immediately after waking", "Set hourly hydration reminders"],
            "high": ["Great hydration! Keep it up.", "Ensure you're replacing electrolytes if exercising", "Stay consistent throughout the day"],
            "ok": ["Maintain your hydration habits", "Drink water before each meal", "Monitor urine color as a hydration indicator"],
        },
        "stress_level": {
            "low": ["Continue your stress management practices", "Share your techniques with others", "Regular mindfulness maintains resilience"],
            "high": ["Practice 5 minutes of box breathing daily", "Identify and reduce key stressors", "Consider speaking with a mental health professional"],
            "ok": ["Continue your coping strategies", "Schedule regular relaxation activities", "Practice mindfulness meditation"],
        },
        "heart_rate_bpm": {
            "low": ["This may be normal for athletes — consult your doctor", "Monitor for dizziness or fatigue", "Ensure adequate nutrition and hydration"],
            "high": ["Reduce caffeine and alcohol intake", "Practice stress reduction techniques", "Consult a healthcare provider if persistent"],
            "ok": ["Maintain your cardiovascular health", "Regular aerobic exercise supports heart health", "Monitor trends over time"],
        },
    }

    recs = []
    seen_statuses = set()
    for fb in feedback:
        metric_name = fb.get("metric", "")
        stat = fb.get("status", "ok")
        message = fb.get("message", "")
        category = category_map.get(metric_name, "general")
        feat = feat_map.get(metric_name, "")
        score = category_scores.get(feat, 50.0)
        priority = get_priority(fb)

        # Only show non-ok statuses as recommendations, plus a general one
        if stat == "ok" and score >= 80:
            continue
        if (metric_name, stat) in seen_statuses:
            continue
        seen_statuses.add((metric_name, stat))

        tips = action_tips.get(feat, {}).get(stat, ["Consult a healthcare professional for guidance"])
        action_steps = [
            ActionStep(order=i + 1, description=tip, duration=None, frequency=None)
            for i, tip in enumerate(tips)
        ]

        score_impact = max(0, round(100 - score))

        recs.append(Recommendation(
            id=str(uuid4()),
            category=category,
            priority=priority,
            title=f"Improve your {metric_name.lower()}",
            summary=message,
            detail=message,
            actions=action_steps,
            metric_value=None,
            target_value=None,
            icon=icon_map.get(category, "💡"),
            score_impact=score_impact,
            tags=[category, stat],
        ))

    return sorted(recs, key=lambda r: ["high", "medium", "low"].index(r.priority) if r.priority in ["high", "medium", "low"] else 99)


def _build_response(result: dict) -> HealthInsightsResponse:
    score = result["health_score"]
    category_scores = result.get("category_scores", {})
    feedback = result.get("feedback", [])
    inputs = result.get("inputs", {})

    metric_statuses = _build_metric_statuses(category_scores, inputs)
    recommendations = _build_recommendations(feedback, category_scores)

    # Score label
    if score >= 85:
        score_label = "Excellent"
    elif score >= 70:
        score_label = "Good"
    elif score >= 55:
        score_label = "Fair"
    elif score >= 40:
        score_label = "Poor"
    else:
        score_label = "Critical"

    # Overall summary
    overall_summary = (
        f"Your health score is {score:.0f}/100 ({score_label}). "
        f"You have {len(recommendations)} recommendation{'s' if len(recommendations) != 1 else ''} to review."
    )

    critical_count = sum(1 for r in recommendations if r.priority == "high")
    high_count = sum(1 for r in recommendations if r.priority == "medium")
    score_improvement = min(30, sum(
        max(0, (100 - category_scores.get(f, 100)) * 0.1)
        for f in FEATURES
    ))

    return HealthInsightsResponse(
        health_score=round(score, 1),
        health_score_label=score_label,
        overall_summary=overall_summary,
        metric_statuses=metric_statuses,
        recommendations=recommendations,
        total_count=len(recommendations),
        critical_count=critical_count,
        high_count=high_count,
        score_improvement_potential=round(score_improvement, 1),
        generated_at=datetime.now(timezone.utc).isoformat(),
    )


@router.post(
    "",
    response_model=HealthInsightsResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate health insights from metrics (authenticated)",
)
async def get_recommendations(
    payload: HealthMetricsRequest,
    current_user: CurrentUser,
) -> HealthInsightsResponse:
    """
    Submit health metrics and receive a complete HealthInsightsResponse
    with score, metric statuses, and recommendations.
    """
    predictor = HealthScorePredictor.get_instance()
    kwargs = {
        k: (v if v is not None else math.nan)
        for k, v in payload.model_dump().items()
    }
    result = predictor.predict_single(**kwargs)
    return _build_response(result)


@router.post(
    "/quick",
    response_model=HealthInsightsResponse,
    status_code=status.HTTP_200_OK,
    summary="Quick health insights (authenticated)",
)
async def get_quick_recommendations(
    payload: HealthMetricsRequest,
    current_user: CurrentUser,
) -> HealthInsightsResponse:
    """
    Same as POST /recommendations — quick convenience alias for dashboard use.
    """
    predictor = HealthScorePredictor.get_instance()
    kwargs = {
        k: (v if v is not None else math.nan)
        for k, v in payload.model_dump().items()
    }
    result = predictor.predict_single(**kwargs)
    return _build_response(result)
