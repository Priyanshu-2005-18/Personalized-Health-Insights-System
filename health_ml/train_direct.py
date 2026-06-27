"""
train_direct.py
===============
Simplified, self-contained training script that trains a GradientBoosting
regressor on the health dataset and saves a joblib pipeline compatible with
the FastAPI predictor.

Features: sleep_hours, steps, calories, water_intake_ml, stress_level, heart_rate_bpm
Target  : health_score (0–100)

Usage (from health_ml/):
    python train_direct.py
"""
import sys
import warnings
import numpy as np
import pandas as pd
from pathlib import Path

warnings.filterwarnings("ignore")

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE_DIR      = Path(__file__).parent
DATA_CSV      = BASE_DIR / "data" / "health_data.csv"
MODEL_DIR     = BASE_DIR / "models"
PIPELINE_OUT  = MODEL_DIR / "full_pipeline.joblib"

# ── Feature / target ──────────────────────────────────────────────────────────
FEATURES = [
    "sleep_hours",
    "steps",
    "calories",
    "water_intake_ml",
    "stress_level",
    "heart_rate_bpm",
]
TARGET = "health_score"


def main():
    # 1. Load data
    if not DATA_CSV.exists():
        print(f"ERROR: data file not found at {DATA_CSV}")
        sys.exit(1)

    df = pd.read_csv(DATA_CSV)
    print(f"Loaded {len(df)} rows from {DATA_CSV}")

    # Validate required columns
    missing = [c for c in FEATURES + [TARGET] if c not in df.columns]
    if missing:
        print(f"ERROR: missing columns: {missing}")
        print(f"Available columns: {list(df.columns)}")
        sys.exit(1)

    X = df[FEATURES].copy()
    y = df[TARGET].copy()

    # 2. Train/test split
    from sklearn.model_selection import train_test_split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42
    )
    print(f"Train: {len(X_train)} | Test: {len(X_test)}")

    # 3. Build pipeline:  Imputer → FeatureEngineer → Scaler → GBR
    from sklearn.pipeline import Pipeline
    from sklearn.impute import SimpleImputer
    from sklearn.preprocessing import StandardScaler
    from sklearn.ensemble import GradientBoostingRegressor

    # Import the project's own feature engineering transformer
    sys.path.insert(0, str(BASE_DIR))
    try:
        from feature_engineering import HealthFeatureEngineer
        fe = HealthFeatureEngineer()
        print("Using HealthFeatureEngineer from feature_engineering.py")
    except Exception as e:
        print(f"WARNING: Could not load HealthFeatureEngineer: {e}")
        print("Falling back to passthrough transformer")
        from sklearn.preprocessing import FunctionTransformer
        fe = FunctionTransformer()

    pipeline = Pipeline([
        ("imputer",  SimpleImputer(strategy="median")),
        ("features", fe),
        ("scaler",   StandardScaler()),
        ("model",    GradientBoostingRegressor(
            n_estimators=200,
            learning_rate=0.1,
            max_depth=5,
            random_state=42,
        )),
    ])

    # 4. Fit
    print("Fitting pipeline ...")
    pipeline.fit(X_train, y_train)

    # 5. Evaluate
    from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error
    y_pred = pipeline.predict(X_test).clip(0, 100)
    r2   = r2_score(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    mae  = mean_absolute_error(y_test, y_pred)
    print(f"\nTest-set metrics:")
    print(f"  R²   = {r2:.4f}")
    print(f"  RMSE = {rmse:.4f}")
    print(f"  MAE  = {mae:.4f}")

    # 6. Save
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    import joblib
    joblib.dump(pipeline, PIPELINE_OUT, compress=3)
    size_kb = PIPELINE_OUT.stat().st_size / 1024
    print(f"\nModel saved -> {PIPELINE_OUT}  ({size_kb:.1f} KB)")
    print("Training complete.")

    return pipeline


if __name__ == "__main__":
    main()
