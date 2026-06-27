"""
thresholds.py
=============
Single source of truth for every health threshold and scoring weight
used across the recommendation engine.

Changing a value here automatically updates ALL rules that reference it —
no hunting through scattered magic numbers.

Sources:
  Sleep    — WHO / National Sleep Foundation guidelines
  Steps    — American Heart Association (AHA) physical activity guidelines
  Calories — USDA Dietary Guidelines 2020-2025
  Water    — European Food Safety Authority (EFSA) adequate intake values
  Stress   — Perceived Stress Scale (PSS-10) clinical thresholds
  HR       — American College of Cardiology resting HR classifications
"""

from dataclasses import dataclass


# ─────────────────────────────────────────────────────────────────────────────
#  Feature value ranges (domain validation)
# ─────────────────────────────────────────────────────────────────────────────

VALID_RANGES = {
    "sleep_hours":     (0.0,  24.0),
    "steps":           (0,    100_000),
    "calories":        (0,    10_000),
    "water_intake_ml": (0,    10_000),
    "stress_level":    (1,    10),
    "heart_rate_bpm":  (30,   250),
    "health_score":    (0.0,  100.0),
}


# ─────────────────────────────────────────────────────────────────────────────
#  Sleep thresholds
# ─────────────────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class SleepThresholds:
    critical_low:  float = 5.0    # < 5h   → critical deprivation
    poor_low:      float = 6.0    # < 6h   → poor sleep
    optimal_low:   float = 7.0    # 7–9h   → optimal range
    optimal_high:  float = 9.0    # > 9h   → possible oversleeping
    excess_high:   float = 10.0   # > 10h  → likely compensatory / illness
    # Sub-score normalisation
    score_min_h:   float = 3.0    # 3h maps to score 0
    score_max_h:   float = 9.0    # 9h maps to score 100
    optimal_target: float = 8.0   # ideal hours for score peak

SLEEP = SleepThresholds()


# ─────────────────────────────────────────────────────────────────────────────
#  Physical activity thresholds
# ─────────────────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class StepThresholds:
    sedentary:      int = 2_500   # < 2500  → sedentary
    low_active:     int = 5_000   # < 5000  → low active
    somewhat_active: int = 7_500  # < 7500  → somewhat active
    active:         int = 10_000  # ≥ 10000 → active (AHA target)
    highly_active:  int = 12_500  # ≥ 12500 → highly active

STEPS = StepThresholds()


# ─────────────────────────────────────────────────────────────────────────────
#  Calorie thresholds
# ─────────────────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class CalorieThresholds:
    critically_low: int = 1_200   # < 1200  → dangerous restriction
    low:            int = 1_500   # < 1500  → below minimum
    optimal_low:    int = 1_600   # lower bound of healthy range
    optimal_high:   int = 2_400   # upper bound of healthy range
    high:           int = 2_800   # > 2800  → moderately high
    very_high:      int = 3_500   # > 3500  → high surplus
    optimal_target: int = 2_000   # reference point for scoring

CALORIES = CalorieThresholds()


# ─────────────────────────────────────────────────────────────────────────────
#  Hydration thresholds
# ─────────────────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class HydrationThresholds:
    severely_low:   int = 1_000   # < 1000 ml → severely dehydrated
    low:            int = 1_500   # < 1500 ml → dehydrated
    below_target:   int = 2_000   # < 2000 ml → below recommended
    optimal_low:    int = 2_000   # 2000 ml → minimum adequate
    optimal_target: int = 2_500   # 2500 ml → EFSA AI (sedentary women)
    optimal_high:   int = 3_000   # 3000 ml → EFSA AI (sedentary men)
    score_max_ml:   int = 3_000   # maps to score 100

HYDRATION = HydrationThresholds()


# ─────────────────────────────────────────────────────────────────────────────
#  Stress thresholds (1–10 scale)
# ─────────────────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class StressThresholds:
    low_max:        int = 3    # 1–3  → low stress
    moderate_max:   int = 5    # 4–5  → moderate
    high_max:       int = 7    # 6–7  → high
    very_high_max:  int = 9    # 8–9  → very high
    extreme_min:    int = 10   # 10   → extreme / crisis

STRESS = StressThresholds()


# ─────────────────────────────────────────────────────────────────────────────
#  Heart rate thresholds (resting BPM)
# ─────────────────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class HeartRateThresholds:
    athlete_max:    int = 55    # < 55  → athlete / very fit
    excellent_max:  int = 65    # 55–65 → excellent
    good_max:       int = 75    # 66–75 → good
    normal_max:     int = 85    # 76–85 → normal
    above_normal:   int = 100   # 86–100 → above normal, monitor
    elevated_min:   int = 100   # > 100 → tachycardia, seek advice
    optimal_target: int = 62    # ideal for sub-score calculation

HR = HeartRateThresholds()


# ─────────────────────────────────────────────────────────────────────────────
#  Overall health score bands
# ─────────────────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class HealthScoreBands:
    critical_max:  float = 40.0   # < 40  → critical
    poor_max:      float = 55.0   # 40–55 → poor
    fair_max:      float = 70.0   # 55–70 → fair
    good_max:      float = 85.0   # 70–85 → good
    excellent_min: float = 85.0   # ≥ 85  → excellent

SCORE_BANDS = HealthScoreBands()


# ─────────────────────────────────────────────────────────────────────────────
#  Priority scoring weights (higher = more urgent to show)
# ─────────────────────────────────────────────────────────────────────────────
#  Weights are summed across triggered rules per category.
#  The category with the highest total weight gets PRIORITY = HIGH.

CATEGORY_WEIGHTS = {
    "sleep":      1.20,   # Sleep deprivation has outsized systemic effects
    "activity":   1.10,
    "nutrition":  1.00,
    "hydration":  0.95,
    "stress":     1.15,   # High weight: stress degrades all other metrics
    "heart_rate": 1.05,
}

# Priority thresholds (total weighted severity score per category)
PRIORITY_THRESHOLDS = {
    "critical": 3.0,
    "high":     2.0,
    "medium":   1.0,
    "low":      0.0,
}

# Maximum recommendations to return (to avoid overwhelming users)
MAX_RECOMMENDATIONS = 8
MAX_PER_CATEGORY    = 3
