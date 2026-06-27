"""
model_selection.py
==================
Step 4: Model Selection

Trains and compares 6 regression models:
  1. Linear Regression      — interpretable baseline
  2. Ridge Regression       — L2 regularised linear model
  3. Random Forest          — robust ensemble, handles non-linearity
  4. Gradient Boosting      — sequential ensemble, typically highest accuracy
  5. SVR (RBF kernel)       — effective in high-dimensional feature spaces
  6. K-Nearest Neighbours   — non-parametric baseline

Selection process:
  Phase 1 — Quick comparison with default hyperparameters + 5-fold CV
  Phase 2 — RandomizedSearchCV on top 2 performers
  Phase 3 — Final evaluation on held-out test set
"""

import numpy as np
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.svm import SVR
from sklearn.neighbors import KNeighborsRegressor
from sklearn.model_selection import cross_val_score, RandomizedSearchCV
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import RobustScaler
from typing import Dict, Tuple
import warnings
warnings.filterwarnings("ignore")


# ─────────────────────────────────────────────────────────────────────────────
#  Phase 1 — Baseline comparison (default hyperparameters)
# ─────────────────────────────────────────────────────────────────────────────

BASELINE_MODELS: Dict[str, object] = {
    "Linear Regression":   LinearRegression(),
    "Ridge Regression":    Ridge(alpha=1.0),
    "Random Forest":       RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1),
    "Gradient Boosting":   GradientBoostingRegressor(n_estimators=100, random_state=42),
    "SVR (RBF)":           SVR(kernel="rbf", C=10, epsilon=0.5),
    "KNN":                 KNeighborsRegressor(n_neighbors=7),
}


def baseline_comparison(
    X_train: np.ndarray,
    y_train: np.ndarray,
    cv: int = 5,
) -> Dict[str, dict]:
    """
    Train all 6 models on X_train with 5-fold CV.
    Returns dict with mean R², RMSE, and MAE for each model.
    """
    print(f"\n{'='*60}")
    print("PHASE 1 — BASELINE MODEL COMPARISON  (5-fold CV)")
    print(f"{'='*60}")
    print(f"{'Model':<22} {'R² (mean±std)':>18} {'RMSE':>10} {'MAE':>10}")
    print("-" * 62)

    results = {}
    for name, model in BASELINE_MODELS.items():
        # R² score
        r2_scores = cross_val_score(
            model, X_train, y_train, cv=cv, scoring="r2", n_jobs=-1
        )
        # Neg RMSE
        rmse_scores = np.sqrt(-cross_val_score(
            model, X_train, y_train, cv=cv,
            scoring="neg_mean_squared_error", n_jobs=-1
        ))
        # Neg MAE
        mae_scores = -cross_val_score(
            model, X_train, y_train, cv=cv,
            scoring="neg_mean_absolute_error", n_jobs=-1
        )

        results[name] = {
            "r2_mean":   r2_scores.mean(),
            "r2_std":    r2_scores.std(),
            "rmse_mean": rmse_scores.mean(),
            "mae_mean":  mae_scores.mean(),
        }
        print(
            f"{name:<22} "
            f"{r2_scores.mean():>8.4f} ± {r2_scores.std():.4f}"
            f"{rmse_scores.mean():>10.3f}"
            f"{mae_scores.mean():>10.3f}"
        )

    # Pick top 2 by R²
    sorted_models = sorted(results.items(), key=lambda x: x[1]["r2_mean"], reverse=True)
    top2 = [name for name, _ in sorted_models[:2]]
    print(f"\n🏆 Top 2 models selected for tuning: {top2[0]} and {top2[1]}")
    return results, top2


# ─────────────────────────────────────────────────────────────────────────────
#  Phase 2 — Hyperparameter tuning (RandomizedSearchCV)
# ─────────────────────────────────────────────────────────────────────────────

PARAM_GRIDS = {
    "Random Forest": {
        "n_estimators":      [100, 200, 300, 500],
        "max_depth":         [None, 5, 10, 15, 20],
        "min_samples_split": [2, 5, 10],
        "min_samples_leaf":  [1, 2, 4],
        "max_features":      ["sqrt", "log2", 0.5, 0.8],
        "bootstrap":         [True, False],
    },
    "Gradient Boosting": {
        "n_estimators":   [100, 200, 300],
        "learning_rate":  [0.01, 0.05, 0.1, 0.2],
        "max_depth":      [3, 4, 5, 6],
        "subsample":      [0.6, 0.7, 0.8, 0.9, 1.0],
        "min_samples_split": [2, 5, 10],
        "max_features":   ["sqrt", "log2", None],
    },
    "Ridge Regression": {
        "alpha": [0.001, 0.01, 0.1, 1.0, 10.0, 100.0, 1000.0],
    },
    "SVR (RBF)": {
        "C":       [0.1, 1, 10, 50, 100],
        "epsilon": [0.01, 0.1, 0.5, 1.0],
        "gamma":   ["scale", "auto", 0.01, 0.1],
    },
    "Linear Regression": {},
    "KNN": {
        "n_neighbors": [3, 5, 7, 10, 15],
        "weights":     ["uniform", "distance"],
        "metric":      ["euclidean", "manhattan"],
    },
}


def tune_model(
    name: str,
    X_train: np.ndarray,
    y_train: np.ndarray,
    n_iter: int = 30,
    cv: int = 5,
    random_state: int = 42,
) -> Tuple[object, dict]:
    """Run RandomizedSearchCV for a single model."""
    model = BASELINE_MODELS[name]
    param_grid = PARAM_GRIDS.get(name, {})

    if not param_grid:
        # No tuning needed (e.g. LinearRegression)
        model.fit(X_train, y_train)
        return model, {}

    search = RandomizedSearchCV(
        estimator=model,
        param_distributions=param_grid,
        n_iter=min(n_iter, len(param_grid) * 5),
        scoring="r2",
        cv=cv,
        refit=True,
        n_jobs=-1,
        random_state=random_state,
        verbose=0,
    )
    search.fit(X_train, y_train)
    print(f"\n  {name} best params:")
    for k, v in search.best_params_.items():
        print(f"    {k}: {v}")
    print(f"  Best CV R²: {search.best_score_:.4f}")
    return search.best_estimator_, search.best_params_


def tune_top_models(
    top_models: list,
    X_train: np.ndarray,
    y_train: np.ndarray,
    n_iter: int = 30,
) -> Dict[str, object]:
    """Tune top N models and return fitted estimators."""
    print(f"\n{'='*60}")
    print("PHASE 2 — HYPERPARAMETER TUNING  (RandomizedSearchCV)")
    print(f"{'='*60}")
    tuned = {}
    for name in top_models:
        print(f"\n🔧 Tuning: {name}")
        estimator, best_params = tune_model(name, X_train, y_train, n_iter=n_iter)
        tuned[name] = estimator
    return tuned


# ─────────────────────────────────────────────────────────────────────────────
#  Phase 3 — Select best model by validation R²
# ─────────────────────────────────────────────────────────────────────────────

def select_best_model(
    tuned_models: Dict[str, object],
    X_val: np.ndarray,
    y_val: np.ndarray,
) -> Tuple[str, object]:
    """Evaluate tuned models on the validation set and pick the winner."""
    from sklearn.metrics import r2_score

    print(f"\n{'='*60}")
    print("PHASE 3 — VALIDATION SET EVALUATION")
    print(f"{'='*60}")
    print(f"{'Model':<22} {'Val R²':>10}")
    print("-" * 35)

    best_name, best_model, best_r2 = None, None, -np.inf
    for name, model in tuned_models.items():
        r2 = r2_score(y_val, model.predict(X_val))
        print(f"{name:<22} {r2:>10.4f}")
        if r2 > best_r2:
            best_r2, best_name, best_model = r2, name, model

    print(f"\n✅ Best model: {best_name}  (Val R² = {best_r2:.4f})")
    return best_name, best_model
