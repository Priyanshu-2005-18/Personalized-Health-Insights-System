"""
rules/heart_rate_rules.py
=========================
Rule-based heart rate recommendations based on resting BPM.
"""

from typing import Optional
from app.recommendation_engine.models.health import (
    ActionStep, Category, HealthMetrics, Priority, Recommendation
)
from app.recommendation_engine.rules.thresholds import HR, STRESS


def rule_elevated_hr(m: HealthMetrics) -> Optional[Recommendation]:
    """Fires when resting HR > 100 bpm — tachycardia territory."""
    if m.heart_rate_bpm is None or m.heart_rate_bpm <= HR.elevated_min:
        return None

    # Compound: high HR + high stress amplifies cardiovascular risk
    stress_note = ""
    if m.stress_level is not None and m.stress_level >= STRESS.high_max:
        stress_note = (
            " Your elevated stress level today may be contributing — "
            "stress hormones directly increase heart rate."
        )

    return Recommendation(
        id="hr_elevated",
        category=Category.HEART_RATE,
        priority=Priority.HIGH,
        title="Elevated Resting Heart Rate — Monitor Closely",
        summary=(
            f"Resting HR of {m.heart_rate_bpm} bpm exceeds the normal upper limit "
            f"(100 bpm).{stress_note} Persistent tachycardia warrants medical review."
        ),
        detail=(
            "A resting heart rate above 100 bpm (tachycardia) can indicate "
            "dehydration, anaemia, thyroid dysfunction, cardiovascular issues, "
            "anxiety, or excessive stimulant intake. An isolated high reading "
            "may reflect temporary causes (caffeine, stress, illness). "
            "If consistently above 100 bpm, consult a GP."
        ),
        actions=[
            ActionStep(1, "Take your resting HR measurement: sit quietly for "
                          "5 minutes, then measure. Repeat for 3 days.",
                       duration="5 minutes", frequency="3 mornings in a row"),
            ActionStep(2, "Reduce caffeine intake today — it raises HR by "
                          "5–15 bpm in sensitive individuals.",
                       frequency="Today"),
            ActionStep(3, "Drink 500ml of water — dehydration is a common cause "
                          "of elevated resting HR.",
                       duration="Now", frequency="Today"),
            ActionStep(4, "Practice slow diaphragmatic breathing (6 breaths/min) "
                          "for 5 minutes — activates the vagus nerve and lowers HR.",
                       duration="5 minutes", frequency="2–3× today"),
            ActionStep(5, "If HR stays above 100 bpm over 3+ days, "
                          "schedule a GP appointment.",
                       frequency="This week if persistent"),
        ],
        metric_value=float(m.heart_rate_bpm),
        target_value="55–75 bpm (resting)",
        icon="❤️",
        score_impact=12.0,
        tags=["heart-rate", "cardiovascular", "urgent", "monitor"],
    )


def rule_above_normal_hr(m: HealthMetrics) -> Optional[Recommendation]:
    """Fires when resting HR is 86–100 bpm."""
    if m.heart_rate_bpm is None:
        return None
    if not (HR.normal_max < m.heart_rate_bpm <= HR.elevated_min):
        return None
    return Recommendation(
        id="hr_above_normal",
        category=Category.HEART_RATE,
        priority=Priority.MEDIUM,
        title="Above-Normal Resting Heart Rate — Cardiovascular Fitness Opportunity",
        summary=(
            f"Resting HR of {m.heart_rate_bpm} bpm is above the ideal range. "
            "Regular aerobic exercise is the most effective way to lower resting HR."
        ),
        detail=(
            "Every 10 bpm reduction in resting HR is associated with a 30% reduction "
            "in cardiovascular mortality risk. 8–12 weeks of regular aerobic exercise "
            "(3–5× weekly) typically reduces resting HR by 5–15 bpm in sedentary adults. "
            "Stress reduction and improved sleep also contribute significantly."
        ),
        actions=[
            ActionStep(1, "Begin a 'Zone 2' cardio routine — brisk walking, cycling, "
                          "or swimming at a pace where you can still hold a conversation.",
                       duration="30 minutes", frequency="4× per week"),
            ActionStep(2, "Reduce stimulant intake: cap coffee at 2 cups before noon.",
                       frequency="Daily"),
            ActionStep(3, "Prioritise 7–9 hours of sleep — sleep deprivation raises "
                       "resting HR by 3–8 bpm.",
                       frequency="Nightly"),
            ActionStep(4, "Track your resting HR each morning before getting out of bed "
                          "to measure progress over weeks.",
                       frequency="Daily"),
        ],
        metric_value=float(m.heart_rate_bpm),
        target_value="55–75 bpm (resting)",
        icon="💓",
        score_impact=8.0,
        tags=["heart-rate", "cardiovascular", "fitness", "aerobic"],
    )


def rule_normal_hr(m: HealthMetrics) -> Optional[Recommendation]:
    """Fires when resting HR is 76–85 bpm — normal range, suggest improvement."""
    if m.heart_rate_bpm is None:
        return None
    if not (HR.good_max < m.heart_rate_bpm <= HR.normal_max):
        return None
    return Recommendation(
        id="hr_normal",
        category=Category.HEART_RATE,
        priority=Priority.LOW,
        title="Normal Resting Heart Rate — Room to Optimise",
        summary=(
            f"Resting HR of {m.heart_rate_bpm} bpm — within normal range. "
            "Consistent aerobic training can bring this into the 'good' range (66–75 bpm)."
        ),
        detail=(
            "A normal resting HR is healthy. Optimising toward 60–70 bpm through "
            "regular aerobic exercise increases your cardiac efficiency and reduces "
            "long-term cardiovascular risk."
        ),
        actions=[
            ActionStep(1, "Add 20–30 minutes of moderate aerobic exercise 3× per week.",
                       duration="20–30 minutes", frequency="3× per week"),
            ActionStep(2, "Morning HR tracking helps you see fitness improvements "
                          "over 4–8 weeks.", frequency="Daily morning"),
        ],
        metric_value=float(m.heart_rate_bpm),
        target_value="55–75 bpm (resting)",
        icon="💗",
        score_impact=4.0,
        tags=["heart-rate", "aerobic", "optimise"],
    )


def rule_good_hr(m: HealthMetrics) -> Optional[Recommendation]:
    """Fires when resting HR is 56–75 bpm — good cardiovascular fitness."""
    if m.heart_rate_bpm is None:
        return None
    if not (HR.athlete_max < m.heart_rate_bpm <= HR.good_max):
        return None
    return Recommendation(
        id="hr_good",
        category=Category.HEART_RATE,
        priority=Priority.LOW,
        title="Good Resting Heart Rate — Cardiovascular Health is Strong",
        summary=(
            f"Resting HR of {m.heart_rate_bpm} bpm — excellent cardiovascular "
            "fitness indicator. Keep up your aerobic exercise habit."
        ),
        detail=(
            "A resting HR in the 55–75 range indicates efficient heart function. "
            "Your heart pumps more blood per beat, reducing wear over a lifetime."
        ),
        actions=[
            ActionStep(1, "Maintain your current aerobic exercise routine.",
                       frequency="Ongoing"),
            ActionStep(2, "Continue monitoring morning HR — a sudden rise of 5–7 bpm "
                          "signals overtraining or illness early.",
                       frequency="Daily"),
        ],
        metric_value=float(m.heart_rate_bpm),
        target_value="55–75 bpm (resting)",
        icon="✅",
        score_impact=0.0,
        tags=["heart-rate", "positive", "maintain"],
    )


def rule_athlete_hr(m: HealthMetrics) -> Optional[Recommendation]:
    """Fires when resting HR < 56 bpm — athlete-level fitness."""
    if m.heart_rate_bpm is None or m.heart_rate_bpm > HR.athlete_max:
        return None
    return Recommendation(
        id="hr_athlete",
        category=Category.HEART_RATE,
        priority=Priority.LOW,
        title="Athlete-Level Resting Heart Rate",
        summary=(
            f"Resting HR of {m.heart_rate_bpm} bpm — elite cardiovascular fitness. "
            "This indicates a highly efficient heart."
        ),
        detail=(
            "Resting HR under 55 bpm typically reflects high cardiovascular fitness "
            "from regular aerobic training. Notable: very low resting HR can also "
            "occasionally indicate bradycardia (heart rhythm disorder) — "
            "if accompanied by dizziness or fatigue, consult a cardiologist."
        ),
        actions=[
            ActionStep(1, "If you experience dizziness or fatigue, consult a cardiologist "
                          "to rule out pathological bradycardia.",
                       frequency="If symptomatic"),
            ActionStep(2, "Focus on recovery: maintain sleep quality and manage "
                          "training load to prevent overtraining.", frequency="Ongoing"),
        ],
        metric_value=float(m.heart_rate_bpm),
        target_value="< 55 bpm (athlete)",
        icon="🏅",
        score_impact=0.0,
        tags=["heart-rate", "athlete", "excellent"],
    )


HEART_RATE_RULES = [
    rule_elevated_hr,
    rule_above_normal_hr,
    rule_normal_hr,
    rule_good_hr,
    rule_athlete_hr,
]
