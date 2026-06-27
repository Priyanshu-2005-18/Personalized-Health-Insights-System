"""
pipeline.py
===========
Step 3: Training Pipeline

Orchestrates the full ML workflow:
  1. Generate / load data
  2. Preprocess (impute, cap, scale)
  3. Engineer features (sub-scores, interactions, ratios, poly, bins)
  4. Select and tune models (6 candidates → top 2 → RandomizedSearchCV)
  5. Evaluate on held-out test set
  6. Save best model + scaler + metadata with joblib

Artifact outputs (saved to models/):
  best_model.joblib     — best trained estimator
  scaler.joblib         — fitted RobustScaler
  feature_cols.joblib   — ordered list of feature column names
  model_metadata.joblib — metrics, model name, feature importances
  evaluation_plots.png  — 6-panel evaluation figure
"""

import os
import time
import numpy as np
import pandas as pd
import joblib
from datetime import datetime
from typing import Optional

from src.generate_data import generate_health_dataset
from src.preprocessor import preprocess, FEATURE_COLS
from src.feature_engineering import engineer_features, print_feature_summary
from src.model_selection import baseline_comparison, tune_top_models, select_best_model
from src.evaluator import (
    compute_metrics,
    print_metrics_table,
    cross_val_stability,
    feature_importance_report,
    plot_evaluation,
)

MODELS_DIR = "models"
DATA_PATH  = "data/health_data.csv"


def run_pipeline(
    data_path: Optional[str] = None,
    tune_n_iter: int = 30,
    random_state: int = 42,
) -> dict:
    """
    Full end-to-end training pipeline.

    Parameters
    ----------
    data_path    : path to CSV; if None, synthetic data is generated
    tune_n_iter  : iterations for RandomizedSearchCV
    random_state : reproducibility seed

    Returns
    -------
    artifacts dict with paths to all saved files
    """
    start_time = time.time()
    os.makedirs(MODELS_DIR, exist_ok=True)
    os.makedirs("data", exist_ok=True)

    print("\n" + "╔" + "═"*58 + "╗")
    print("║   HEALTH SCORE PREDICTION — ML TRAINING PIPELINE      ║")
    print("╚" + "═"*58 + "╝")

    # ────────────────────────────────────────────────────────────
    # STEP 1 — Data
    # ────────────────────────────────────────────────────────────
    print("\n▶  STEP 1 — DATA LOADING")
    if data_path is None or not os.path.exists(data_path):
        print("   Generating synthetic health dataset (2 000 samples)...")
        df_raw = generate_health_dataset(2000)
        df_raw.to_csv(DATA_PATH, index=False)
        data_path = DATA_PATH
        print(f"   Saved → {DATA_PATH}")
    else:
        df_raw = pd.read_csv(data_path)
        print(f"   Loaded existing dataset: {data_path}")

    # ────────────────────────────────────────────────────────────
    # STEP 2 — Feature Engineering (before splitting)
    # ────────────────────────────────────────────────────────────
    print("\n▶  STEP 2 — FEATURE ENGINEERING")
    df_eng, feature_cols = engineer_features(df_raw)
    print_feature_summary(feature_cols)

    # Save engineered dataset
    eng_path = DATA_PATH.replace(".csv", "_engineered.csv")
    df_eng.to_csv(eng_path, index=False)
    print(f"\n   Engineered dataset saved → {eng_path}")

    # ────────────────────────────────────────────────────────────
    # STEP 3 — Preprocessing
    # ────────────────────────────────────────────────────────────
    print("\n▶  STEP 3 — PREPROCESSING")

    # Re-run preprocess on engineered feature set
    from sklearn.model_selection import train_test_split
    from sklearn.preprocessing import RobustScaler
    from sklearn.impute import SimpleImputer

    TARGET_COL = "health_score"
    X = df_eng[feature_cols].values
    y = df_eng[TARGET_COL].values

    # Fill any remaining NaN from feature engineering
    imp = SimpleImputer(strategy="median")
    X = imp.fit_transform(X)

    # Train / val / test split (70 / 15 / 15)
    X_tv, X_test, y_tv, y_test = train_test_split(
        X, y, test_size=0.15, random_state=random_state
    )
    X_train, X_val, y_train, y_val = train_test_split(
        X_tv, y_tv, test_size=0.15 / 0.85, random_state=random_state
    )

    scaler = RobustScaler()
    X_train = scaler.fit_transform(X_train)
    X_val   = scaler.transform(X_val)
    X_test  = scaler.transform(X_test)

    print(f"\n   Train : {X_train.shape[0]:>5} samples × {X_train.shape[1]} features")
    print(f"   Val   : {X_val.shape[0]:>5} samples × {X_val.shape[1]} features")
    print(f"   Test  : {X_test.shape[0]:>5} samples × {X_test.shape[1]} features")

    # ────────────────────────────────────────────────────────────
    # STEP 4 — Model Selection
    # ────────────────────────────────────────────────────────────
    print("\n▶  STEP 4 — MODEL SELECTION & TUNING")
    baseline_results, top2 = baseline_comparison(X_train, y_train)
    tuned_models = tune_top_models(top2, X_train, y_train, n_iter=tune_n_iter)
    best_name, best_model = select_best_model(tuned_models, X_val, y_val)

    # ────────────────────────────────────────────────────────────
    # STEP 5 — Final Evaluation on Test Set
    # ────────────────────────────────────────────────────────────
    print("\n▶  STEP 5 — FINAL TEST SET EVALUATION")
    y_pred = best_model.predict(X_test)
    test_metrics = compute_metrics(y_test, y_pred)
    print_metrics_table(test_metrics, title=f"TEST SET — {best_name}")

    # Val metrics for comparison
    val_metrics = compute_metrics(y_val, best_model.predict(X_val))
    print(f"\n  Val R²  = {val_metrics['R²']:.4f}  │  "
          f"Test R² = {test_metrics['R²']:.4f}  "
          f"({'✅ No overfit' if abs(val_metrics['R²'] - test_metrics['R²']) < 0.03 else '⚠️  Check overfit'})")

    # Cross-validation stability
    X_trainval = np.vstack([X_train, X_val])
    y_trainval = np.concatenate([y_train, y_val])
    cross_val_stability(best_model, X_trainval, y_trainval, cv=10)

    # Feature importance
    feature_importance_report(best_model, X_test, y_test, feature_cols)

    # Plots
    plot_evaluation(
        best_model, X_test, y_test, feature_cols,
        model_name=best_name,
        save_path=f"{MODELS_DIR}/evaluation_plots.png",
    )

    # ────────────────────────────────────────────────────────────
    # STEP 6 — Save Artifacts
    # ────────────────────────────────────────────────────────────
    print(f"\n▶  STEP 6 — SAVING MODEL ARTIFACTS")
    metadata = {
        "model_name":      best_name,
        "feature_cols":    feature_cols,
        "n_features":      len(feature_cols),
        "train_samples":   X_train.shape[0],
        "test_samples":    X_test.shape[0],
        "test_metrics":    test_metrics,
        "val_metrics":     val_metrics,
        "baseline_results": baseline_results,
        "trained_at":      datetime.now().isoformat(),
        "sklearn_version": __import__("sklearn").__version__,
        "random_state":    random_state,
    }

    artifacts = {
        "model":        f"{MODELS_DIR}/best_model.joblib",
        "scaler":       f"{MODELS_DIR}/scaler.joblib",
        "feature_cols": f"{MODELS_DIR}/feature_cols.joblib",
        "imputer":      f"{MODELS_DIR}/imputer.joblib",
        "metadata":     f"{MODELS_DIR}/model_metadata.joblib",
        "plots":        f"{MODELS_DIR}/evaluation_plots.png",
    }

    joblib.dump(best_model,   artifacts["model"],        compress=3)
    joblib.dump(scaler,       artifacts["scaler"],       compress=3)
    joblib.dump(feature_cols, artifacts["feature_cols"], compress=3)
    joblib.dump(imp,          artifacts["imputer"],      compress=3)
    joblib.dump(metadata,     artifacts["metadata"],     compress=3)

    elapsed = time.time() - start_time
    print(f"\n{'─'*46}")
    for name, path in artifacts.items():
        if os.path.exists(path):
            size = os.path.getsize(path) / 1024
            print(f"  ✅ {name:<14} → {path}  ({size:.1f} KB)")

    print(f"\n{'='*46}")
    print(f"  🏁 Pipeline complete in {elapsed:.1f}s")
    print(f"  🏆 Best model : {best_name}")
    print(f"  📊 Test R²    : {test_metrics['R²']:.4f}")
    print(f"  📏 Test MAE   : {test_metrics['MAE']:.3f} pts")
    print(f"{'='*46}\n")

    return artifacts


if __name__ == "__main__":
    run_pipeline()
