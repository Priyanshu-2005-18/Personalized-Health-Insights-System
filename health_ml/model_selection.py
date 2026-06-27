"""
model_selection.py
==================
Step 3 — candidate model definitions and hyper-parameter search.

Models compared:
  1. Ridge Regression          — linear baseline
  2. Random Forest Regressor   — ensemble, handles non-linearity
  3. Gradient Boosting         — sequential boosting, typically best on tabular
  4. Support Vector Regressor  — kernel-based, good on scaled data
  5. Extra Trees Regressor     — randomised forests, fast
  6. MLP Regressor             — feed-forward neural network

Each model is wrapped in an sklearn Pipeline:
  [HealthFeatureEngineer → ColumnTransformer (impute+scale) → Model]

GridSearchCV is run per model; the best estimator from each
search is returned to the training pipeline for final comparison.
"""

from sklearn.ensemble import (
    ExtraTreesRegressor,
    GradientBoostingRegressor,
    RandomForestRegressor,
)
from sklearn.linear_model import Ridge
from sklearn.neural_network import MLPRegressor
from sklearn.pipeline import Pipeline
from sklearn.svm import SVR

from config import CV_FOLDS, PARAM_GRIDS, SCORING
from feature_engineering import HealthFeatureEngineer
from preprocessing import build_preprocessor


# ─────────────────────────────────────────────────────────────────────────────
#  Model registry
# ─────────────────────────────────────────────────────────────────────────────

def get_candidate_pipelines() -> dict:
    """
    Returns a dict of { model_name: sklearn Pipeline }.
    Each pipeline includes feature engineering + preprocessing + the model.
    The preprocessor operates on the *output* of HealthFeatureEngineer.
    """
    fe = HealthFeatureEngineer()

    candidates = {
        "Ridge": Pipeline([
            ("engineer",     HealthFeatureEngineer()),
            ("preprocessor", build_full_preprocessor()),
            ("model",        Ridge()),
        ]),
        "RandomForest": Pipeline([
            ("engineer",     HealthFeatureEngineer()),
            ("preprocessor", build_full_preprocessor()),
            ("model",        RandomForestRegressor(random_state=42, n_jobs=-1)),
        ]),
        "GradientBoosting": Pipeline([
            ("engineer",     HealthFeatureEngineer()),
            ("preprocessor", build_full_preprocessor()),
            ("model",        GradientBoostingRegressor(random_state=42)),
        ]),
        "SVR": Pipeline([
            ("engineer",     HealthFeatureEngineer()),
            ("preprocessor", build_full_preprocessor()),
            ("model",        SVR()),
        ]),
        "ExtraTrees": Pipeline([
            ("engineer",     HealthFeatureEngineer()),
            ("preprocessor", build_full_preprocessor()),
            ("model",        ExtraTreesRegressor(random_state=42, n_jobs=-1)),
        ]),
        "MLP": Pipeline([
            ("engineer",     HealthFeatureEngineer()),
            ("preprocessor", build_full_preprocessor()),
            ("model",        MLPRegressor(
                hidden_layer_sizes=(128, 64, 32),
                activation="relu",
                max_iter=500,
                early_stopping=True,
                validation_fraction=0.1,
                random_state=42,
            )),
        ]),
    }
    return candidates


def build_full_preprocessor():
    """
    Preprocessor that handles all columns output by HealthFeatureEngineer.
    SimpleImputer + StandardScaler applied to every column.
    """
    from sklearn.compose import ColumnTransformer
    from sklearn.impute import SimpleImputer
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import StandardScaler

    numeric_pipe = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler",  StandardScaler()),
    ])

    # "passthrough" with remainder means: apply to ALL columns that come through
    return ColumnTransformer(
        transformers=[("num", numeric_pipe, _all_feature_names())],
        remainder="drop",
        verbose_feature_names_out=False,
    )


def _all_feature_names() -> list:
    """Names of all columns output by HealthFeatureEngineer (base + engineered)."""
    fe = HealthFeatureEngineer()
    return list(fe.get_feature_names_out())


def get_param_grids() -> dict:
    """
    Returns the hyper-parameter search grids for each model.
    Keys must match those in get_candidate_pipelines().
    """
    return {
        "Ridge": {
            "model__alpha": [0.1, 1.0, 10.0, 100.0],
        },
        "RandomForest": {
            "model__n_estimators":      [100, 200],
            "model__max_depth":         [None, 10, 20],
            "model__min_samples_split": [2, 5],
        },
        "GradientBoosting": {
            "model__n_estimators":  [100, 200],
            "model__learning_rate": [0.05, 0.1],
            "model__max_depth":     [3, 5],
        },
        "SVR": {
            "model__C":       [1, 10],
            "model__epsilon": [0.1, 0.5],
        },
        "ExtraTrees": {
            "model__n_estimators": [100, 200],
            "model__max_depth":    [None, 20],
        },
        "MLP": {
            "model__hidden_layer_sizes": [(128, 64), (128, 64, 32)],
            "model__alpha":              [0.0001, 0.001],
        },
    }


if __name__ == "__main__":
    pipelines = get_candidate_pipelines()
    print("Candidate pipelines:")
    for name, pipe in pipelines.items():
        print(f"  {name:20s} → {[s[0] for s in pipe.steps]}")
    print("\n✅  Model registry check passed.")
