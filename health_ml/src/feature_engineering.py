"""
feature_engineering.py
======================
Step 2: Feature Engineering

Transforms the 6 raw features into 26 total features (6 original + 20 engineered):

Category A — Domain-derived sub-scores (0–100 scale)
  Converts each raw metric into a normalised score reflecting health impact.
  E.g. 10k steps → 100, 5k steps → 50.

Category B — Interaction features
  Captures synergistic effects that single features miss.
  E.g. high steps + low stress = compounded positive effect.

Category C — Ratio features
  Relative relationships between metrics (calories per step, water per calorie).

Category D — Polynomial features
  Captures non-linear relationships (sleep deprivation has a non-linear impact).

Category E — Binned features
  Discretises continuous variables into ordinal health categories.

Why custom engineering over PolynomialFeatures(degree=2) alone?
  PolynomialFeatures on 6 raw features produces 27 features including many
  physically meaningless ones (e.g. stress²). Domain-derived features are
  more interpretable and often outperform blind polynomial expansion on
  small-to-medium health datasets.
"""

import numpy as np
import pandas as pd
from typing import Tuple, List


FEATURE_COLS = [
    "sleep_hours",
    "steps",
    "calories",
    "water_intake_ml",
    "stress_level",
    "heart_rate_bpm",
]


# ─────────────────────────────────────────────────────────────────────────────
#  A — Domain-derived sub-scores
# ─────────────────────────────────────────────────────────────────────────────

def compute_sub_scores(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalise each feature to a 0–100 health sub-score using
    evidence-based optimal ranges from health literature.
    """
    df = df.copy()

    # Sleep: optimal 7–9h, penalty outside
    df["sleep_score"] = np.clip(
        100 - np.abs(df["sleep_hours"] - 8.0) * 15, 0, 100
    )

    # Steps: 10 000 steps/day = 100, proportional below
    df["step_score"] = np.clip(df["steps"] / 10_000 * 100, 0, 100)

    # Calories: optimal ~2000 kcal, symmetric penalty
    df["calorie_score"] = np.clip(
        100 - np.abs(df["calories"] - 2000) / 20, 0, 100
    )

    # Water: 3 000 ml/day = 100
    df["water_score"] = np.clip(df["water_intake_ml"] / 3000 * 100, 0, 100)

    # Stress: lower is better (1 = 100, 10 = 0)
    df["stress_score"] = (10 - df["stress_level"]) / 9 * 100

    # Heart rate: optimal resting 55–70 bpm, penalty outside
    df["hr_score"] = np.clip(
        100 - np.abs(df["heart_rate_bpm"] - 62) * 1.8, 0, 100
    )

    return df


# ─────────────────────────────────────────────────────────────────────────────
#  B — Interaction features
# ─────────────────────────────────────────────────────────────────────────────

def compute_interactions(df: pd.DataFrame) -> pd.DataFrame:
    """
    Capture joint effects between features that individual features miss.
    All interactions are normalised to prevent scale dominance.
    """
    df = df.copy()

    # Active + rested = better recovery (step × sleep synergy)
    df["active_sleep_score"] = (df["step_score"] * df["sleep_score"]) / 100

    # Low stress + adequate sleep = mental recovery bonus
    df["recovery_score"] = (df["stress_score"] * df["sleep_score"]) / 100

    # Hydration efficiency: water per 1000 calories (optimal ~1.2 L/1000 kcal)
    df["hydration_ratio"] = np.clip(
        df["water_intake_ml"] / (df["calories"].clip(1) / 1000), 0, 5000
    )

    # Cardiovascular fitness index: low HR + high steps
    df["cardio_index"] = (df["hr_score"] * df["step_score"]) / 100

    # Overall lifestyle score: average of all sub-scores
    sub_score_cols = [
        "sleep_score", "step_score", "calorie_score",
        "water_score", "stress_score", "hr_score",
    ]
    df["lifestyle_score"] = df[sub_score_cols].mean(axis=1)

    return df


# ─────────────────────────────────────────────────────────────────────────────
#  C — Ratio features
# ─────────────────────────────────────────────────────────────────────────────

def compute_ratios(df: pd.DataFrame) -> pd.DataFrame:
    """Capture relative relationships between raw metrics."""
    df = df.copy()

    # Calories burned per 1000 steps (proxy for metabolic efficiency)
    df["cal_per_1k_steps"] = np.clip(
        df["calories"] / (df["steps"].clip(1) / 1000), 0, 2000
    )

    # Sleep per stress unit (sleep quality index)
    df["sleep_per_stress"] = df["sleep_hours"] / df["stress_level"].clip(1)

    # Water per calorie (hydration density)
    df["water_per_cal"] = (
        df["water_intake_ml"] / df["calories"].clip(1)
    ).clip(0, 5)

    return df


# ─────────────────────────────────────────────────────────────────────────────
#  D — Polynomial features (selective)
# ─────────────────────────────────────────────────────────────────────────────

def compute_polynomial(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add squared terms for features known to have non-linear health impacts.
    Sleep deprivation and extreme stress both have accelerating negative effects.
    """
    df = df.copy()
    df["sleep_hours_sq"]  = df["sleep_hours"] ** 2
    df["stress_level_sq"] = df["stress_level"] ** 2
    df["steps_log"]       = np.log1p(df["steps"])   # log-transform right-skewed steps
    return df


# ─────────────────────────────────────────────────────────────────────────────
#  E — Binned features
# ─────────────────────────────────────────────────────────────────────────────

def compute_bins(df: pd.DataFrame) -> pd.DataFrame:
    """
    Discretise continuous variables into ordinal health categories.
    Helps tree-based models find split points more easily.
    """
    df = df.copy()

    df["sleep_category"] = pd.cut(
        df["sleep_hours"],
        bins=[0, 5, 6, 7, 9, 24],
        labels=[0, 1, 2, 3, 2],   # poor/short/ok/optimal/ok (inverted U)
        ordered=False,
    ).astype(float)

    df["activity_category"] = pd.cut(
        df["steps"],
        bins=[0, 2500, 5000, 7500, 10000, 100_000],
        labels=[0, 1, 2, 3, 4],   # sedentary/low/moderate/active/very active
        ordered=True,
    ).astype(float)

    df["stress_category"] = pd.cut(
        df["stress_level"],
        bins=[0, 3, 6, 10],
        labels=[0, 1, 2],          # low/medium/high
        ordered=True,
    ).astype(float)

    return df


# ─────────────────────────────────────────────────────────────────────────────
#  Main pipeline
# ─────────────────────────────────────────────────────────────────────────────

def engineer_features(df: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]]:
    """
    Apply all feature engineering steps in sequence.

    Parameters
    ----------
    df : DataFrame with raw FEATURE_COLS

    Returns
    -------
    df_eng      : DataFrame with original + engineered features
    feature_cols: list of all feature column names to use in training
    """
    df_eng = df.copy()
    df_eng = compute_sub_scores(df_eng)
    df_eng = compute_interactions(df_eng)
    df_eng = compute_ratios(df_eng)
    df_eng = compute_polynomial(df_eng)
    df_eng = compute_bins(df_eng)

    # Collect all feature columns (original + engineered)
    feature_cols = [
        # Original
        "sleep_hours", "steps", "calories", "water_intake_ml",
        "stress_level", "heart_rate_bpm",
        # Sub-scores
        "sleep_score", "step_score", "calorie_score",
        "water_score", "stress_score", "hr_score",
        # Interactions
        "active_sleep_score", "recovery_score", "hydration_ratio",
        "cardio_index", "lifestyle_score",
        # Ratios
        "cal_per_1k_steps", "sleep_per_stress", "water_per_cal",
        # Polynomial
        "sleep_hours_sq", "stress_level_sq", "steps_log",
        # Bins
        "sleep_category", "activity_category", "stress_category",
    ]

    # Drop any NaN introduced by bins or ratios
    df_eng[feature_cols] = df_eng[feature_cols].fillna(df_eng[feature_cols].median())

    return df_eng, feature_cols


def print_feature_summary(feature_cols: List[str]) -> None:
    # Fixed: use explicit lists instead of endswith("_score") which incorrectly
    # catches interaction features (active_sleep_score, recovery_score, lifestyle_score)
    categories = {
        "Original (6)":     ["sleep_hours","steps","calories","water_intake_ml","stress_level","heart_rate_bpm"],
        "Sub-scores (6)":   ["sleep_score","step_score","calorie_score","water_score","stress_score","hr_score"],
        "Interactions (5)": ["active_sleep_score","recovery_score","hydration_ratio","cardio_index","lifestyle_score"],
        "Ratios (3)":       ["cal_per_1k_steps","sleep_per_stress","water_per_cal"],
        "Polynomial (3)":   ["sleep_hours_sq","stress_level_sq","steps_log"],
        "Binned (3)":       ["sleep_category","activity_category","stress_category"],
    }
    print(f"\n{'='*50}")
    print(f"FEATURE ENGINEERING SUMMARY — {len(feature_cols)} total features")
    print(f"{'='*50}")
    for cat, cols in categories.items():
        print(f"\n  {cat}:")
        for c in cols:
            print(f"    • {c}")


if __name__ == "__main__":
    from src.generate_data import generate_health_dataset

    df_raw = generate_health_dataset(500)
    df_eng, feature_cols = engineer_features(df_raw)
    print_feature_summary(feature_cols)
    print(f"\nShape before: {df_raw.shape}")
    print(f"Shape after:  {df_eng[feature_cols].shape}")
    print(f"\nSample (first row):\n{df_eng[feature_cols].iloc[0].round(3).to_string()}")
