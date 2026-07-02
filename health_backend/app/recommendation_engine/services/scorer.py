from typing import Dict, Optional
from app.recommendation_engine.models.health import HealthMetrics, HealthScoreLabel, MetricStatus
from app.recommendation_engine.rules.thresholds import (
    CALORIES, CATEGORY_WEIGHTS, HR, HYDRATION, SCORE_BANDS, SLEEP, STEPS, STRESS
)


def score_sleep(hours: float) -> float:
    """Optimal window 7–9 h → 100. Graduated penalty outside."""
    if hours < SLEEP.score_min_h:
        return 0.0
    if hours <= SLEEP.optimal_low:
        return round((hours - SLEEP.score_min_h) / (SLEEP.optimal_low - SLEEP.score_min_h) * 100, 2)
    if hours <= SLEEP.optimal_high:
        return 100.0
    return round(max(0.0, 100.0 - (hours - SLEEP.optimal_high) * 15), 2)


def score_steps(steps: int) -> float:
    """10,000 steps → 100. Linear below, capped at 100 above."""
    return round(min(100.0, steps / STEPS.active * 100), 2)


def score_calories(kcal: int) -> float:
    """Optimal 1600–2400 → 100. Graduated penalty outside window."""
    if kcal < CALORIES.optimal_low:
        return round(max(0.0, 100.0 - (CALORIES.optimal_low - kcal) / 4), 2)
    if kcal <= CALORIES.optimal_high:
        return 100.0
    return round(max(0.0, 100.0 - (kcal - CALORIES.optimal_high) / 8), 2)


def score_water(ml: int) -> float:
    """3000 ml → 100. Linear below, capped at 100 above."""
    return round(min(100.0, ml / HYDRATION.score_max_ml * 100), 2)


def score_stress(level: int) -> float:
    """1 = 100, 10 = 0. Linear inverse."""
    return round((10 - level) / 9 * 100, 2)


def score_heart_rate(bpm: int) -> float:
    """Optimal 55–70 bpm → 100. Graduated penalty outside."""
    if bpm <= HR.athlete_max:
        return 95.0
    if bpm <= HR.excellent_max:
        return 100.0
    if bpm <= HR.good_max:
        return round(100.0 - (bpm - HR.excellent_max) * 1.5, 2)
    if bpm <= HR.normal_max:
        return round(85.0 - (bpm - HR.good_max) * 2.0, 2)
    if bpm <= HR.above_normal:
        return round(65.0 - (bpm - HR.normal_max) * 1.5, 2)
    return round(max(0.0, 40.0 - (bpm - HR.above_normal) * 2.0), 2)


SCORE_FN = {
    "sleep":      lambda m: score_sleep(m.sleep_hours)         if m.sleep_hours     is not None else None,
    "activity":   lambda m: score_steps(m.steps)               if m.steps           is not None else None,
    "nutrition":  lambda m: score_calories(m.calories)         if m.calories        is not None else None,
    "hydration":  lambda m: score_water(m.water_intake_ml)     if m.water_intake_ml is not None else None,
    "stress":     lambda m: score_stress(m.stress_level)       if m.stress_level    is not None else None,
    "heart_rate": lambda m: score_heart_rate(m.heart_rate_bpm) if m.heart_rate_bpm  is not None else None,
}


def compute_sub_scores(m: HealthMetrics) -> Dict[str, Optional[float]]:
    return {cat: fn(m) for cat, fn in SCORE_FN.items()}


def compute_composite_score(sub_scores: Dict[str, Optional[float]]) -> float:
    """Weighted average of available sub-scores."""
    total_weight = 0.0
    weighted_sum = 0.0
    for cat, score in sub_scores.items():
        if score is not None:
            w = CATEGORY_WEIGHTS.get(cat, 1.0)
            weighted_sum += score * w
            total_weight += w
    if total_weight == 0:
        return 50.0
    return round(weighted_sum / total_weight, 2)


def get_health_score_label(score: float) -> HealthScoreLabel:
    if score >= SCORE_BANDS.excellent_min:
        return HealthScoreLabel.EXCELLENT
    if score >= SCORE_BANDS.fair_max:
        return HealthScoreLabel.GOOD
    if score >= SCORE_BANDS.poor_max:
        return HealthScoreLabel.FAIR
    if score >= SCORE_BANDS.critical_max:
        return HealthScoreLabel.POOR
    return HealthScoreLabel.CRITICAL


def build_metric_statuses(
    m: HealthMetrics,
    sub_scores: Dict[str, Optional[float]],
) -> list:
    """Build per-metric status cards for the response."""

    def _status_label(score: Optional[float]) -> tuple[str, str]:
        if score is None:
            return "unknown", "No data"
        if score >= 90:
            return "optimal", "Optimal ✅"
        if score >= 75:
            return "good", "Good 🟡"
        if score >= 55:
            return "fair", "Fair 🟠"
        if score >= 35:
            return "poor", "Poor 🔴"
        return "critical", "Critical 🆘"

    entries = [
        ("Sleep",           m.sleep_hours,     "hours", "7–9 hours",        "sleep"),
        ("Steps",           m.steps,           "steps", "10,000 steps/day", "activity"),
        ("Calories",        m.calories,        "kcal",  "1,600–2,400 kcal", "nutrition"),
        ("Water Intake",    m.water_intake_ml, "ml",    "2,000–3,000 ml",   "hydration"),
        ("Stress Level",    m.stress_level,    "/10",   "1–3 (low)",         "stress"),
        ("Heart Rate",      m.heart_rate_bpm,  "bpm",   "55–75 bpm",         "heart_rate"),
    ]

    statuses = []

    for name, value, unit, target, cat in entries:
        score = sub_scores.get(cat)

        # Use the same thresholds as the recommendation engine for stress
        if cat == "stress" and m.stress_level is not None:
            if m.stress_level >= STRESS.extreme_min:          # 10
                status_key = "critical"
                status_label = "Critical 🆘"
            elif m.stress_level > STRESS.high_max:            # 8-9
                status_key = "high"
                status_label = "High 🔴"
            elif m.stress_level > STRESS.moderate_max:        # 6-7
                status_key = "fair"
                status_label = "Moderate 🟠"
            elif m.stress_level > STRESS.low_max:             # 4-5
                status_key = "good"
                status_label = "Mild 🟡"
            else:                                             # 1-3
                status_key = "optimal"
                status_label = "Low ✅"
        else:
            status_key, status_label = _status_label(score)

        statuses.append(
            MetricStatus(
                name=name,
                value=float(value) if value is not None else None,
                unit=unit,
                status=status_key,
                status_label=status_label,
                target=target,
                score=score if score is not None else 0.0,
            )
        )

    return statuses


def build_overall_summary(score: float, label: HealthScoreLabel, m: HealthMetrics) -> str:
    """Generate a one-paragraph personalised health summary."""
    parts = []
    parts.append(f"Your overall health score is {score:.0f}/100 — {label.value}.")

    if label == HealthScoreLabel.EXCELLENT:
        parts.append(
            "You're performing exceptionally well across all tracked metrics. "
            "Focus on maintaining consistency and monitoring for early warning signs."
        )
    elif label == HealthScoreLabel.GOOD:
        parts.append(
            "You're in good health with a few areas to fine-tune. "
            "Small, consistent improvements will push you into the excellent range."
        )
    elif label == HealthScoreLabel.FAIR:
        parts.append(
            "Several metrics need attention. Prioritise the high-priority "
            "recommendations below — they'll have the biggest impact on your score."
        )
    elif label == HealthScoreLabel.POOR:
        parts.append(
            "Multiple health indicators are below healthy thresholds. "
            "Start with the critical recommendations and address one area at a time."
        )
    else:
        parts.append(
            "Your health metrics are in a critical range across multiple areas. "
            "Please act on the urgent recommendations below and consider consulting "
            "a healthcare professional."
        )

    sub_scores = compute_sub_scores(m)
    available = {k: v for k, v in sub_scores.items() if v is not None}
    if available:
        worst = min(available, key=available.get)
        worst_score = available[worst]
        if worst_score < 60:
            label_map = {
                "sleep": "sleep quality",
                "activity": "daily activity",
                "nutrition": "calorie intake",
                "hydration": "hydration",
                "stress": "stress management",
                "heart_rate": "resting heart rate",
            }
            parts.append(
                f"Your biggest opportunity today is improving your "
                f"{label_map.get(worst, worst)} (sub-score: {worst_score:.0f}/100)."
            )

    return " ".join(parts)
