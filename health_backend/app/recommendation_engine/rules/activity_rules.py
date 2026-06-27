from typing import Optional
from app.recommendation_engine.models.health import (
    ActionStep, Category, HealthMetrics, Priority, Recommendation
)
from app.recommendation_engine.rules.thresholds import STEPS


def rule_sedentary(m: HealthMetrics) -> Optional[Recommendation]:
    """Fires when steps < 2500 — sedentary lifestyle."""
    if m.steps is None or m.steps >= STEPS.sedentary:
        return None
    return Recommendation(
        id="activity_sedentary",
        category=Category.ACTIVITY,
        priority=Priority.CRITICAL,
        title="Sedentary Alert — Your Body Needs to Move",
        summary=(
            f"Only {m.steps:,} steps today. Fewer than 2,500 steps is classified as "
            "sedentary and is associated with a 73% higher risk of metabolic syndrome."
        ),
        detail=(
            "Prolonged sitting slows metabolism, stiffens arteries, and increases "
            "insulin resistance independent of exercise habits. Even standing for "
            "5 minutes every hour produces measurable cardiovascular benefit. "
            "Today's goal: reach 5,000 steps — just 40 minutes of casual walking."
        ),
        actions=[
            ActionStep(1, "Stand up and walk for 5 minutes right now.",
                       duration="5 minutes", frequency="Every hour"),
            ActionStep(2, "Take a brisk 20-minute walk after your next meal.",
                       duration="20 minutes", frequency="After each meal"),
            ActionStep(3, "Set an hourly movement reminder on your phone.",
                       frequency="Daily"),
            ActionStep(4, "Park further from your destination or get off public "
                          "transport one stop early.",
                       frequency="Daily"),
            ActionStep(5, "Aim for 5,000 steps as this week's minimum daily target.",
                       frequency="Daily this week"),
        ],
        metric_value=float(m.steps),
        target_value="10,000 steps/day",
        icon="🚨",
        score_impact=20.0,
        tags=["activity", "urgent", "sedentary", "metabolic"],
    )


def rule_low_active(m: HealthMetrics) -> Optional[Recommendation]:
    """Fires when steps are 2500–4999."""
    if m.steps is None:
        return None
    if not (STEPS.sedentary <= m.steps < STEPS.low_active):
        return None
    return Recommendation(
        id="activity_low",
        category=Category.ACTIVITY,
        priority=Priority.HIGH,
        title="Low Activity Level — Time to Add More Movement",
        summary=(
            f"{m.steps:,} steps today. You're in the 'low active' range. "
            "Increasing to 7,500+ steps reduces all-cause mortality risk by up to 50%."
        ),
        detail=(
            "Research from JAMA Internal Medicine shows that benefits plateau "
            "at around 7,500 steps/day for mortality outcomes. You're about 2,500 "
            "steps away from significant health gains. Adding one 20-minute walk "
            "per day bridges that gap."
        ),
        actions=[
            ActionStep(1, "Add one 20-minute brisk walk to your daily routine.",
                       duration="20 minutes", frequency="Daily"),
            ActionStep(2, "Take stairs instead of lifts for all journeys under 5 floors.",
                       frequency="Daily"),
            ActionStep(3, "Walk during phone calls instead of sitting.",
                       frequency="Every call"),
            ActionStep(4, "Try a lunchtime 10-minute walk to break up the workday.",
                       duration="10 minutes", frequency="Weekdays"),
        ],
        metric_value=float(m.steps),
        target_value="7,500–10,000 steps/day",
        icon="🚶",
        score_impact=14.0,
        tags=["activity", "walking", "cardiovascular"],
    )


def rule_somewhat_active(m: HealthMetrics) -> Optional[Recommendation]:
    """Fires when steps are 5000–7499."""
    if m.steps is None:
        return None
    if not (STEPS.low_active <= m.steps < STEPS.somewhat_active):
        return None
    return Recommendation(
        id="activity_moderate",
        category=Category.ACTIVITY,
        priority=Priority.MEDIUM,
        title="Good Start — Push Toward the 7,500 Step Goal",
        summary=(
            f"{m.steps:,} steps — you're moving but haven't reached the "
            "evidence-based minimum of 7,500 steps. A small push yields big results."
        ),
        detail=(
            "You're in the 'somewhat active' zone. Adding 10–15 minutes of walking "
            "spread across the day will push you past 7,500 steps and into the "
            "range where significant mortality benefits are observed."
        ),
        actions=[
            ActionStep(1, "Add two 5-minute walking breaks to your afternoon.",
                       duration="5 minutes each", frequency="Daily"),
            ActionStep(2, "Try a 15-minute walk after dinner — it also aids digestion "
                          "and blood sugar regulation.",
                       duration="15 minutes", frequency="Daily"),
            ActionStep(3, "Use a step tracker widget on your phone home screen "
                          "for real-time motivation.", frequency="Ongoing"),
        ],
        metric_value=float(m.steps),
        target_value="7,500–10,000 steps/day",
        icon="🏃",
        score_impact=7.0,
        tags=["activity", "walking", "optimise"],
    )


def rule_active(m: HealthMetrics) -> Optional[Recommendation]:
    """Fires when steps are 7500–9999 — active, suggest strength training."""
    if m.steps is None:
        return None
    if not (STEPS.somewhat_active <= m.steps < STEPS.active):
        return None
    return Recommendation(
        id="activity_good",
        category=Category.ACTIVITY,
        priority=Priority.LOW,
        title="Active Lifestyle — Add Strength Training for Full Benefits",
        summary=(
            f"{m.steps:,} steps — great cardio foundation! Complement it with "
            "2× weekly strength training to maximise metabolic health."
        ),
        detail=(
            "You're hitting solid cardiovascular activity targets. The WHO recommends "
            "also including muscle-strengthening activities ≥2 days/week. Resistance "
            "training improves insulin sensitivity, bone density, and resting "
            "metabolic rate beyond what steps alone provide."
        ),
        actions=[
            ActionStep(1, "Add 2 strength training sessions per week (bodyweight or weights).",
                       duration="30 minutes", frequency="2× per week"),
            ActionStep(2, "Include compound movements: squats, push-ups, lunges, rows.",
                       duration="30 minutes", frequency="Each session"),
            ActionStep(3, "Aim to hit 10,000 steps to reach the AHA 'active' benchmark.",
                       frequency="Daily"),
        ],
        metric_value=float(m.steps),
        target_value="10,000 steps/day + 2× strength",
        icon="💪",
        score_impact=4.0,
        tags=["activity", "strength", "optimise"],
    )


def rule_highly_active(m: HealthMetrics) -> Optional[Recommendation]:
    """Fires when steps >= 10000 — highly active, focus on recovery."""
    if m.steps is None or m.steps < STEPS.active:
        return None
    return Recommendation(
        id="activity_excellent",
        category=Category.ACTIVITY,
        priority=Priority.LOW,
        title="Excellent Activity — Prioritise Recovery to Sustain It",
        summary=(
            f"Outstanding! {m.steps:,} steps today. At this activity level, "
            "recovery quality determines long-term sustainability."
        ),
        detail=(
            "You're well above the active threshold. Overtraining without adequate "
            "recovery increases injury risk and cortisol. Focus on sleep quality, "
            "protein intake, and occasional lower-intensity days."
        ),
        actions=[
            ActionStep(1, "Ensure 7–9 hours of sleep to support muscle repair.",
                       frequency="Nightly"),
            ActionStep(2, "Include 1–2 active recovery days per week "
                          "(light walking, yoga, stretching).",
                       frequency="Weekly"),
            ActionStep(3, "Hydrate well — aim for ≥ 3L water on high-activity days.",
                       frequency="Daily"),
        ],
        metric_value=float(m.steps),
        target_value="Maintain + prioritise recovery",
        icon="🏅",
        score_impact=0.0,
        tags=["activity", "excellent", "recovery"],
    )


ACTIVITY_RULES = [
    rule_sedentary,
    rule_low_active,
    rule_somewhat_active,
    rule_active,
    rule_highly_active,
]
