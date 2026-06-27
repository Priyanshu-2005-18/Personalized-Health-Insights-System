"""
preprocessing.py
================
Step 1 of the ML pipeline — data loading and cleaning.

Responsibilities:
  load_data()          → read CSV, basic dtype casting
  validate_data()      → range checks, warn on outliers
  build_preprocessor() → returns a fitted ColumnTransformer
                         (imputation + scaling, ready to embed in Pipeline)

Design:
  • Uses sklearn Pipeline / ColumnTransformer so the exact same
    transformations are applied identically at train and inference time.
  • Imputer strategy: median (robust to outliers vs mean).
  • Scaler: StandardScaler — zero-mean, unit-variance.
    (RobustScaler is also available for heavily skewed distributions.)
"""

import warnings
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from config import FEATURES, OPTIMAL_RANGES, RAW_CSV


# ─────────────────────────────────────────────────────────────────────────────
#  1. Load
# ─────────────────────────────────────────────────────────────────────────────

def load_data(path=RAW_CSV) -> pd.DataFrame:
    """
    Read the CSV and cast every feature to float64.
    Returns a DataFrame with the original column order intact.
    """
    df = pd.read_csv(path)
    for col in FEATURES:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    print(f"[load]  {len(df):,} rows × {len(df.columns)} cols loaded from {path.name}")
    return df


# ─────────────────────────────────────────────────────────────────────────────
#  2. Validate
# ─────────────────────────────────────────────────────────────────────────────

HARD_LIMITS = {
    "sleep_hours":     (0.0,    24.0),
    "steps":           (0,      100_000),
    "calories":        (0,      10_000),
    "water_intake_ml": (0,      10_000),
    "stress_level":    (1,      10),
    "heart_rate_bpm":  (30,     250),
}


def validate_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clip values that violate hard physiological limits and warn the user.
    Returns a cleaned copy.
    """
    df = df.copy()
    for col, (lo, hi) in HARD_LIMITS.items():
        if col not in df.columns:
            continue
        n_below = (df[col] < lo).sum()
        n_above = (df[col] > hi).sum()
        if n_below + n_above > 0:
            warnings.warn(
                f"[validate] {col}: {n_below} values below {lo}, "
                f"{n_above} above {hi} — clipping to [{lo}, {hi}]"
            )
        df[col] = df[col].clip(lo, hi)

    # Report missing values
    missing = df[FEATURES].isnull().sum()
    if missing.any():
        print("[validate] Missing values found:")
        print(missing[missing > 0].to_string())

    return df


# ─────────────────────────────────────────────────────────────────────────────
#  3. Preprocessor (imputation + scaling)
# ─────────────────────────────────────────────────────────────────────────────

def build_preprocessor() -> ColumnTransformer:
    """
    Returns an un-fitted ColumnTransformer that:
      1. Imputes missing values with the column median
      2. Standard-scales all numeric features

    Embedding this in a sklearn Pipeline guarantees that the imputer
    and scaler are fit only on training data (no data leakage).
    """
    numeric_transformer = Pipeline(steps=[
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler",  StandardScaler()),
    ])

    preprocessor = ColumnTransformer(
        transformers=[
            ("num", numeric_transformer, FEATURES),
        ],
        remainder="drop",     # drop any extra columns not in FEATURES
        verbose_feature_names_out=False,
    )
    return preprocessor


# ─────────────────────────────────────────────────────────────────────────────
#  Quick sanity-check
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    df = load_data()
    df = validate_data(df)
    pre = build_preprocessor()

    from sklearn.model_selection import train_test_split
    from config import TARGET, TEST_SIZE, RANDOM_STATE

    X = df[FEATURES]
    y = df[TARGET]
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=TEST_SIZE, random_state=RANDOM_STATE
    )

    X_train_t = pre.fit_transform(X_train)
    X_test_t  = pre.transform(X_test)

    print(f"\n[preprocess] Train shape : {X_train_t.shape}")
    print(f"[preprocess] Test shape  : {X_test_t.shape}")
    print(f"[preprocess] Feature names: {pre.get_feature_names_out().tolist()}")
    print("\n✅  Preprocessor sanity-check passed.")
