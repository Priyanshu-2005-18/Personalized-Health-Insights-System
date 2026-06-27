"""
Feature engineering: converts raw ORM objects into a flat dict
suitable for Scikit-learn model input.
"""
from typing import Any, Dict, List, Optional
import numpy as np


def extract_sleep_features(sleep_logs: list) -> Dict[str, float]:
    """Aggregate sleep metrics over last N records."""
    if not sleep_logs:
        return {
            "avg_sleep_duration_min": 0.0,
            "avg_sleep_quality": 0.0,
            "avg_interruptions": 0.0,
            "sleep_consistency": 0.0,
        }

    durations  = [s.duration_min or 0 for s in sleep_logs]
    qualities  = [s.quality_score or 0 for s in sleep_logs]
    interrupts = [s.interruptions or 0 for s in sleep_logs]

    return {
        "avg_sleep_duration_min": float(np.mean(durations)),
        "avg_sleep_quality":      float(np.mean(qualities)),
        "avg_interruptions":      float(np.mean(interrupts)),
        "sleep_consistency":      float(1.0 - (np.std(durations) / (np.mean(durations) + 1e-9))),
    }


def extract_activity_features(activity_logs: list) -> Dict[str, float]:
    """Aggregate activity metrics over last N records."""
    if not activity_logs:
        return {
            "avg_activity_duration_min": 0.0,
            "avg_calories_burned":       0.0,
            "avg_steps":                 0.0,
            "activity_frequency":        0.0,
            "avg_intensity":             0.0,
        }

    durations = [a.duration_min    or 0 for a in activity_logs]
    calories  = [a.calories_burned or 0 for a in activity_logs]
    steps     = [a.steps           or 0 for a in activity_logs]
    intensity = [a.intensity       or 0 for a in activity_logs]

    return {
        "avg_activity_duration_min": float(np.mean(durations)),
        "avg_calories_burned":       float(np.mean(calories)),
        "avg_steps":                 float(np.mean(steps)),
        "activity_frequency":        float(len(activity_logs)),
        "avg_intensity":             float(np.mean(intensity)),
    }


def extract_nutrition_features(nutrition_logs: list) -> Dict[str, float]:
    """Aggregate nutrition metrics over last N records."""
    if not nutrition_logs:
        return {
            "avg_daily_calories":  0.0,
            "avg_protein_g":       0.0,
            "avg_carbs_g":         0.0,
            "avg_fat_g":           0.0,
            "avg_fiber_g":         0.0,
        }

    calories = [n.total_calories  or 0 for n in nutrition_logs]
    protein  = [n.total_protein_g or 0 for n in nutrition_logs]
    carbs    = [n.total_carbs_g   or 0 for n in nutrition_logs]
    fat      = [n.total_fat_g     or 0 for n in nutrition_logs]
    fiber    = [n.total_fiber_g   or 0 for n in nutrition_logs]

    return {
        "avg_daily_calories": float(np.mean(calories)),
        "avg_protein_g":      float(np.mean(protein)),
        "avg_carbs_g":        float(np.mean(carbs)),
        "avg_fat_g":          float(np.mean(fat)),
        "avg_fiber_g":        float(np.mean(fiber)),
    }


def extract_health_log_features(health_logs: list) -> Dict[str, float]:
    """Aggregate subjective scores from daily logs."""
    if not health_logs:
        return {
            "avg_mood_score":    0.0,
            "avg_stress_level":  0.0,
            "avg_energy_level":  0.0,
            "avg_water_ml":      0.0,
        }

    mood   = [h.mood_score    or 0 for h in health_logs]
    stress = [h.stress_level  or 0 for h in health_logs]
    energy = [h.energy_level  or 0 for h in health_logs]
    water  = [h.water_ml      or 0 for h in health_logs]

    return {
        "avg_mood_score":   float(np.mean(mood)),
        "avg_stress_level": float(np.mean(stress)),
        "avg_energy_level": float(np.mean(energy)),
        "avg_water_ml":     float(np.mean(water)),
    }


def extract_profile_features(profile) -> Dict[str, float]:
    """Extract numeric features from user profile."""
    if not profile:
        return {"age": 0.0, "bmi": 0.0, "activity_level_code": 0.0}

    from datetime import date
    age = 0.0
    if profile.date_of_birth:
        today = date.today()
        age = float(
            (today - profile.date_of_birth).days / 365.25
        )

    bmi = 0.0
    if profile.height_cm and profile.weight_kg and profile.height_cm > 0:
        bmi = float(profile.weight_kg / ((profile.height_cm / 100) ** 2))

    activity_map = {
        "sedentary": 1, "lightly_active": 2, "moderately_active": 3,
        "very_active": 4, "extra_active": 5,
    }
    activity_code = activity_map.get(
        profile.activity_level.value if profile.activity_level else "", 0
    )

    return {
        "age":                  age,
        "bmi":                  bmi,
        "activity_level_code":  float(activity_code),
    }


def build_feature_vector(
    profile,
    health_logs: list,
    sleep_logs: list,
    activity_logs: list,
    nutrition_logs: list,
) -> Dict[str, float]:
    """Merge all feature groups into a single flat dict."""
    features: Dict[str, float] = {}
    features.update(extract_profile_features(profile))
    features.update(extract_health_log_features(health_logs))
    features.update(extract_sleep_features(sleep_logs))
    features.update(extract_activity_features(activity_logs))
    features.update(extract_nutrition_features(nutrition_logs))
    return features


FEATURE_COLUMNS = [
    # profile
    "age", "bmi", "activity_level_code",
    # health log
    "avg_mood_score", "avg_stress_level", "avg_energy_level", "avg_water_ml",
    # sleep
    "avg_sleep_duration_min", "avg_sleep_quality", "avg_interruptions", "sleep_consistency",
    # activity
    "avg_activity_duration_min", "avg_calories_burned", "avg_steps",
    "activity_frequency", "avg_intensity",
    # nutrition
    "avg_daily_calories", "avg_protein_g", "avg_carbs_g", "avg_fat_g", "avg_fiber_g",
]
