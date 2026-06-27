"""
evaluation.py
=============
Step 4 — model evaluation utilities.

Functions:
  compute_metrics()    → full regression metric dict (MAE, MSE, RMSE, R², MAPE)
  print_metrics()      → formatted console report
  cross_val_report()   → k-fold cross-validation summary
  plot_predictions()   → actual vs predicted scatter + residual histogram
  plot_feature_importance() → bar chart for tree-based models
  compare_models()     → ranked summary DataFrame of all candidate models
"""

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")    # non-interactive backend — works in all environments
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from sklearn.model_selection import cross_validate
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from typing import Optional

from config import CV_FOLDS, REPORT_DIR


# ─────────────────────────────────────────────────────────────────────────────
#  Metrics
# ─────────────────────────────────────────────────────────────────────────────

def compute_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> dict:
    """
    Returns a dict with:
      MAE   — Mean Absolute Error (same unit as target)
      MSE   — Mean Squared Error
      RMSE  — Root Mean Squared Error
      R²    — Coefficient of determination (1 = perfect)
      MAPE  — Mean Absolute Percentage Error (%)
    """
    mae  = mean_absolute_error(y_true, y_pred)
    mse  = mean_squared_error(y_true, y_pred)
    rmse = np.sqrt(mse)
    r2   = r2_score(y_true, y_pred)

    # MAPE — guarded against zero targets
    mask = y_true != 0
    mape = np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100

    return {
        "MAE":  round(float(mae),  4),
        "MSE":  round(float(mse),  4),
        "RMSE": round(float(rmse), 4),
        "R²":   round(float(r2),   4),
        "MAPE": round(float(mape), 4),
    }


def print_metrics(metrics: dict, model_name: str = "") -> None:
    """Pretty-print metric dict to the console."""
    header = f" {model_name} Evaluation Metrics " if model_name else " Evaluation Metrics "
    print("\n" + "═" * 48)
    print(header.center(48))
    print("═" * 48)
    for k, v in metrics.items():
        unit = "%" if k == "MAPE" else ""
        print(f"  {k:<6} : {v:.4f}{unit}")
    print("═" * 48)


# ─────────────────────────────────────────────────────────────────────────────
#  Cross-validation
# ─────────────────────────────────────────────────────────────────────────────

def cross_val_report(model, X, y, cv: int = CV_FOLDS) -> dict:
    """
    Run k-fold CV and return mean ± std for MAE, RMSE, R².
    """
    scoring = {
        "neg_mae":  "neg_mean_absolute_error",
        "neg_rmse": "neg_root_mean_squared_error",
        "r2":       "r2",
    }
    results = cross_validate(model, X, y, cv=cv, scoring=scoring, n_jobs=-1)
    report = {
        "CV_MAE_mean":  round(-results["test_neg_mae"].mean(),  4),
        "CV_MAE_std":   round( results["test_neg_mae"].std(),   4),
        "CV_RMSE_mean": round(-results["test_neg_rmse"].mean(), 4),
        "CV_RMSE_std":  round( results["test_neg_rmse"].std(),  4),
        "CV_R²_mean":   round( results["test_r2"].mean(),       4),
        "CV_R²_std":    round( results["test_r2"].std(),        4),
    }
    return report


def print_cv_report(cv_report: dict, model_name: str = "") -> None:
    header = f" {model_name} {CV_FOLDS}-Fold CV Report "
    print("\n" + "─" * 48)
    print(header.center(48))
    print("─" * 48)
    print(f"  MAE  : {cv_report['CV_MAE_mean']:.4f}  ± {cv_report['CV_MAE_std']:.4f}")
    print(f"  RMSE : {cv_report['CV_RMSE_mean']:.4f}  ± {cv_report['CV_RMSE_std']:.4f}")
    print(f"  R²   : {cv_report['CV_R²_mean']:.4f}  ± {cv_report['CV_R²_std']:.4f}")
    print("─" * 48)


# ─────────────────────────────────────────────────────────────────────────────
#  Plots
# ─────────────────────────────────────────────────────────────────────────────

def plot_predictions(y_true, y_pred, model_name: str = "Model",
                     save_path: Optional[str] = None) -> None:
    """
    Two-panel figure:
      Left  — Actual vs Predicted scatter (ideal: diagonal line)
      Right — Residual histogram (ideal: centred on 0)
    """
    residuals = np.array(y_true) - np.array(y_pred)

    fig = plt.figure(figsize=(12, 5))
    gs  = gridspec.GridSpec(1, 2, figure=fig)

    # ── Panel 1: Actual vs Predicted ──────────────────────────────────────────
    ax1 = fig.add_subplot(gs[0])
    ax1.scatter(y_true, y_pred, alpha=0.35, s=20, color="#185FA5", edgecolors="none")
    lims = [min(min(y_true), min(y_pred)) - 2,
            max(max(y_true), max(y_pred)) + 2]
    ax1.plot(lims, lims, "r--", linewidth=1.2, label="Perfect fit")
    ax1.set_xlabel("Actual Health Score", fontsize=11)
    ax1.set_ylabel("Predicted Health Score", fontsize=11)
    ax1.set_title(f"{model_name} — Actual vs Predicted", fontsize=12, fontweight="bold")
    ax1.legend(fontsize=9)
    ax1.set_xlim(lims); ax1.set_ylim(lims)

    r2  = r2_score(y_true, y_pred)
    mae = mean_absolute_error(y_true, y_pred)
    ax1.text(0.05, 0.92, f"R² = {r2:.4f}\nMAE = {mae:.4f}",
             transform=ax1.transAxes, fontsize=9,
             verticalalignment="top",
             bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.5))

    # ── Panel 2: Residuals histogram ──────────────────────────────────────────
    ax2 = fig.add_subplot(gs[1])
    ax2.hist(residuals, bins=40, color="#1D9E75", edgecolor="white", alpha=0.8)
    ax2.axvline(0,   color="red",    linestyle="--", linewidth=1.2, label="Zero residual")
    ax2.axvline(residuals.mean(), color="orange", linestyle="-",
                linewidth=1.2, label=f"Mean = {residuals.mean():.2f}")
    ax2.set_xlabel("Residual (Actual − Predicted)", fontsize=11)
    ax2.set_ylabel("Count", fontsize=11)
    ax2.set_title("Residual Distribution", fontsize=12, fontweight="bold")
    ax2.legend(fontsize=9)

    plt.tight_layout()
    path = save_path or REPORT_DIR / f"{model_name.replace(' ', '_')}_predictions.png"
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"[plot]  Saved → {path}")


def plot_feature_importance(model_pipeline, feature_names: list,
                             model_name: str = "Model",
                             top_n: int = 15,
                             save_path: Optional[str] = None) -> None:
    """
    Horizontal bar chart of the top N feature importances.
    Works with RandomForest, GradientBoosting, ExtraTrees.
    """
    estimator = model_pipeline.named_steps.get("model")
    if not hasattr(estimator, "feature_importances_"):
        print(f"[importance] {model_name} has no feature_importances_ attribute — skipping.")
        return

    importances = estimator.feature_importances_
    n = min(top_n, len(feature_names))
    idx = np.argsort(importances)[-n:]

    fig, ax = plt.subplots(figsize=(9, 6))
    colors = ["#185FA5" if i == idx[-1] else "#1D9E75" for i in idx]
    ax.barh([feature_names[i] for i in idx],
            importances[idx], color=colors, edgecolor="none")
    ax.set_xlabel("Feature Importance (Gini / Impurity)", fontsize=11)
    ax.set_title(f"{model_name} — Top {n} Feature Importances",
                 fontsize=12, fontweight="bold")
    ax.invert_yaxis()
    plt.tight_layout()

    path = save_path or REPORT_DIR / f"{model_name.replace(' ', '_')}_importance.png"
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"[plot]  Saved → {path}")


# ─────────────────────────────────────────────────────────────────────────────
#  Model comparison table
# ─────────────────────────────────────────────────────────────────────────────

def compare_models(results: dict) -> pd.DataFrame:
    """
    Build a ranked summary DataFrame from a dict of
    { model_name: metrics_dict }.

    Returns a DataFrame sorted by R² descending.
    """
    rows = []
    for name, metrics in results.items():
        row = {"Model": name}
        row.update(metrics)
        rows.append(row)

    df = pd.DataFrame(rows).sort_values("R²", ascending=False).reset_index(drop=True)
    df.index += 1    # 1-based rank
    df.index.name = "Rank"
    return df


def plot_model_comparison(results: dict, save_path: Optional[str] = None) -> None:
    """Bar chart comparing RMSE and R² across all candidate models."""
    df = compare_models(results)
    models = df["Model"].tolist()
    rmse   = df["RMSE"].tolist()
    r2     = df["R²"].tolist()

    x = np.arange(len(models))
    width = 0.35

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5))

    # RMSE — lower is better
    bars1 = ax1.bar(x, rmse, width=0.55, color="#185FA5", alpha=0.85, edgecolor="white")
    ax1.set_xticks(x); ax1.set_xticklabels(models, rotation=30, ha="right")
    ax1.set_ylabel("RMSE", fontsize=11)
    ax1.set_title("RMSE by Model  (lower = better)", fontsize=12, fontweight="bold")
    for bar, val in zip(bars1, rmse):
        ax1.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.1,
                 f"{val:.3f}", ha="center", va="bottom", fontsize=9)

    # R² — higher is better
    bars2 = ax2.bar(x, r2, width=0.55, color="#1D9E75", alpha=0.85, edgecolor="white")
    ax2.set_xticks(x); ax2.set_xticklabels(models, rotation=30, ha="right")
    ax2.set_ylabel("R²", fontsize=11)
    ax2.set_title("R² by Model  (higher = better)", fontsize=12, fontweight="bold")
    ax2.set_ylim(0, 1.05)
    for bar, val in zip(bars2, r2):
        ax2.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.005,
                 f"{val:.4f}", ha="center", va="bottom", fontsize=9)

    plt.tight_layout()
    path = save_path or REPORT_DIR / "model_comparison.png"
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"[plot]  Saved → {path}")
