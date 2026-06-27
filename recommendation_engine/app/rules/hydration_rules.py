"""
rules/hydration_rules.py
========================
Rule-based hydration recommendations.
"""

from typing import Optional
from app.models.health import (
    ActionStep, Category, HealthMetrics, Priority, Recommendation
)
from app.rules.thresholds import HYDRATION, STEPS


def rule_severe_dehydration(m: HealthMetrics) -> Optional[Recommendation]:
    """Fires when water intake < 1000ml — severely dehydrated."""
    if m.water_intake_ml is None or m.water_intake_ml >= HYDRATION.severely_low:
        return None
    return Recommendation(
        id="hydration_severe",
        category=Category.HYDRATION,
        priority=Priority.CRITICAL,
        title="Severe Dehydration Risk — Drink Water Immediately",
        summary=(
            f"Only {m.water_intake_ml}ml consumed today. Severe dehydration impairs "
            "kidney function, drops blood pressure, and causes cognitive decline "
            "within hours."
        ),
        detail=(
            "At under 1,000ml, you are at risk of acute dehydration symptoms: "
            "headache, dizziness, dark urine, reduced concentration, and in severe "
            "cases, kidney stress. The body loses ~2.5L daily through breathing, "
            "sweat, and urine — this must be replaced. Drink 500ml of water right now."
        ),
        actions=[
            ActionStep(1, "Drink a large glass of water (500ml) immediately.",
                       duration="Now"),
            ActionStep(2, "Set a recurring 30-minute reminder to drink 200ml of water.",
                       frequency="Every 30 minutes"),
            ActionStep(3, "Keep a 1L water bottle visible on your desk at all times.",
                       frequency="Daily"),
            ActionStep(4, "Check urine colour — target pale yellow (lemonade colour). "
                          "Dark yellow or amber = dehydrated.",
                       frequency="Throughout the day"),
            ActionStep(5, "Eat water-rich foods: cucumber, watermelon, oranges, soup.",
                       frequency="Today's meals"),
        ],
        metric_value=float(m.water_intake_ml),
        target_value="2,000–3,000ml/day",
        icon="🚨",
        score_impact=15.0,
        tags=["hydration", "urgent", "kidney", "cognitive"],
    )


def rule_dehydrated(m: HealthMetrics) -> Optional[Recommendation]:
    """Fires when water intake is 1000–1499ml."""
    if m.water_intake_ml is None:
        return None
    if not (HYDRATION.severely_low <= m.water_intake_ml < HYDRATION.low):
        return None
    return Recommendation(
        id="hydration_low",
        category=Category.HYDRATION,
        priority=Priority.HIGH,
        title="Below Hydration Minimum — Increase Water Intake",
        summary=(
            f"{m.water_intake_ml}ml consumed — under the 1,500ml minimum. "
            "Even mild dehydration (1–2% body weight) reduces cognitive performance "
            "by up to 13%."
        ),
        detail=(
            "Mild dehydration affects concentration, memory, and mood before thirst "
            "is even felt. By the time you feel thirsty, you're already 1–2% "
            "dehydrated. Building a habit of proactive drinking — not reactive — "
            "is the key to consistent hydration."
        ),
        actions=[
            ActionStep(1, "Drink a glass of water with every meal and snack.",
                       frequency="Every meal"),
            ActionStep(2, "Start every morning with 500ml of water before coffee.",
                       duration="First 10 minutes of the day", frequency="Daily"),
            ActionStep(3, "Use a marked water bottle (500ml marks) to track intake visually.",
                       frequency="Daily"),
            ActionStep(4, "Add a slice of lemon, cucumber, or mint if plain water "
                          "is unappealing.", frequency="Daily"),
        ],
        metric_value=float(m.water_intake_ml),
        target_value="2,000–3,000ml/day",
        icon="💧",
        score_impact=10.0,
        tags=["hydration", "cognitive", "habit"],
    )


def rule_below_target(m: HealthMetrics) -> Optional[Recommendation]:
    """Fires when water intake is 1500–1999ml."""
    if m.water_intake_ml is None:
        return None
    if not (HYDRATION.low <= m.water_intake_ml < HYDRATION.optimal_low):
        return None

    # Adjust target upward if user is very active
    extra_note = ""
    if m.steps is not None and m.steps >= STEPS.active:
        extra_note = (
            " Given your high activity level today, you likely need an "
            "additional 500–700ml to compensate for sweat losses."
        )
    return Recommendation(
        id="hydration_below_target",
        category=Category.HYDRATION,
        priority=Priority.MEDIUM,
        title="Hydration Reminder — Almost at Your Daily Target",
        summary=(
            f"{m.water_intake_ml}ml in — you're close to the 2,000ml minimum. "
            f"A few more glasses will get you there.{extra_note}"
        ),
        detail=(
            "You're making good progress. Reaching 2,000–2,500ml consistently "
            "supports kidney health, skin hydration, and metabolic efficiency. "
            "The final push before bed is often where people fall short."
        ),
        actions=[
            ActionStep(1, "Drink 2 more glasses (400–500ml) before the end of the day.",
                       duration="This evening", frequency="Today"),
            ActionStep(2, "Herbal teas and diluted fruit juice count toward intake.",
                       frequency="Ongoing"),
            ActionStep(3, "Aim to finish your water bottle before 8 PM to avoid "
                          "disruptive overnight trips.",
                       frequency="Daily"),
        ],
        metric_value=float(m.water_intake_ml),
        target_value="2,000–3,000ml/day",
        icon="💦",
        score_impact=5.0,
        tags=["hydration", "reminder", "optimise"],
    )


def rule_well_hydrated(m: HealthMetrics) -> Optional[Recommendation]:
    """Fires when water intake is 2000ml+ — positive reinforcement."""
    if m.water_intake_ml is None or m.water_intake_ml < HYDRATION.optimal_low:
        return None
    return Recommendation(
        id="hydration_optimal",
        category=Category.HYDRATION,
        priority=Priority.LOW,
        title="Well Hydrated — Excellent Work",
        summary=(
            f"{m.water_intake_ml}ml today — you're hitting your hydration target. "
            "Keep distributing intake evenly throughout the day."
        ),
        detail=(
            "Consistent hydration supports metabolic function, kidney health, and "
            "thermoregulation. Spread intake evenly across the day rather than "
            "drinking large amounts at once for best absorption."
        ),
        actions=[
            ActionStep(1, "Keep distributing water intake — aim for 200–300ml per hour.",
                       frequency="Ongoing"),
            ActionStep(2, "On high-activity days or hot weather, add 500–700ml extra.",
                       frequency="As needed"),
        ],
        metric_value=float(m.water_intake_ml),
        target_value="2,000–3,000ml/day",
        icon="✅",
        score_impact=0.0,
        tags=["hydration", "positive", "maintain"],
    )


HYDRATION_RULES = [
    rule_severe_dehydration,
    rule_dehydrated,
    rule_below_target,
    rule_well_hydrated,
]
