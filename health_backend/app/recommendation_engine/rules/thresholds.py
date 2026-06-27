from dataclasses import dataclass

VALID_RANGES = {
    "sleep_hours":     (0.0,  24.0),
    "steps":           (0,    100_000),
    "calories":        (0,    10_000),
    "water_intake_ml": (0,    10_000),
    "stress_level":    (1,    10),
    "heart_rate_bpm":  (30,   250),
    "health_score":    (0.0,  100.0),
}


@dataclass(frozen=True)
class SleepThresholds:
    critical_low:  float = 5.0
    poor_low:      float = 6.0
    optimal_low:   float = 7.0
    optimal_high:  float = 9.0
    excess_high:   float = 10.0
    score_min_h:   float = 3.0
    score_max_h:   float = 9.0
    optimal_target: float = 8.0

SLEEP = SleepThresholds()


@dataclass(frozen=True)
class StepThresholds:
    sedentary:      int = 2_500
    low_active:     int = 5_000
    somewhat_active: int = 7_500
    active:         int = 10_000
    highly_active:  int = 12_500

STEPS = StepThresholds()


@dataclass(frozen=True)
class CalorieThresholds:
    critically_low: int = 1_200
    low:            int = 1_500
    optimal_low:    int = 1_600
    optimal_high:   int = 2_400
    high:           int = 2_800
    very_high:      int = 3_500
    optimal_target: int = 2_000

CALORIES = CalorieThresholds()


@dataclass(frozen=True)
class HydrationThresholds:
    severely_low:   int = 1_000
    low:            int = 1_500
    below_target:   int = 2_000
    optimal_low:    int = 2_000
    optimal_target: int = 2_500
    optimal_high:   int = 3_000
    score_max_ml:   int = 3_000

HYDRATION = HydrationThresholds()


@dataclass(frozen=True)
class StressThresholds:
    low_max:        int = 3
    moderate_max:   int = 5
    high_max:       int = 7
    very_high_max:  int = 9
    extreme_min:    int = 10

STRESS = StressThresholds()


@dataclass(frozen=True)
class HeartRateThresholds:
    athlete_max:    int = 55
    excellent_max:  int = 65
    good_max:       int = 75
    normal_max:     int = 85
    above_normal:   int = 100
    elevated_min:   int = 100
    optimal_target: int = 62

HR = HeartRateThresholds()


@dataclass(frozen=True)
class HealthScoreBands:
    critical_max:  float = 40.0
    poor_max:      float = 55.0
    fair_max:      float = 70.0
    good_max:      float = 85.0
    excellent_min: float = 85.0

SCORE_BANDS = HealthScoreBands()


CATEGORY_WEIGHTS = {
    "sleep":      1.20,
    "activity":   1.10,
    "nutrition":  1.00,
    "hydration":  0.95,
    "stress":     1.15,
    "heart_rate": 1.05,
}

PRIORITY_THRESHOLDS = {
    "critical": 3.0,
    "high":     2.0,
    "medium":   1.0,
    "low":      0.0,
}

MAX_RECOMMENDATIONS = 8
MAX_PER_CATEGORY    = 3
