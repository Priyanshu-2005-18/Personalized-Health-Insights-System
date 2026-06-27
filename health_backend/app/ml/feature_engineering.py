import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin

FEATURES = [
    "sleep_hours",
    "steps",
    "calories",
    "water_intake_ml",
    "stress_level",
    "heart_rate_bpm",
]


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
