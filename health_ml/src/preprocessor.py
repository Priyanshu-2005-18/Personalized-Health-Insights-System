"""
preprocessor.py
===============
Step 1: Data Preprocessing

Handles:
  - Schema validation (expected columns + types)
  - Missing value imputation (median strategy for robustness)
  - Outlier detection and capping using IQR method
  - Duplicate row removal
  - Feature scaling via RobustScaler (handles outliers better than StandardScaler)
  - Train/validation/test stratified split

Design choice — RobustScaler over StandardScaler:
  Health data often contains outliers (e.g. a user who logged 25,000 steps once).
  RobustScaler uses median and IQR instead of mean and std, making it
  resistant to those extreme values without removing data points.
"""

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import RobustScaler
from sklearn.impute import SimpleImputer
from typing import Tuple
import warnings
warnings.filterwarnings("ignore")


FEATURE_COLS = [
    "sleep_hours",
    "steps",
    "calories",
    "water_intake_ml",
    "stress_level",
    "heart_rate_bpm",
]
TARGET_COL = "health_score"

# Valid range bounds for each feature (domain knowledge)
VALID_RANGES = {
    "sleep_hours":     (0.0, 24.0),
    "steps":           (0, 100_000),
    "calories":        (0, 10_000),
    "water_intake_ml": (0, 10_000),
    "stress_level":    (1, 10),
    "heart_rate_bpm":  (30, 250),
    "health_score":    (0, 100),
}


def load_and_validate(path: str) -> pd.DataFrame:
    """Load CSV and validate schema."""
    df = pd.read_csv(path)
    print(f"\n📂 Loaded: {df.shape[0]:,} rows × {df.shape[1]} columns")

    # Check all required columns present
    required = FEATURE_COLS + [TARGET_COL]
    missing_cols = [c for c in required if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing columns: {missing_cols}")

    return df[required].copy()


def report_missing(df: pd.DataFrame) -> None:
    """Print missing value summary."""
    miss = df.isnull().sum()
    miss_pct = (miss / len(df) * 100).round(2)
    report = pd.DataFrame({"missing": miss, "pct": miss_pct})
    report = report[report["missing"] > 0]
    if report.empty:
        print("✅ No missing values found")
    else:
        print("\n⚠️  Missing values detected:")
        print(report.to_string())


def cap_outliers_iqr(df: pd.DataFrame, cols: list, factor: float = 1.5) -> pd.DataFrame:
    """
    Cap outliers at [Q1 - factor*IQR, Q3 + factor*IQR].
    Capping (Winsorization) preferred over removal to preserve dataset size.
    """
    df = df.copy()
    for col in cols:
        Q1 = df[col].quantile(0.25)
        Q3 = df[col].quantile(0.75)
        IQR = Q3 - Q1
        lo = Q1 - factor * IQR
        hi = Q3 + factor * IQR
        n_outliers = ((df[col] < lo) | (df[col] > hi)).sum()
        if n_outliers > 0:
            print(f"  📌 {col}: {n_outliers} outliers capped to [{lo:.2f}, {hi:.2f}]")
        df[col] = df[col].clip(lo, hi)
    return df


def enforce_domain_bounds(df: pd.DataFrame) -> pd.DataFrame:
    """Hard-clip all values to physiologically valid ranges."""
    df = df.copy()
    for col, (lo, hi) in VALID_RANGES.items():
        if col in df.columns:
            df[col] = df[col].clip(lo, hi)
    return df


def preprocess(
    path: str,
    test_size: float = 0.15,
    val_size: float = 0.15,
    random_state: int = 42,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray,
           np.ndarray, np.ndarray, np.ndarray,
           RobustScaler]:
    """
    Full preprocessing pipeline.

    Returns
    -------
    X_train, X_val, X_test : np.ndarray  (scaled)
    y_train, y_val, y_test : np.ndarray
    scaler                  : fitted RobustScaler (save with joblib)
    """
    # 1. Load & validate
    df = load_and_validate(path)
    print(f"\n{'='*50}")
    print("STEP 1 — DATA VALIDATION")
    print(f"{'='*50}")
    print(f"Shape     : {df.shape}")
    print(f"Dtypes    :\n{df.dtypes.to_string()}")
    report_missing(df)

    # 2. Remove exact duplicates
    n_before = len(df)
    df = df.drop_duplicates()
    print(f"\n🗑️  Removed {n_before - len(df)} duplicate rows → {len(df):,} rows remain")

    # 3. Impute missing values (median — robust to skew)
    print(f"\n{'='*50}")
    print("STEP 2 — MISSING VALUE IMPUTATION  (median strategy)")
    print(f"{'='*50}")
    imputer = SimpleImputer(strategy="median")
    df[FEATURE_COLS + [TARGET_COL]] = imputer.fit_transform(
        df[FEATURE_COLS + [TARGET_COL]]
    )
    print("✅ Imputation complete")

    # 4. Domain bounds enforcement
    df = enforce_domain_bounds(df)

    # 5. Outlier capping (IQR method)
    print(f"\n{'='*50}")
    print("STEP 3 — OUTLIER CAPPING  (IQR × 1.5)")
    print(f"{'='*50}")
    df = cap_outliers_iqr(df, FEATURE_COLS)

    # 6. Descriptive stats after cleaning
    print(f"\n{'='*50}")
    print("CLEANED DATA SUMMARY")
    print(f"{'='*50}")
    print(df[FEATURE_COLS + [TARGET_COL]].describe().round(2).to_string())

    # 7. Split features / target
    X = df[FEATURE_COLS].values
    y = df[TARGET_COL].values

    # 8. Train / val / test split
    # First split out test, then split remainder into train + val
    X_trainval, X_test, y_trainval, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state
    )
    val_frac = val_size / (1 - test_size)
    X_train, X_val, y_train, y_val = train_test_split(
        X_trainval, y_trainval, test_size=val_frac, random_state=random_state
    )
    print(f"\n{'='*50}")
    print("STEP 4 — TRAIN / VAL / TEST SPLIT")
    print(f"{'='*50}")
    print(f"  Train   : {X_train.shape[0]:>5} samples ({(1-test_size-val_size)*100:.0f}%)")
    print(f"  Val     : {X_val.shape[0]:>5} samples ({val_size*100:.0f}%)")
    print(f"  Test    : {X_test.shape[0]:>5} samples ({test_size*100:.0f}%)")

    # 9. Feature scaling with RobustScaler
    print(f"\n{'='*50}")
    print("STEP 5 — FEATURE SCALING  (RobustScaler)")
    print(f"{'='*50}")
    scaler = RobustScaler()
    X_train = scaler.fit_transform(X_train)   # fit ONLY on train
    X_val   = scaler.transform(X_val)         # transform val/test with train stats
    X_test  = scaler.transform(X_test)
    print("✅ Scaling complete")
    print(f"   Center (median) : {scaler.center_.round(2)}")
    print(f"   Scale  (IQR)    : {scaler.scale_.round(2)}")

    return X_train, X_val, X_test, y_train, y_val, y_test, scaler


if __name__ == "__main__":
    from src.generate_data import generate_health_dataset
    import os

    os.makedirs("data", exist_ok=True)
    df = generate_health_dataset()
    df.to_csv("data/health_data.csv", index=False)

    X_train, X_val, X_test, y_train, y_val, y_test, scaler = preprocess(
        "data/health_data.csv"
    )
    print(f"\n✅ Preprocessing complete. Ready for model training.")
