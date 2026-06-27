"""
Train and serialize the health score prediction model.

Features used
-------------
sleep_hours       : average nightly sleep (hrs)
sleep_quality     : self-rated quality 1-10
steps_daily       : average daily steps
active_minutes    : weekly active minutes
resting_hr        : resting heart rate (bpm)
hrv               : heart-rate variability (ms)
stress_index      : 0-100 (higher = more stress)
water_intake      : daily water intake (litres)
bmi               : body-mass index

Target
------
health_score      : 0-100 composite wellbeing score
"""

import json
import os
import numpy as np
import joblib
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import cross_val_score, train_test_split
from sklearn.metrics import mean_absolute_error, r2_score

# ── Reproducibility ────────────────────────────────────────────────────────────
np.random.seed(42)
N = 2000

ARTIFACTS_DIR = os.path.join(os.path.dirname(__file__), "..", "artifacts")
os.makedirs(ARTIFACTS_DIR, exist_ok=True)

# ── Synthetic training data ────────────────────────────────────────────────────
def generate_dataset(n: int) -> tuple[np.ndarray, np.ndarray]:
    """
    Generate a synthetic but physiologically-plausible dataset.
    In production replace with real labelled data (e.g. from NHANES).
    """
    sleep_hours    = np.random.normal(7.0, 1.2, n).clip(3, 12)
    sleep_quality  = np.random.normal(6.5, 1.8, n).clip(1, 10)
    steps_daily    = np.random.normal(8500, 3000, n).clip(500, 25000)
    active_minutes = np.random.normal(150, 60, n).clip(0, 600)
    resting_hr     = np.random.normal(68, 10, n).clip(40, 110)
    hrv            = np.random.normal(55, 20, n).clip(10, 120)
    stress_index   = np.random.normal(40, 20, n).clip(0, 100)
    water_intake   = np.random.normal(2.0, 0.6, n).clip(0.3, 5.0)
    bmi            = np.random.normal(24, 4, n).clip(15, 45)

    # Composite score — weighted domain logic that mirrors what the ML model
    # learns to approximate from labelled data.
    sleep_score   = (sleep_hours / 9.0) * 25 + (sleep_quality / 10.0) * 15
    activity_score = (steps_daily / 15000) * 20 + (active_minutes / 300) * 10
    cardio_score  = ((110 - resting_hr) / 70) * 10 + (hrv / 100) * 10
    stress_score  = ((100 - stress_index) / 100) * 5
    lifestyle_score = (water_intake / 3.0) * 3 + np.where(
        (bmi >= 18.5) & (bmi < 25), 2, np.where((bmi >= 25) & (bmi < 30), 0, -3)
    )

    health_score = (
        sleep_score + activity_score + cardio_score + stress_score + lifestyle_score
        + np.random.normal(0, 2, n)          # measurement noise
    ).clip(0, 100)

    X = np.column_stack([
        sleep_hours, sleep_quality, steps_daily, active_minutes,
        resting_hr, hrv, stress_index, water_intake, bmi,
    ])
    return X, health_score


# ── Train ──────────────────────────────────────────────────────────────────────
def train() -> None:
    print("Generating synthetic dataset …")
    X, y = generate_dataset(N)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    pipeline = Pipeline([
        ("scaler", StandardScaler()),
        ("model", GradientBoostingRegressor(
            n_estimators=300,
            max_depth=4,
            learning_rate=0.05,
            subsample=0.8,
            random_state=42,
        )),
    ])

    print("Training model …")
    pipeline.fit(X_train, y_train)

    # ── Evaluate ───────────────────────────────────────────────────────────────
    y_pred  = pipeline.predict(X_test)
    mae     = mean_absolute_error(y_test, y_pred)
    r2      = r2_score(y_test, y_pred)
    cv_r2   = cross_val_score(pipeline, X, y, cv=5, scoring="r2").mean()

    metrics = {
        "mae":           round(float(mae), 4),
        "r2":            round(float(r2), 4),
        "cv_r2_mean":    round(float(cv_r2), 4),
        "train_samples": len(X_train),
        "test_samples":  len(X_test),
        "feature_names": [
            "sleep_hours", "sleep_quality", "steps_daily", "active_minutes",
            "resting_hr", "hrv", "stress_index", "water_intake", "bmi",
        ],
    }

    print(f"\nEvaluation results:")
    print(f"  MAE    : {mae:.4f}")
    print(f"  R²     : {r2:.4f}")
    print(f"  CV R²  : {cv_r2:.4f}")

    # ── Persist ────────────────────────────────────────────────────────────────
    model_path   = os.path.join(ARTIFACTS_DIR, "health_score_model.joblib")
    metrics_path = os.path.join(ARTIFACTS_DIR, "model_metrics.json")

    joblib.dump(pipeline, model_path, compress=3)
    with open(metrics_path, "w") as f:
        json.dump(metrics, f, indent=2)

    print(f"\nModel saved  → {model_path}")
    print(f"Metrics saved → {metrics_path}")


if __name__ == "__main__":
    train()
