"""
train.py
========
End-to-end training pipeline.

Steps:
  1. Load & validate data
  2. Train / validation / test split
  3. Run GridSearchCV for every candidate model
  4. Select the best model by CV R²
  5. Evaluate best model on held-out test set
  6. Generate evaluation plots
  7. Save best model with joblib

Run:
  python train.py
"""

import warnings
import time
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.model_selection import GridSearchCV, train_test_split

warnings.filterwarnings("ignore")

from config import (
    CV_FOLDS, FEATURES, MODEL_DIR, PIPELINE_PATH, RANDOM_STATE,
    REPORT_DIR, SCORING, TARGET, TEST_SIZE,
)
from evaluation import (
    compare_models, compute_metrics, cross_val_report,
    plot_feature_importance, plot_model_comparison, plot_predictions,
    print_cv_report, print_metrics,
)
from model_selection import get_candidate_pipelines, get_param_grids
from preprocessing import load_data, validate_data

# Ensure output directories exist
MODEL_DIR.mkdir(parents=True, exist_ok=True)
REPORT_DIR.mkdir(parents=True, exist_ok=True)


# ─────────────────────────────────────────────────────────────────────────────
#  1. Load & validate
# ─────────────────────────────────────────────────────────────────────────────

def prepare_data():
    df = validate_data(load_data())

    X = df[FEATURES]
    y = df[TARGET]

    # Train (80 %) / Test (20 %) split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=TEST_SIZE, random_state=RANDOM_STATE
    )
    print(f"\n[split]  Train: {X_train.shape[0]}  |  Test: {X_test.shape[0]}")
    return X_train, X_test, y_train, y_test


# ─────────────────────────────────────────────────────────────────────────────
#  2. Hyper-parameter search
# ─────────────────────────────────────────────────────────────────────────────

def run_grid_search(X_train, y_train) -> dict:
    """
    Run GridSearchCV for every candidate model.
    Returns { model_name: best_estimator } after fitting on full training set.
    """
    pipelines   = get_candidate_pipelines()
    param_grids = get_param_grids()
    best_models = {}

    print(f"\n{'═'*60}")
    print(f"  Hyper-parameter search  ({CV_FOLDS}-fold CV, {len(pipelines)} models)")
    print(f"{'═'*60}")

    for name, pipeline in pipelines.items():
        t0 = time.time()
        print(f"\n[search] {name} ...", end=" ", flush=True)

        grid = GridSearchCV(
            estimator  = pipeline,
            param_grid = param_grids.get(name, {}),
            cv         = CV_FOLDS,
            scoring    = SCORING,
            n_jobs     = -1,
            refit      = True,   # refit on full training data with best params
            verbose    = 0,
        )
        grid.fit(X_train, y_train)
        elapsed = time.time() - t0

        best_score = np.sqrt(-grid.best_score_)   # RMSE from neg_MSE
        print(f"done in {elapsed:.1f}s  |  best CV RMSE = {best_score:.4f}")
        print(f"         best params: {grid.best_params_}")

        best_models[name] = grid.best_estimator_

    return best_models


# ─────────────────────────────────────────────────────────────────────────────
#  3. Evaluate all models
# ─────────────────────────────────────────────────────────────────────────────

def evaluate_all(best_models: dict, X_train, X_test, y_train, y_test) -> dict:
    """
    Compute test-set metrics for every best model.
    Returns { model_name: metrics_dict }.
    """
    all_metrics = {}
    for name, model in best_models.items():
        y_pred = model.predict(X_test)
        metrics = compute_metrics(y_test.values, y_pred)
        all_metrics[name] = metrics
        print(f"\n  {name:<20s}  "
              f"RMSE={metrics['RMSE']:.4f}  "
              f"R²={metrics['R²']:.4f}  "
              f"MAE={metrics['MAE']:.4f}")
    return all_metrics


# ─────────────────────────────────────────────────────────────────────────────
#  4. Select best model
# ─────────────────────────────────────────────────────────────────────────────

def select_best(all_metrics: dict, best_models: dict):
    """Pick the model with the highest test-set R²."""
    best_name = max(all_metrics, key=lambda k: all_metrics[k]["R²"])
    best_model = best_models[best_name]
    print(f"\n🏆  Best model: {best_name}  "
          f"(R² = {all_metrics[best_name]['R²']:.4f})")
    return best_name, best_model


# ─────────────────────────────────────────────────────────────────────────────
#  5. Full report on best model
# ─────────────────────────────────────────────────────────────────────────────

def full_report(best_name, best_model, X_train, X_test, y_train, y_test):
    y_pred = best_model.predict(X_test)
    metrics = compute_metrics(y_test.values, y_pred)

    print_metrics(metrics, best_name)

    # Cross-validation report on training data
    cv_report = cross_val_report(best_model, X_train, y_train, cv=CV_FOLDS)
    print_cv_report(cv_report, best_name)

    # Plots
    plot_predictions(y_test.values, y_pred, model_name=best_name)

    # Feature importance (for tree-based models)
    from feature_engineering import HealthFeatureEngineer
    fe = HealthFeatureEngineer()
    feature_names = list(fe.get_feature_names_out())
    plot_feature_importance(best_model, feature_names, model_name=best_name)

    return metrics, cv_report


# ─────────────────────────────────────────────────────────────────────────────
#  6. Save model
# ─────────────────────────────────────────────────────────────────────────────

def save_model(model, name: str) -> None:
    """
    Persist the full sklearn Pipeline (including preprocessing + feature
    engineering) with joblib. The saved file contains everything needed
    for inference — no separate scaler or encoder files required.
    """
    import joblib
    path = PIPELINE_PATH
    joblib.dump(model, path, compress=3)   # compress=3 → good size/speed trade-off
    size_kb = path.stat().st_size / 1024
    print(f"\n💾  Model saved → {path}  ({size_kb:.1f} KB)")


# ─────────────────────────────────────────────────────────────────────────────
#  Main
# ─────────────────────────────────────────────────────────────────────────────

def main():
    print("\n" + "═" * 60)
    print("  Health Score Prediction — Training Pipeline")
    print("═" * 60)

    # Step 1 — Data
    X_train, X_test, y_train, y_test = prepare_data()

    # Step 2 — Grid search
    best_models = run_grid_search(X_train, y_train)

    # Step 3 — Evaluate all
    print(f"\n{'─'*60}")
    print("  Test-set Metrics (all models)")
    print(f"{'─'*60}")
    all_metrics = evaluate_all(best_models, X_train, X_test, y_train, y_test)

    # Step 4 — Select best
    best_name, best_model = select_best(all_metrics, best_models)

    # Step 5 — Full report
    metrics, cv_report = full_report(
        best_name, best_model, X_train, X_test, y_train, y_test
    )

    # Step 6 — Model comparison plot
    plot_model_comparison(all_metrics)

    # Step 7 — Save
    save_model(best_model, best_name)

    # Summary table
    print("\n" + "═" * 60)
    print("  Final Model Comparison (ranked by R²)")
    print("═" * 60)
    print(compare_models(all_metrics).to_string())

    print("\n✅  Pipeline complete.\n")
    return best_model, best_name, metrics


if __name__ == "__main__":
    main()
