"""
predictor.py
============
Step 6 (inference): Load saved model artifacts and predict health scores.

Provides:
  HealthScorePredictor  — class wrapping model + scaler + feature engineering
  predict_single()      — predict for one user's input dict
  predict_batch()       — predict for a DataFrame of users
  explain_prediction()  — per-user feedback based on raw metric values
"""

import numpy as np
import pandas as pd
import joblib
from pathlib import Path
from typing import List, Union

from src.feature_engineering import engineer_features

MODELS_DIR = Path("models")


class HealthScorePredictor:
    """
    Load persisted model artifacts and provide a clean prediction interface.

    Usage
    -----
    predictor = HealthScorePredictor()
    score = predictor.predict_single({
        "sleep_hours": 7.0,
        "steps": 8000,
        "calories": 2100,
        "water_intake_ml": 2500,
        "stress_level": 4,
        "heart_rate_bpm": 68,
    })
    """

    RAW_COLS = [
        "sleep_hours", "steps", "calories",
        "water_intake_ml", "stress_level", "heart_rate_bpm",
    ]

    def __init__(self, models_dir: Union[str, Path] = MODELS_DIR) -> None:
        models_dir = Path(models_dir)
        self.model        = joblib.load(models_dir / "best_model.joblib")
        self.scaler       = joblib.load(models_dir / "scaler.joblib")
        self.feature_cols = joblib.load(models_dir / "feature_cols.joblib")
        self.imputer      = joblib.load(models_dir / "imputer.joblib")
        self.metadata     = joblib.load(models_dir / "model_metadata.joblib")
        print(f"✅ Model loaded: {self.metadata['model_name']}")
        print(f"   Test R² = {self.metadata['test_metrics']['R²']}")
        print(f"   Test MAE = {self.metadata['test_metrics']['MAE']} pts")

    def _prepare(self, df: pd.DataFrame) -> np.ndarray:
        """Apply feature engineering → impute → scale."""
        df_eng, _ = engineer_features(df)
        X = df_eng[self.feature_cols].values
        X = self.imputer.transform(X)
        X = self.scaler.transform(X)
        return X

    def predict_single(self, inputs: dict) -> dict:
        """
        Predict health score for a single user.

        Parameters
        ----------
        inputs : dict with keys matching RAW_COLS

        Returns
        -------
        dict with predicted_score, category, and per-metric feedback
        """
        df = pd.DataFrame([inputs])
        for col in self.RAW_COLS:
            if col not in df.columns:
                df[col] = np.nan

        X = self._prepare(df)
        score = float(np.clip(self.model.predict(X)[0], 0, 100))
        category = self._score_to_category(score)
        feedback = explain_prediction(inputs)

        return {
            "predicted_score": round(score, 2),
            "category":        category,
            "feedback":        feedback,
        }

    def predict_batch(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Predict health scores for a DataFrame of users.
        Returns original DataFrame with 'predicted_score' and 'category' columns added.
        """
        X = self._prepare(df)
        scores = np.clip(self.model.predict(X), 0, 100)
        result = df.copy()
        result["predicted_score"] = scores.round(2)
        result["category"] = [self._score_to_category(s) for s in scores]
        return result

    @staticmethod
    def _score_to_category(score: float) -> str:
        if score >= 85:   return "Excellent 🟢"
        if score >= 70:   return "Good 🟡"
        if score >= 55:   return "Fair 🟠"
        if score >= 40:   return "Poor 🔴"
        return "Critical 🆘"


def explain_prediction(inputs: dict) -> List[str]:
    """
    Generate human-readable feedback for each metric
    based on domain health guidelines.
    """
    feedback = []

    sleep = inputs.get("sleep_hours")
    if sleep is not None:
        if sleep < 6:
            feedback.append(f"😴 Sleep ({sleep}h): Below recommended. Target 7–9 hours.")
        elif sleep > 9:
            feedback.append(f"😴 Sleep ({sleep}h): Slightly above average. May indicate fatigue.")
        else:
            feedback.append(f"✅ Sleep ({sleep}h): Within optimal range (7–9h).")

    steps = inputs.get("steps")
    if steps is not None:
        if steps < 5000:
            feedback.append(f"🚶 Steps ({steps:,}): Low. Aim for 7,500–10,000 steps/day.")
        elif steps < 7500:
            feedback.append(f"🚶 Steps ({steps:,}): Moderate. Push toward 10,000 for better outcomes.")
        else:
            feedback.append(f"✅ Steps ({steps:,}): Great daily activity level.")

    calories = inputs.get("calories")
    if calories is not None:
        if calories < 1500:
            feedback.append(f"🍽️  Calories ({calories}): Too low. Risk of nutrient deficiency.")
        elif calories > 2500:
            feedback.append(f"🍽️  Calories ({calories}): Above average. Monitor portion sizes.")
        else:
            feedback.append(f"✅ Calories ({calories}): Within healthy range (1500–2500).")

    water = inputs.get("water_intake_ml")
    if water is not None:
        if water < 1500:
            feedback.append(f"💧 Water ({water}ml): Dehydrated. Target ≥ 2000–3000 ml/day.")
        elif water < 2000:
            feedback.append(f"💧 Water ({water}ml): Slightly low. Increase intake.")
        else:
            feedback.append(f"✅ Water ({water}ml): Good hydration level.")

    stress = inputs.get("stress_level")
    if stress is not None:
        if stress >= 7:
            feedback.append(f"😰 Stress ({stress}/10): High. Consider mindfulness or rest.")
        elif stress >= 4:
            feedback.append(f"😐 Stress ({stress}/10): Moderate. Monitor and manage.")
        else:
            feedback.append(f"✅ Stress ({stress}/10): Well managed.")

    hr = inputs.get("heart_rate_bpm")
    if hr is not None:
        if hr < 50:
            feedback.append(f"❤️  HR ({hr} bpm): Very low (possible athlete, or monitor if symptomatic).")
        elif hr > 100:
            feedback.append(f"❤️  HR ({hr} bpm): Elevated. Consult a healthcare provider.")
        elif hr <= 70:
            feedback.append(f"✅ HR ({hr} bpm): Excellent resting rate (50–70 bpm).")
        else:
            feedback.append(f"✅ HR ({hr} bpm): Normal resting rate (71–100 bpm).")

    return feedback


if __name__ == "__main__":
    predictor = HealthScorePredictor()

    # ── Single prediction ─────────────────────────────────────────────────────
    print("\n" + "="*50)
    print("SINGLE USER PREDICTION")
    print("="*50)
    result = predictor.predict_single({
        "sleep_hours":     7.5,
        "steps":           9000,
        "calories":        2100,
        "water_intake_ml": 2500,
        "stress_level":    3,
        "heart_rate_bpm":  65,
    })
    print(f"\nPredicted Health Score : {result['predicted_score']}")
    print(f"Category               : {result['category']}")
    print("\nFeedback:")
    for line in result["feedback"]:
        print(f"  {line}")

    # ── Batch prediction ──────────────────────────────────────────────────────
    print("\n" + "="*50)
    print("BATCH PREDICTIONS — 4 USERS")
    print("="*50)
    batch = pd.DataFrame([
        {"sleep_hours": 8.0, "steps": 10000, "calories": 1900, "water_intake_ml": 3000, "stress_level": 2, "heart_rate_bpm": 62},
        {"sleep_hours": 5.0, "steps": 2000,  "calories": 2800, "water_intake_ml": 900,  "stress_level": 9, "heart_rate_bpm": 95},
        {"sleep_hours": 7.0, "steps": 7500,  "calories": 2100, "water_intake_ml": 2200, "stress_level": 4, "heart_rate_bpm": 70},
        {"sleep_hours": 4.5, "steps": 1500,  "calories": 3200, "water_intake_ml": 700,  "stress_level": 10,"heart_rate_bpm":105},
    ])
    results = predictor.predict_batch(batch)
    print(results[["sleep_hours","steps","stress_level","predicted_score","category"]].to_string(index=False))
