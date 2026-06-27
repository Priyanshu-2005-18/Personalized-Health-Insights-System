"""
feature_engineering.py
======================
Step 2 — domain-specific feature engineering.

New features created:
  ┌──────────────────────────────┬───────────────────────────────────────────┐
  │ Feature                      │ Rationale                                 │
  ├──────────────────────────────┼───────────────────────────────────────────┤
  │ sleep_deviation              │ |sleep - 8|  (8 h is ideal midpoint)      │
  │ is_sleep_optimal             │ 1 if 7 ≤ sleep ≤ 9                        │
  │ steps_k                      │ steps / 1000 (scale reduction)            │
  │ steps_goal_pct               │ steps / 10 000 capped at 1.0              │
  │ calorie_deviation            │ |calories - 2000| / 200                   │
  │ is_calorie_optimal           │ 1 if 1 800 ≤ cal ≤ 2 200                  │
  │ water_glasses                │ water_ml / 250 (unit: glasses)            │
  │ is_hydrated                  │ 1 if water ≥ 2 500 ml                     │
  │ stress_inverse               │ (10 - stress) / 9   (0 = extreme stress)  │
  │ is_low_stress                │ 1 if stress ≤ 3                           │
  │ hr_deviation                 │ |hr - 70| / 10                            │
  │ is_hr_optimal                │ 1 if 60 ≤ hr ≤ 80                        │
  │ activity_recovery_index      │ steps_goal_pct × sleep_deviation⁻¹       │
  │ lifestyle_score              │ 0.3×steps_goal + 0.4×is_sleep + 0.3×hyd  │
  └──────────────────────────────┴───────────────────────────────────────────┘

Implementation uses a custom sklearn BaseEstimator + TransformerMixin
so it slots directly into a Pipeline and is serialisable by joblib.
"""

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin

from config import FEATURES


class HealthFeatureEngineer(BaseEstimator, TransformerMixin):
    """
    Stateless transformer — fit() does nothing (all features are rule-based).
    Compatible with sklearn Pipeline and cross-validation.

    Parameters
    ----------
    add_interaction : bool
        If True, also adds the activity_recovery_index and lifestyle_score
        interaction features. Default True.
    """

    def __init__(self, add_interaction: bool = True):
        self.add_interaction = add_interaction

    def fit(self, X, y=None):
        # Store feature names for get_feature_names_out()
        if isinstance(X, pd.DataFrame):
            self.feature_names_in_ = list(X.columns)
        return self

    def transform(self, X, y=None) -> pd.DataFrame:
        if isinstance(X, np.ndarray):
            df = pd.DataFrame(X, columns=FEATURES)
        else:
            df = X.copy()

        out = df.copy()

        # ── Sleep ─────────────────────────────────────────────────────────────
        out["sleep_deviation"]    = (df["sleep_hours"] - 8.0).abs()
        out["is_sleep_optimal"]   = df["sleep_hours"].between(7.0, 9.0).astype(float)

        # ── Steps ─────────────────────────────────────────────────────────────
        out["steps_k"]            = df["steps"] / 1_000
        out["steps_goal_pct"]     = (df["steps"] / 10_000).clip(0, 1.0)

        # ── Calories ──────────────────────────────────────────────────────────
        out["calorie_deviation"]  = ((df["calories"] - 2_000).abs() / 200)
        out["is_calorie_optimal"] = df["calories"].between(1_800, 2_200).astype(float)

        # ── Water ─────────────────────────────────────────────────────────────
        out["water_glasses"]      = df["water_intake_ml"] / 250
        out["is_hydrated"]        = (df["water_intake_ml"] >= 2_500).astype(float)

        # ── Stress ────────────────────────────────────────────────────────────
        out["stress_inverse"]     = (10 - df["stress_level"]) / 9
        out["is_low_stress"]      = (df["stress_level"] <= 3).astype(float)

        # ── Heart rate ────────────────────────────────────────────────────────
        out["hr_deviation"]       = ((df["heart_rate_bpm"] - 70).abs() / 10)
        out["is_hr_optimal"]      = df["heart_rate_bpm"].between(60, 80).astype(float)

        # ── Interaction features ───────────────────────────────────────────────
        if self.add_interaction:
            # Activity-recovery: high steps + good sleep → high index
            denom = out["sleep_deviation"] + 0.5   # avoid div/0
            out["activity_recovery_index"] = out["steps_goal_pct"] / denom

            # Composite lifestyle score (simple weighted sum of binary flags)
            out["lifestyle_score"] = (
                0.30 * out["steps_goal_pct"] +
                0.40 * out["is_sleep_optimal"] +
                0.30 * out["is_hydrated"]
            )

        return out

    def get_feature_names_out(self, input_features=None):
        base = list(FEATURES)
        engineered = [
            "sleep_deviation", "is_sleep_optimal",
            "steps_k", "steps_goal_pct",
            "calorie_deviation", "is_calorie_optimal",
            "water_glasses", "is_hydrated",
            "stress_inverse", "is_low_stress",
            "hr_deviation", "is_hr_optimal",
        ]
        if self.add_interaction:
            engineered += ["activity_recovery_index", "lifestyle_score"]
        return np.array(base + engineered)


# ─────────────────────────────────────────────────────────────────────────────
#  Quick sanity-check
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    from preprocessing import load_data, validate_data

    df = validate_data(load_data())
    X  = df[FEATURES]

    eng = HealthFeatureEngineer()
    X_eng = eng.fit_transform(X)

    print(f"Original features  : {X.shape[1]}")
    print(f"Engineered features: {X_eng.shape[1]}")
    print(f"\nNew columns added:\n{[c for c in X_eng.columns if c not in FEATURES]}")
    print(f"\nSample (first row):\n{X_eng.iloc[0].to_string()}")
    print("\n✅  Feature engineering sanity-check passed.")
