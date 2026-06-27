"""
evaluator.py
============
Step 5: Evaluation Metrics

Computes and reports:
  Regression metrics:
    R²  (coefficient of determination) — variance explained
    MAE (mean absolute error)          — average prediction error in score points
    RMSE (root mean squared error)     — penalises large errors more
    MAPE (mean absolute % error)       — scale-independent error %
    Max Error                          — worst-case single prediction
    Explained Variance Score           — proportion of variance captured

  Residual analysis:
    Residuals vs predicted plot
    Residual distribution histogram
    Q-Q plot for normality check

  Feature importance:
    Permutation importance (model-agnostic)
    Tree-based importance (if applicable)

  Cross-validation stability:
    Final 10-fold CV on full training set
"""

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from sklearn.metrics import (
    r2_score,
    mean_absolute_error,
    mean_squared_error,
    explained_variance_score,
    max_error,
)
from sklearn.inspection import permutation_importance
from sklearn.model_selection import cross_val_score
from typing import List, Optional
import warnings
warnings.filterwarnings("ignore")


def compute_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> dict:
    """Compute all regression evaluation metrics."""
    mse  = mean_squared_error(y_true, y_pred)
    rmse = np.sqrt(mse)
    mae  = mean_absolute_error(y_true, y_pred)
    r2   = r2_score(y_true, y_pred)
    evs  = explained_variance_score(y_true, y_pred)
    me   = max_error(y_true, y_pred)

    # MAPE — avoid division by zero
    mask = y_true != 0
    mape = np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100

    # Median Absolute Error — robust to outlier predictions
    medae = np.median(np.abs(y_true - y_pred))

    return {
        "R²":                    round(r2, 4),
        "MAE":                   round(mae, 3),
        "RMSE":                  round(rmse, 3),
        "MAPE (%)":              round(mape, 2),
        "Max Error":             round(me, 3),
        "Median Abs Error":      round(medae, 3),
        "Explained Variance":    round(evs, 4),
        "MSE":                   round(mse, 3),
    }


def print_metrics_table(
    metrics: dict,
    title: str = "Evaluation Metrics",
) -> None:
    """Pretty-print metrics table."""
    width = 46
    print(f"\n{'='*width}")
    print(f"  {title}")
    print(f"{'='*width}")
    for metric, value in metrics.items():
        bar = ""
        if metric == "R²":
            filled = int(value * 20)
            bar = f"  {'█'*filled}{'░'*(20-filled)}"
        print(f"  {metric:<22} {str(value):>8}{bar}")
    print(f"{'='*width}")

    # Interpretation guide
    r2 = metrics.get("R²", 0)
    mae = metrics.get("MAE", 0)
    print("\n  📖 Interpretation:")
    if r2 >= 0.90:
        print(f"  ✅ Excellent fit — model explains {r2*100:.1f}% of variance")
    elif r2 >= 0.80:
        print(f"  ✅ Good fit — model explains {r2*100:.1f}% of variance")
    elif r2 >= 0.70:
        print(f"  ⚠️  Fair fit — model explains {r2*100:.1f}% of variance")
    else:
        print(f"  ❌ Poor fit — model explains only {r2*100:.1f}% of variance")
    print(f"  📏 Average prediction error: ±{mae:.2f} health score points")


def cross_val_stability(
    model,
    X_train: np.ndarray,
    y_train: np.ndarray,
    cv: int = 10,
) -> None:
    """10-fold CV on full training set to check model stability."""
    scores = cross_val_score(model, X_train, y_train, cv=cv, scoring="r2", n_jobs=-1)
    print(f"\n{'='*46}")
    print(f"  {cv}-FOLD CROSS-VALIDATION STABILITY")
    print(f"{'='*46}")
    print(f"  R² per fold: {np.round(scores, 4)}")
    print(f"  Mean R²    : {scores.mean():.4f}")
    print(f"  Std  R²    : {scores.std():.4f}")
    print(f"  Min  R²    : {scores.min():.4f}")
    print(f"  Max  R²    : {scores.max():.4f}")
    if scores.std() < 0.02:
        print("  ✅ Very stable — low variance across folds")
    elif scores.std() < 0.05:
        print("  ✅ Stable — acceptable variance across folds")
    else:
        print("  ⚠️  High variance — model may be overfitting some folds")


def feature_importance_report(
    model,
    X_val: np.ndarray,
    y_val: np.ndarray,
    feature_cols: List[str],
    top_n: int = 15,
) -> pd.DataFrame:
    """
    Compute feature importances using two methods:
      1. Tree-based (if available) — fast, built-in
      2. Permutation importance   — model-agnostic, more reliable
    """
    print(f"\n{'='*46}")
    print(f"  FEATURE IMPORTANCE  (top {top_n})")
    print(f"{'='*46}")

    # Permutation importance (model-agnostic)
    perm = permutation_importance(
        model, X_val, y_val, n_repeats=10, random_state=42, n_jobs=-1
    )
    perm_df = pd.DataFrame({
        "feature":    feature_cols,
        "perm_importance": perm.importances_mean,
        "perm_std":   perm.importances_std,
    }).sort_values("perm_importance", ascending=False).head(top_n)

    print("\n  Permutation Importance (R² drop when feature shuffled):")
    print(f"  {'Feature':<26} {'Importance':>12} {'±Std':>8}")
    print("  " + "-" * 48)
    for _, row in perm_df.iterrows():
        bar_len = max(0, int(row["perm_importance"] / perm_df["perm_importance"].max() * 20))
        bar = "█" * bar_len
        print(
            f"  {row['feature']:<26} "
            f"{row['perm_importance']:>12.4f} "
            f"{row['perm_std']:>8.4f}  {bar}"
        )

    # Tree-based importance (if available)
    if hasattr(model, "feature_importances_"):
        tree_df = pd.DataFrame({
            "feature":       feature_cols,
            "tree_importance": model.feature_importances_,
        }).sort_values("tree_importance", ascending=False).head(top_n)

        print("\n  Tree-Based Importance (Gini impurity / MSE reduction):")
        print(f"  {'Feature':<26} {'Importance':>12}")
        print("  " + "-" * 40)
        for _, row in tree_df.iterrows():
            bar_len = int(row["tree_importance"] / tree_df["tree_importance"].max() * 20)
            bar = "█" * bar_len
            print(f"  {row['feature']:<26} {row['tree_importance']:>12.4f}  {bar}")

    return perm_df


def plot_evaluation(
    model,
    X_test: np.ndarray,
    y_test: np.ndarray,
    feature_cols: List[str],
    model_name: str = "Model",
    save_path: str = "models/evaluation_plots.png",
) -> None:
    """
    Generate a 6-panel evaluation figure:
      [1] Predicted vs Actual scatter
      [2] Residuals vs Predicted
      [3] Residual distribution
      [4] Permutation feature importance (top 10)
      [5] Error distribution CDF
      [6] Metrics summary text panel
    """
    y_pred = model.predict(X_test)
    residuals = y_test - y_pred
    metrics = compute_metrics(y_test, y_pred)

    fig = plt.figure(figsize=(18, 12))
    fig.suptitle(
        f"Health Score Prediction — {model_name} Evaluation",
        fontsize=14, fontweight="bold", y=0.98
    )
    gs = gridspec.GridSpec(2, 3, figure=fig, hspace=0.4, wspace=0.35)

    TEAL   = "#1D9E75"
    ORANGE = "#F5A623"
    PURPLE = "#534AB7"
    RED    = "#D85A30"

    # ── Panel 1: Predicted vs Actual ────────────────────────────────────────
    ax1 = fig.add_subplot(gs[0, 0])
    ax1.scatter(y_test, y_pred, alpha=0.5, s=20, color=TEAL, edgecolors="none")
    lo = min(y_test.min(), y_pred.min()) - 2
    hi = max(y_test.max(), y_pred.max()) + 2
    ax1.plot([lo, hi], [lo, hi], "r--", lw=1.5, label="Perfect fit")
    ax1.set_xlabel("Actual Health Score")
    ax1.set_ylabel("Predicted Health Score")
    ax1.set_title(f"Predicted vs Actual  (R²={metrics['R²']})")
    ax1.legend(fontsize=8)
    ax1.grid(True, alpha=0.3)

    # ── Panel 2: Residuals vs Predicted ─────────────────────────────────────
    ax2 = fig.add_subplot(gs[0, 1])
    ax2.scatter(y_pred, residuals, alpha=0.5, s=20, color=ORANGE, edgecolors="none")
    ax2.axhline(0, color="red", lw=1.5, ls="--")
    ax2.axhline(metrics["MAE"],  color="gray", lw=1, ls=":", alpha=0.7)
    ax2.axhline(-metrics["MAE"], color="gray", lw=1, ls=":", alpha=0.7)
    ax2.set_xlabel("Predicted Health Score")
    ax2.set_ylabel("Residual (Actual - Predicted)")
    ax2.set_title(f"Residuals vs Predicted  (MAE={metrics['MAE']})")
    ax2.grid(True, alpha=0.3)

    # ── Panel 3: Residual distribution ──────────────────────────────────────
    ax3 = fig.add_subplot(gs[0, 2])
    ax3.hist(residuals, bins=30, color=PURPLE, alpha=0.8, edgecolor="white", lw=0.5)
    ax3.axvline(0,                color="red", lw=1.5, ls="--", label="Zero")
    ax3.axvline(residuals.mean(), color="orange", lw=1.5, ls="-",
                label=f"Mean={residuals.mean():.2f}")
    ax3.set_xlabel("Residual")
    ax3.set_ylabel("Count")
    ax3.set_title("Residual Distribution")
    ax3.legend(fontsize=8)
    ax3.grid(True, alpha=0.3)

    # ── Panel 4: Feature importance (top 10) ────────────────────────────────
    ax4 = fig.add_subplot(gs[1, 0])
    perm = permutation_importance(
        model, X_test, y_test, n_repeats=5, random_state=42, n_jobs=-1
    )
    perm_df = pd.DataFrame({
        "feature": feature_cols,
        "importance": perm.importances_mean
    }).sort_values("importance", ascending=False).head(10)

    ax4.barh(perm_df["feature"][::-1], perm_df["importance"][::-1],
             color=TEAL, alpha=0.85, edgecolor="white")
    ax4.set_xlabel("Permutation Importance (R² drop)")
    ax4.set_title("Top 10 Feature Importances")
    ax4.grid(True, alpha=0.3, axis="x")

    # ── Panel 5: Cumulative error distribution ──────────────────────────────
    ax5 = fig.add_subplot(gs[1, 1])
    abs_errors = np.abs(residuals)
    sorted_err = np.sort(abs_errors)
    cumulative  = np.arange(1, len(sorted_err)+1) / len(sorted_err)
    ax5.plot(sorted_err, cumulative * 100, color=PURPLE, lw=2)
    ax5.axvline(metrics["MAE"],  color="orange", ls="--", lw=1.5,
                label=f"MAE = {metrics['MAE']}")
    ax5.axvline(metrics["RMSE"], color="red",    ls="--", lw=1.5,
                label=f"RMSE = {metrics['RMSE']}")
    # Draw 90th percentile
    p90 = np.percentile(abs_errors, 90)
    ax5.axvline(p90, color="gray", ls=":", lw=1.5, label=f"P90 = {p90:.2f}")
    ax5.set_xlabel("Absolute Error (score points)")
    ax5.set_ylabel("Cumulative %")
    ax5.set_title("Cumulative Error Distribution")
    ax5.legend(fontsize=8)
    ax5.grid(True, alpha=0.3)

    # ── Panel 6: Metrics summary ─────────────────────────────────────────────
    ax6 = fig.add_subplot(gs[1, 2])
    ax6.axis("off")
    metric_lines = [
        ("Model", model_name),
        ("", ""),
        ("R²",               f"{metrics['R²']:.4f}"),
        ("MAE",              f"{metrics['MAE']:.3f} pts"),
        ("RMSE",             f"{metrics['RMSE']:.3f} pts"),
        ("MAPE",             f"{metrics['MAPE (%)']:.2f}%"),
        ("Max Error",        f"{metrics['Max Error']:.3f} pts"),
        ("Median Abs Error", f"{metrics['Median Abs Error']:.3f} pts"),
        ("Explained Var",    f"{metrics['Explained Variance']:.4f}"),
        ("", ""),
        ("Test samples",     f"{len(y_test)}"),
        ("Features",         f"{len(feature_cols)}"),
    ]
    y_pos = 0.95
    for label, value in metric_lines:
        if label == "":
            y_pos -= 0.03
            continue
        weight = "bold" if label in ("Model", "R²", "MAE", "RMSE") else "normal"
        color  = TEAL if label == "R²" else "black"
        ax6.text(0.05, y_pos, label + ":",  transform=ax6.transAxes,
                 fontsize=10, fontweight=weight, va="top")
        ax6.text(0.55, y_pos, value,         transform=ax6.transAxes,
                 fontsize=10, va="top", color=color, fontweight=weight)
        y_pos -= 0.07

    ax6.set_title("Performance Summary", fontweight="bold")
    ax6.add_patch(plt.Rectangle((0, 0), 1, 1,
                  fill=False, edgecolor="lightgray", lw=1,
                  transform=ax6.transAxes))

    import os
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    plt.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"\n📊 Evaluation plots saved → {save_path}")
