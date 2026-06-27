from typing import Optional
from app.recommendation_engine.models.health import (
    ActionStep, Category, HealthMetrics, Priority, Recommendation
)
from app.recommendation_engine.rules.thresholds import SLEEP


def rule_critical_sleep_deprivation(m: HealthMetrics) -> Optional[Recommendation]:
    """Fires when sleep < 5 hours — serious health risk."""
    if m.sleep_hours is None or m.sleep_hours >= SLEEP.critical_low:
        return None
    return Recommendation(
        id="sleep_critical_deprivation",
        category=Category.SLEEP,
        priority=Priority.CRITICAL,
        title="Critical Sleep Deprivation Detected",
        summary=(
            f"You slept only {m.sleep_hours:.1f} hours. "
            "Sleeping under 5 hours is linked to a 65% increased risk of "
            "cardiovascular disease, impaired immune function, and cognitive decline."
        ),
        detail=(
            "Chronic sleep deprivation suppresses immune response, disrupts cortisol "
            "regulation, and accelerates cellular ageing. Even one night under 5 hours "
            "reduces reaction time equivalent to a blood alcohol level of 0.08%. "
            "Prioritise sleep tonight as a medical necessity."
        ),
        actions=[
            ActionStep(1, "Go to bed at least 8 hours before your next alarm tonight.",
                       duration="Tonight", frequency="Every night this week"),
            ActionStep(2, "Eliminate all screens (phone, TV, laptop) 1 hour before bed.",
                       duration="60 minutes before bed", frequency="Daily"),
            ActionStep(3, "Keep your bedroom dark, quiet, and below 20°C (68°F).",
                       frequency="Every night"),
            ActionStep(4, "Avoid caffeine after 2 PM — it stays in your system 6–8 hours.",
                       frequency="Daily"),
            ActionStep(5, "If you cannot sleep, consider speaking with a healthcare provider "
                          "about sleep hygiene assessment.", frequency="This week"),
        ],
        metric_value=m.sleep_hours,
        target_value="7–9 hours",
        icon="🚨",
        score_impact=18.0,
        tags=["sleep", "urgent", "cardiovascular", "immune"],
    )


def rule_poor_sleep(m: HealthMetrics) -> Optional[Recommendation]:
    """Fires when sleep is 5–6 hours — consistently inadequate."""
    if m.sleep_hours is None:
        return None
    if not (SLEEP.critical_low <= m.sleep_hours < SLEEP.poor_low):
        return None
    return Recommendation(
        id="sleep_poor",
        category=Category.SLEEP,
        priority=Priority.HIGH,
        title="Insufficient Sleep — Build a Better Bedtime Routine",
        summary=(
            f"You slept {m.sleep_hours:.1f} hours, below the recommended 7–9 hours. "
            "Consistent sleep under 6 hours raises stress hormones and suppresses "
            "the immune system."
        ),
        detail=(
            "Adults sleeping 6 hours instead of 8 hours show 4× more susceptibility "
            "to the common cold. Sleep debt accumulates — you cannot fully 'recover' "
            "it on weekends. Building a consistent sleep routine is the highest-ROI "
            "health intervention available."
        ),
        actions=[
            ActionStep(1, "Set a fixed bedtime and wake time — even on weekends.",
                       frequency="Daily"),
            ActionStep(2, "Create a 20-minute wind-down routine: dim lights, light stretching "
                          "or reading (not screens).",
                       duration="20 minutes", frequency="Every evening"),
            ActionStep(3, "Limit alcohol — it fragments sleep architecture and reduces "
                          "REM sleep quality.",
                       frequency="Nightly"),
            ActionStep(4, "Try a 10-minute body-scan meditation to reduce pre-sleep anxiety.",
                       duration="10 minutes", frequency="Before bed"),
        ],
        metric_value=m.sleep_hours,
        target_value="7–9 hours",
        icon="😴",
        score_impact=12.0,
        tags=["sleep", "routine", "immune", "stress"],
    )


def rule_suboptimal_sleep(m: HealthMetrics) -> Optional[Recommendation]:
    """Fires when sleep is 6–7 hours — slightly below optimal."""
    if m.sleep_hours is None:
        return None
    if not (SLEEP.poor_low <= m.sleep_hours < SLEEP.optimal_low):
        return None
    return Recommendation(
        id="sleep_suboptimal",
        category=Category.SLEEP,
        priority=Priority.MEDIUM,
        title="Slightly Under Your Sleep Target",
        summary=(
            f"You slept {m.sleep_hours:.1f} hours — just below the 7-hour minimum. "
            "Small adjustments to your bedtime could unlock significant health benefits."
        ),
        detail=(
            "Even 30 extra minutes of sleep measurably improves mood, reaction time, "
            "and metabolic health. Most people underestimate their sleep need by 60–90 "
            "minutes. Try moving your bedtime 30 minutes earlier this week."
        ),
        actions=[
            ActionStep(1, "Move your bedtime 30 minutes earlier for the next 7 days.",
                       frequency="Daily this week"),
            ActionStep(2, "Expose yourself to natural daylight within 30 minutes of waking "
                          "— this anchors your circadian rhythm.",
                       duration="10–15 minutes", frequency="Every morning"),
            ActionStep(3, "Avoid heavy meals within 3 hours of bedtime.",
                       frequency="Nightly"),
        ],
        metric_value=m.sleep_hours,
        target_value="7–9 hours",
        icon="🌙",
        score_impact=6.0,
        tags=["sleep", "circadian", "optimise"],
    )


def rule_oversleeping(m: HealthMetrics) -> Optional[Recommendation]:
    """Fires when sleep > 9 hours — potential compensatory or health signal."""
    if m.sleep_hours is None or m.sleep_hours <= SLEEP.optimal_high:
        return None
    return Recommendation(
        id="sleep_excess",
        category=Category.SLEEP,
        priority=Priority.LOW,
        title="Extended Sleep — Monitor for Underlying Causes",
        summary=(
            f"You slept {m.sleep_hours:.1f} hours. Regularly sleeping over 9 hours "
            "can indicate sleep debt recovery, depression, thyroid issues, or "
            "poor sleep quality."
        ),
        detail=(
            "Occasionally sleeping 9–10 hours after accumulated sleep debt is normal. "
            "Consistently needing over 9 hours despite feeling unrefreshed may signal "
            "obstructive sleep apnoea, depression, or hypothyroidism. If this is "
            "a regular pattern, consult a healthcare provider."
        ),
        actions=[
            ActionStep(1, "Track your sleep for 7 days using a wearable or sleep journal "
                          "to identify patterns.", frequency="Daily for 1 week"),
            ActionStep(2, "Maintain a consistent wake time even when sleeping late — "
                          "this stabilises circadian rhythm.", frequency="Daily"),
            ActionStep(3, "If you feel unrefreshed despite 9+ hours, schedule a GP visit "
                          "to rule out sleep disorders.", frequency="This month"),
        ],
        metric_value=m.sleep_hours,
        target_value="7–9 hours",
        icon="⏰",
        score_impact=3.0,
        tags=["sleep", "monitor", "circadian"],
    )


def rule_optimal_sleep(m: HealthMetrics) -> Optional[Recommendation]:
    """Fires when sleep is in the optimal 7–9 hour range — positive reinforcement."""
    if m.sleep_hours is None:
        return None
    if not (SLEEP.optimal_low <= m.sleep_hours <= SLEEP.optimal_high):
        return None
    return Recommendation(
        id="sleep_optimal",
        category=Category.SLEEP,
        priority=Priority.LOW,
        title="Great Sleep Duration — Keep It Consistent",
        summary=(
            f"Excellent! You slept {m.sleep_hours:.1f} hours — right in the "
            "optimal 7–9 hour window. Consistency is key to sustaining these benefits."
        ),
        detail=(
            "You're hitting the sleep sweet spot. To maintain this: protect your "
            "sleep schedule on weekends, keep the bedroom cool and dark, and "
            "continue your current bedtime routine."
        ),
        actions=[
            ActionStep(1, "Maintain your current sleep schedule on weekends (±30 min max).",
                       frequency="Weekly"),
            ActionStep(2, "Consider tracking sleep quality (not just duration) with a "
                       "wearable to optimise REM and deep sleep.",
                       frequency="Ongoing"),
        ],
        metric_value=m.sleep_hours,
        target_value="7–9 hours",
        icon="✅",
        score_impact=0.0,
        tags=["sleep", "positive", "maintain"],
    )


SLEEP_RULES = [
    rule_critical_sleep_deprivation,
    rule_poor_sleep,
    rule_suboptimal_sleep,
    rule_oversleeping,
    rule_optimal_sleep,
]
