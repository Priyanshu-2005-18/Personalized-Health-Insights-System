"""
config.py
=========
Single source of truth for every path, constant, and hyper-parameter
used across the pipeline. Edit here — never scatter magic numbers.
"""
from pathlib import Path

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE_DIR    = Path(__file__).parent
DATA_DIR    = BASE_DIR / "data"
MODEL_DIR   = BASE_DIR / "models"
REPORT_DIR  = BASE_DIR / "reports"

RAW_CSV     = DATA_DIR   / "health_data.csv"
MODEL_PATH  = MODEL_DIR  / "health_score_model.joblib"
PIPELINE_PATH = MODEL_DIR / "full_pipeline.joblib"

# ── Features ──────────────────────────────────────────────────────────────────
FEATURES = [
    "sleep_hours",
    "steps",
    "calories",
    "water_intake_ml",
    "stress_level",
    "heart_rate_bpm",
]
TARGET = "health_score"

# ── Preprocessing ─────────────────────────────────────────────────────────────
RANDOM_STATE = 42
TEST_SIZE    = 0.20
VAL_SIZE     = 0.10   # fraction of training set used for validation

# ── Feature engineering ───────────────────────────────────────────────────────
# Optimal reference ranges (used to compute deviation features)
OPTIMAL_RANGES = {
    "sleep_hours":     (7.0,   9.0),
    "steps":           (10_000, 10_000),  # target = 10 000+
    "calories":        (1_800,  2_200),
    "water_intake_ml": (2_500,  3_000),
    "stress_level":    (1,      3),       # low stress is optimal
    "heart_rate_bpm":  (60,     80),
}

# ── Model hyper-parameters (GridSearchCV search space) ────────────────────────
PARAM_GRIDS = {
    "RandomForest": {
        "model__n_estimators":  [100, 200, 300],
        "model__max_depth":     [None, 10, 20],
        "model__min_samples_split": [2, 5],
    },
    "GradientBoosting": {
        "model__n_estimators":  [100, 200],
        "model__learning_rate": [0.05, 0.1, 0.2],
        "model__max_depth":     [3, 5],
    },
    "Ridge": {
        "model__alpha": [0.1, 1.0, 10.0, 100.0],
    },
    "SVR": {
        "model__C":       [1, 10, 100],
        "model__epsilon": [0.1, 0.5],
        "model__kernel":  ["rbf"],
    },
}

# ── Evaluation ────────────────────────────────────────────────────────────────
CV_FOLDS = 5
SCORING  = "neg_mean_squared_error"   # used inside GridSearchCV
