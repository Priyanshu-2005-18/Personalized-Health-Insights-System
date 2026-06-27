"""
rules/nutrition_rules.py
========================
Rule-based nutrition recommendations based on calorie intake.
"""

from typing import Optional
from app.models.health import (
    ActionStep, Category, HealthMetrics, Priority, Recommendation
)
from app.rules.thresholds import CALORIES, STEPS


def rule_critically_low_calories(m: HealthMetrics) -> Optional[Recommendation]:
    """Fires when calories < 1200 — dangerous restriction."""
    if m.calories is None or m.calories >= CALORIES.critically_low:
        return None
    return Recommendation(
        id="nutrition_critical_low",
        category=Category.NUTRITION,
        priority=Priority.CRITICAL,
        title="Dangerously Low Calorie Intake",
        summary=(
            f"Only {m.calories} kcal consumed today. Below 1,200 kcal causes "
            "muscle catabolism, metabolic slowdown, and nutrient deficiencies."
        ),
        detail=(
            "Eating under 1,200 kcal triggers the body to break down muscle for "
            "energy (gluconeogenesis), slows thyroid function, and depletes "
            "essential vitamins and minerals. This is counterproductive for any "
            "health goal. If intentional (e.g. intermittent fasting), ensure "
            "medical supervision."
        ),
        actions=[
            ActionStep(1, "Eat a nutrient-dense meal within the next 2 hours: "
                          "protein + complex carbs + healthy fat.",
                       duration="Within 2 hours", frequency="Today"),
            ActionStep(2, "Aim for a minimum of 1,400–1,600 kcal distributed "
                          "across 3–4 meals.",
                       frequency="Daily minimum"),
            ActionStep(3, "Include protein at every meal to protect muscle mass: "
                          "eggs, chicken, legumes, dairy, tofu.",
                       frequency="Every meal"),
            ActionStep(4, "If restricting intentionally, consult a registered "
                          "dietitian for a safe, evidence-based plan.",
                       frequency="This week"),
        ],
        metric_value=float(m.calories),
        target_value="1,600–2,400 kcal/day",
        icon="⚠️",
        score_impact=16.0,
        tags=["nutrition", "urgent", "calories", "protein"],
    )


def rule_low_calories(m: HealthMetrics) -> Optional[Recommendation]:
    """Fires when calories are 1200–1499."""
    if m.calories is None:
        return None
    if not (CALORIES.critically_low <= m.calories < CALORIES.low):
        return None
    return Recommendation(
        id="nutrition_low",
        category=Category.NUTRITION,
        priority=Priority.HIGH,
        title="Below Minimum Calorie Threshold",
        summary=(
            f"{m.calories} kcal today — below the recommended minimum. "
            "Insufficient fuel reduces energy, cognitive performance, and "
            "athletic recovery."
        ),
        detail=(
            "At this intake level you may experience fatigue, poor concentration, "
            "and slowed physical recovery. Your body needs consistent energy to "
            "maintain organ function, thermoregulation, and cellular repair."
        ),
        actions=[
            ActionStep(1, "Add a calorie-dense snack today: nut butter on wholegrain "
                          "toast, trail mix, or a protein smoothie.",
                       duration="This afternoon", frequency="Today"),
            ActionStep(2, "Increase portion sizes gradually — add one extra serving "
                          "of protein or complex carbs to each meal.",
                       frequency="Daily"),
            ActionStep(3, "Track your intake for 3 days using MyFitnessPal "
                          "to get an accurate picture.", frequency="3 days"),
        ],
        metric_value=float(m.calories),
        target_value="1,600–2,400 kcal/day",
        icon="🍽️",
        score_impact=10.0,
        tags=["nutrition", "calories", "energy"],
    )


def rule_optimal_calories(m: HealthMetrics) -> Optional[Recommendation]:
    """Fires when calories are in the healthy range 1600–2400."""
    if m.calories is None:
        return None
    if not (CALORIES.optimal_low <= m.calories <= CALORIES.optimal_high):
        return None

    # Refine advice based on activity level
    if m.steps is not None and m.steps >= STEPS.active:
        detail = (
            "Given your active day, your calorie intake looks well balanced. "
            "Ensure protein is ≥ 0.8g per kg body weight to support muscle recovery."
        )
        action_extra = "Include a post-activity protein source within 45 minutes of exercise."
    else:
        detail = (
            "You're in the optimal calorie zone. Focus on food quality — prioritise "
            "whole foods, lean protein, fibre, and healthy fats over processed sources."
        )
        action_extra = "Aim for 5 servings of vegetables/fruit across your meals today."

    return Recommendation(
        id="nutrition_optimal",
        category=Category.NUTRITION,
        priority=Priority.LOW,
        title="Calorie Intake on Target — Focus on Food Quality",
        summary=(
            f"{m.calories} kcal — right in the healthy range. "
            "Now optimise what those calories are made of."
        ),
        detail=detail,
        actions=[
            ActionStep(1, action_extra, frequency="Daily"),
            ActionStep(2, "Ensure each meal includes a quality protein source "
                          "(≥ 20–30g per meal).", frequency="Every meal"),
            ActionStep(3, "Minimise ultra-processed foods — prioritise "
                          "whole grains, legumes, and vegetables.", frequency="Daily"),
        ],
        metric_value=float(m.calories),
        target_value="1,600–2,400 kcal/day",
        icon="✅",
        score_impact=2.0,
        tags=["nutrition", "quality", "protein", "positive"],
    )


def rule_high_calories(m: HealthMetrics) -> Optional[Recommendation]:
    """Fires when calories are 2400–3500."""
    if m.calories is None:
        return None
    if not (CALORIES.optimal_high < m.calories <= CALORIES.very_high):
        return None

    # If very active, high calories may be appropriate
    if m.steps is not None and m.steps >= STEPS.highly_active:
        return Recommendation(
            id="nutrition_high_active",
            category=Category.NUTRITION,
            priority=Priority.LOW,
            title="High Calorie Intake — Appropriate for Your Activity Level",
            summary=(
                f"{m.calories} kcal consumed. Given your high activity today "
                f"({m.steps:,} steps), this calorie intake may be appropriate."
            ),
            detail=(
                "Active individuals and athletes often need 2,500–3,500 kcal. "
                "Ensure calories are coming from quality sources — complex carbs "
                "for fuel, lean protein for recovery, healthy fats for hormones."
            ),
            actions=[
                ActionStep(1, "Prioritise complex carbs (oats, sweet potato, rice) "
                              "for sustained energy.", frequency="Daily"),
                ActionStep(2, "Target 1.6–2.2g protein per kg bodyweight for "
                              "athletic recovery.", frequency="Daily"),
            ],
            metric_value=float(m.calories),
            target_value="Maintain with quality sources",
            icon="⚡",
            score_impact=1.0,
            tags=["nutrition", "athlete", "active"],
        )

    return Recommendation(
        id="nutrition_high",
        category=Category.NUTRITION,
        priority=Priority.MEDIUM,
        title="Above Optimal Calorie Intake — Review Meal Choices",
        summary=(
            f"{m.calories} kcal today — above the recommended range for most adults. "
            "Consistent surplus leads to gradual weight gain and metabolic strain."
        ),
        detail=(
            "A calorie surplus of 500 kcal/day leads to approximately 0.5kg/week "
            "weight gain. Focus on reducing portion sizes of calorie-dense foods "
            "(oils, sweets, processed snacks) while keeping nutrient-dense foods high."
        ),
        actions=[
            ActionStep(1, "Reduce portion sizes of calorie-dense items by 20% at "
                          "your next meal.", frequency="Next meal"),
            ActionStep(2, "Replace high-calorie snacks with fruit, vegetables, or "
                          "natural yoghurt.", frequency="Daily"),
            ActionStep(3, "Use smaller plates — research shows this reduces intake "
                          "by 20–25% without feelings of deprivation.",
                       frequency="Every meal"),
            ActionStep(4, "Add 20 minutes of walking after dinner to improve "
                          "post-meal blood sugar control.", duration="20 minutes",
                       frequency="After dinner"),
        ],
        metric_value=float(m.calories),
        target_value="1,600–2,400 kcal/day",
        icon="🍽️",
        score_impact=6.0,
        tags=["nutrition", "portion", "weight", "blood-sugar"],
    )


def rule_very_high_calories(m: HealthMetrics) -> Optional[Recommendation]:
    """Fires when calories > 3500."""
    if m.calories is None or m.calories <= CALORIES.very_high:
        return None
    return Recommendation(
        id="nutrition_very_high",
        category=Category.NUTRITION,
        priority=Priority.HIGH,
        title="Very High Calorie Intake — Significant Surplus",
        summary=(
            f"{m.calories} kcal today — well above recommended levels. "
            "Regular intake at this level significantly increases metabolic "
            "and cardiovascular risk."
        ),
        detail=(
            "Consistently eating over 3,500 kcal (without equivalent exercise) "
            "leads to rapid weight gain, insulin resistance, elevated triglycerides, "
            "and increased inflammatory markers. Tracking intake and identifying "
            "high-calorie triggers is the essential first step."
        ),
        actions=[
            ActionStep(1, "Log your meals for the next 3 days to identify calorie "
                          "hotspots.", frequency="3 days"),
            ActionStep(2, "Identify and reduce your 2 highest-calorie food sources "
                          "this week.", frequency="This week"),
            ActionStep(3, "Increase physical activity to offset surplus — "
                          "30 minutes of brisk walking burns ~150 kcal.",
                       duration="30 minutes", frequency="Daily"),
            ActionStep(4, "Consider a consultation with a registered dietitian "
                          "for a personalised plan.", frequency="This month"),
        ],
        metric_value=float(m.calories),
        target_value="1,600–2,400 kcal/day",
        icon="🔴",
        score_impact=12.0,
        tags=["nutrition", "urgent", "metabolic", "weight"],
    )


NUTRITION_RULES = [
    rule_critically_low_calories,
    rule_low_calories,
    rule_very_high_calories,
    rule_high_calories,
    rule_optimal_calories,
]
