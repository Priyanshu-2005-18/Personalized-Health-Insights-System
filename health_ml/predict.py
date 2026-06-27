"""
predict.py
==========
Load the saved pipeline and run inference on new health data.

Usage:
  python predict.py                        # demo with sample inputs
  python predict.py --file new_data.csv    # batch prediction from CSV
"""

import argparse
import sys
import numpy as np
import pandas as pd
import joblib

from config import FEATURES, PIPELINE_PATH


# ─────────────────────────────────────────────────────────────────────────────
#  Load
# ─────────────────────────────────────────────────────────────────────────────

def load_model():
    if not PIPELINE_PATH.exists():
        print(f"❌  No model found at {PIPELINE_PATH}. Run train.py first.")
        sys.exit(1)
    model = joblib.load(PIPELINE_PATH)
    print(f"✅  Model loaded from {PIPELINE_PATH}")
    return model


# ─────────────────────────────────────────────────────────────────────────────
#  Predict
# ─────────────────────────────────────────────────────────────────────────────

def predict(model, data: pd.DataFrame) -> np.ndarray:
    """
    Run the full pipeline (feature engineering + preprocessing + model)
    and return predicted health scores.
    """
    missing = [c for c in FEATURES if c not in data.columns]
    if missing:
        raise ValueError(f"Missing columns in input: {missing}")

    X = data[FEATURES]
    scores = model.predict(X).clip(0, 100).round(2)
    return scores


def score_to_grade(score: float) -> str:
    """Convert numeric score to letter grade + label."""
    if score >= 85:  return "A  — Excellent"
    if score >= 70:  return "B  — Good"
    if score >= 55:  return "C  — Average"
    if score >= 40:  return "D  — Below average"
    return            "F  — Poor"


def predict_single(model, **kwargs) -> dict:
    """
    Predict for a single person supplied as keyword arguments.

    Example:
      result = predict_single(
          model,
          sleep_hours=7.5, steps=9000, calories=2100,
          water_intake_ml=2500, stress_level=3, heart_rate_bpm=68
      )
    """
    row = {f: kwargs.get(f, np.nan) for f in FEATURES}
    df  = pd.DataFrame([row])
    score = predict(model, df)[0]
    return {
        "health_score": score,
        "grade":        score_to_grade(score),
        "inputs":       row,
    }


# ─────────────────────────────────────────────────────────────────────────────
#  Demo
# ─────────────────────────────────────────────────────────────────────────────

DEMO_PROFILES = [
    {
        "name":            "Alice (Healthy)",
        "sleep_hours":     8.0,
        "steps":           10_500,
        "calories":        2_050,
        "water_intake_ml": 2_800,
        "stress_level":    2,
        "heart_rate_bpm":  65,
    },
    {
        "name":            "Bob (Average)",
        "sleep_hours":     6.5,
        "steps":           6_200,
        "calories":        2_400,
        "water_intake_ml": 1_800,
        "stress_level":    5,
        "heart_rate_bpm":  74,
    },
    {
        "name":            "Carol (Unhealthy)",
        "sleep_hours":     4.5,
        "steps":           1_800,
        "calories":        3_200,
        "water_intake_ml": 800,
        "stress_level":    9,
        "heart_rate_bpm":  98,
    },
    {
        "name":            "Dave (Partial data)",
        "sleep_hours":     7.0,
        "steps":           np.nan,      # missing step count
        "calories":        1_900,
        "water_intake_ml": np.nan,      # missing water data
        "stress_level":    4,
        "heart_rate_bpm":  70,
    },
]


def run_demo(model) -> None:
    print("\n" + "═" * 60)
    print("  Demo Predictions — Sample Health Profiles")
    print("═" * 60)

    rows = []
    for profile in DEMO_PROFILES:
        name = profile.pop("name")
        result = predict_single(model, **profile)
        print(f"\n  👤  {name}")
        print(f"      Inputs:       {result['inputs']}")
        print(f"      Health Score: {result['health_score']} / 100")
        print(f"      Grade:        {result['grade']}")
        profile["name"] = name    # restore

    print("\n" + "═" * 60)


def run_batch(model, csv_path: str) -> None:
    df = pd.read_csv(csv_path)
    scores = predict(model, df)
    df["predicted_health_score"] = scores
    df["grade"] = [score_to_grade(s) for s in scores]

    out_path = csv_path.replace(".csv", "_predictions.csv")
    df.to_csv(out_path, index=False)
    print(f"\n✅  Batch predictions saved → {out_path}")
    print(df[["predicted_health_score", "grade"]].describe().round(2))


# ─────────────────────────────────────────────────────────────────────────────
#  CLI
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Health Score Predictor")
    parser.add_argument("--file", type=str, default=None,
                        help="Path to CSV for batch prediction")
    args = parser.parse_args()

    mdl = load_model()

    if args.file:
        run_batch(mdl, args.file)
    else:
        run_demo(mdl)
