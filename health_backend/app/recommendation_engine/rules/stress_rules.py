from typing import Optional
from app.recommendation_engine.models.health import (
    ActionStep, Category, HealthMetrics, Priority, Recommendation
)
from app.recommendation_engine.rules.thresholds import SLEEP, STRESS


def rule_extreme_stress(m: HealthMetrics) -> Optional[Recommendation]:
    """Fires when stress = 10 — crisis-level stress."""
    if m.stress_level is None or m.stress_level < STRESS.very_high_max:
        return None
    return Recommendation(
        id="stress_extreme",
        category=Category.STRESS,
        priority=Priority.CRITICAL,
        title="Extreme Stress Level — Immediate Relief Needed",
        summary=(
            f"Stress level {m.stress_level}/10 — this is extremely high. "
            "Chronic extreme stress raises cortisol, damages cardiovascular health, "
            "and can trigger mental health crises."
        ),
        detail=(
            "At this stress level, your body is in prolonged fight-or-flight mode. "
            "Cortisol suppresses the immune system, raises blood pressure, disrupts "
            "sleep, and impairs memory. Immediate relief techniques and professional "
            "support are both strongly recommended."
        ),
        actions=[
            ActionStep(1, "Try box breathing right now: inhale 4 counts, hold 4, "
                          "exhale 4, hold 4. Repeat 4 times.",
                       duration="2 minutes", frequency="Whenever stress peaks"),
            ActionStep(2, "Step outside for 10 minutes — natural light and fresh air "
                          "lower cortisol within minutes.",
                       duration="10 minutes", frequency="Twice today"),
            ActionStep(3, "Identify the primary stressor and write it down — "
                          "externalising reduces perceived threat.",
                       duration="5 minutes", frequency="Today"),
            ActionStep(4, "Contact a trusted person for support — social connection "
                          "activates the parasympathetic nervous system.",
                       frequency="Today"),
            ActionStep(5, "If stress is persistent, consider speaking with a "
                          "therapist or GP this week.",
                       frequency="This week"),
        ],
        metric_value=float(m.stress_level),
        target_value="1–3 (low)",
        icon="🆘",
        score_impact=18.0,
        tags=["stress", "urgent", "cortisol", "mental-health"],
    )


def rule_high_stress(m: HealthMetrics) -> Optional[Recommendation]:
    """Fires when stress is 7–9."""
    if m.stress_level is None:
        return None
    if not (STRESS.high_max < m.stress_level <= STRESS.very_high_max):
        return None

    compound_note = ""
    if m.sleep_hours is not None and m.sleep_hours < SLEEP.poor_low:
        compound_note = (
            " Combined with your low sleep today, this creates a particularly "
            "high cortisol environment that compounds health risks."
        )
    return Recommendation(
        id="stress_high",
        category=Category.STRESS,
        priority=Priority.HIGH,
        title="High Stress — Build Active Recovery Into Your Day",
        summary=(
            f"Stress level {m.stress_level}/10 — significantly elevated.{compound_note} "
            "Regular stress management techniques reduce cortisol within 10–20 minutes."
        ),
        detail=(
            "High cortisol for extended periods degrades hippocampal function "
            "(memory), raises blood pressure, and disrupts gut microbiome balance. "
            "Evidence-based techniques — breathing, movement, nature exposure — "
            "produce measurable cortisol reduction and should be treated as "
            "non-negotiable daily habits."
        ),
        actions=[
            ActionStep(1, "Practice 4-7-8 breathing: inhale 4s, hold 7s, exhale 8s. "
                          "Activates the vagus nerve and calms the nervous system.",
                       duration="5 minutes", frequency="3× daily"),
            ActionStep(2, "Take a 15-minute walk in natural surroundings — "
                          "green space exposure reduces cortisol by ~16%.",
                       duration="15 minutes", frequency="Daily"),
            ActionStep(3, "Reduce caffeine intake — it amplifies cortisol response "
                          "and should be capped at 200mg when stressed.",
                       frequency="Daily"),
            ActionStep(4, "Schedule one enjoyable activity today: music, a hobby, "
                          "a conversation with a friend.",
                       duration="30 minutes", frequency="Daily"),
        ],
        metric_value=float(m.stress_level),
        target_value="1–4 (low-moderate)",
        icon="😰",
        score_impact=13.0,
        tags=["stress", "cortisol", "breathing", "nature"],
    )


def rule_moderate_stress(m: HealthMetrics) -> Optional[Recommendation]:
    """Fires when stress is 5–7."""
    if m.stress_level is None:
        return None
    if not (STRESS.moderate_max < m.stress_level <= STRESS.high_max):
        return None
    return Recommendation(
        id="stress_moderate",
        category=Category.STRESS,
        priority=Priority.MEDIUM,
        title="Moderate Stress — Small Habits Make a Big Difference",
        summary=(
            f"Stress level {m.stress_level}/10 — manageable but worth addressing "
            "proactively. Daily micro-breaks and mindfulness prevent escalation."
        ),
        detail=(
            "Moderate stress is common but cumulative. Without intervention, "
            "moderate stress often escalates over days or weeks. Five-minute "
            "breathing exercises twice daily have been shown to reduce perceived "
            "stress by 25% over two weeks."
        ),
        actions=[
            ActionStep(1, "Try a 5-minute mindfulness app session (Headspace, Calm, "
                          "or Insight Timer — all free tier available).",
                       duration="5 minutes", frequency="Morning and evening"),
            ActionStep(2, "Build a 'stress log' — note what triggered stress today. "
                          "Patterns become manageable once identified.",
                       duration="3 minutes", frequency="End of each day"),
            ActionStep(3, "Ensure your next meal includes magnesium-rich foods: "
                          "dark chocolate, leafy greens, nuts, seeds.",
                       frequency="Today's meals"),
        ],
        metric_value=float(m.stress_level),
        target_value="1–4 (low-moderate)",
        icon="😐",
        score_impact=7.0,
        tags=["stress", "mindfulness", "habit", "nutrition"],
    )


def rule_mild_stress(m: HealthMetrics) -> Optional[Recommendation]:
    """Fires when stress is 4–5."""
    if m.stress_level is None:
        return None
    if not (STRESS.low_max < m.stress_level <= STRESS.moderate_max):
        return None
    return Recommendation(
        id="stress_mild",
        category=Category.STRESS,
        priority=Priority.LOW,
        title="Mild Stress — Maintain Your Current Coping Strategies",
        summary=(
            f"Stress level {m.stress_level}/10 — mild but present. "
            "Your current coping strategies seem to be working. Keep building them."
        ),
        detail=(
            "Mild stress can be motivating in short bursts (eustress). "
            "The key is preventing it from escalating through consistent "
            "self-care: good sleep, regular movement, and social connection."
        ),
        actions=[
            ActionStep(1, "Maintain your exercise routine — it's the most effective "
                          "long-term stress buffer.",
                       frequency="Daily"),
            ActionStep(2, "Schedule something to look forward to this week — "
                          "anticipatory positive emotion reduces stress baseline.",
                       frequency="This week"),
        ],
        metric_value=float(m.stress_level),
        target_value="1–3 (low)",
        icon="😌",
        score_impact=3.0,
        tags=["stress", "maintain", "mild"],
    )


def rule_low_stress(m: HealthMetrics) -> Optional[Recommendation]:
    """Fires when stress is 1–3 — positive reinforcement."""
    if m.stress_level is None or m.stress_level > STRESS.low_max:
        return None
    return Recommendation(
        id="stress_optimal",
        category=Category.STRESS,
        priority=Priority.LOW,
        title="Low Stress — Keep Protecting Your Mental Space",
        summary=(
            f"Stress level {m.stress_level}/10 — excellent. Low stress "
            "supports immune function, sleep quality, and longevity."
        ),
        detail=(
            "You're managing stress well. Protect this by guarding your sleep "
            "schedule, maintaining social connection, and continuing whatever "
            "activities bring you calm."
        ),
        actions=[
            ActionStep(1, "Identify what contributed to your low stress today "
                          "and replicate it.", frequency="Daily reflection"),
        ],
        metric_value=float(m.stress_level),
        target_value="1–3 (low)",
        icon="😊",
        score_impact=0.0,
        tags=["stress", "positive", "maintain"],
    )


STRESS_RULES = [
    rule_extreme_stress,
    rule_high_stress,
    rule_moderate_stress,
    rule_mild_stress,
    rule_low_stress,
]
