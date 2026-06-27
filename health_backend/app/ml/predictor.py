"""
predictor.py
============
Loads the trained scikit-learn full_pipeline.joblib and exposes a
clean interface for the FastAPI endpoints.

Features expected (from health_ml/config.py):
    sleep_hours, steps, calories, water_intake_ml, stress_level, heart_rate_bpm

The saved pipeline already contains:
    HealthFeatureEngineer → StandardScaler → <best model (Ridge/RF/GB/SVR)>

So we just pass raw feature values — no manual preprocessing needed.
"""
from __future__ import annotations

import logging
import threading
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# ── Feature definition (mirrors health_ml/config.py) ─────────────────────────
FEATURES: List[str] = [
    "sleep_hours",
    "steps",
    "calories",
    "water_intake_ml",
    "stress_level",
    "heart_rate_bpm",
]

# Grade thresholds (matches health_ml/predict.py)
_GRADE_THRESHOLDS = [
    (85, "A", "Excellent"),
    (70, "B", "Good"),
    (55, "C", "Average"),
    (40, "D", "Below Average"),
    (0,  "F", "Poor"),
]

# Optimal ranges for per-metric feedback
_OPTIMAL_RANGES: Dict[str, tuple] = {
    "sleep_hours":     (7.0, 9.0),
    "steps":           (8000, 12000),
    "calories":        (1800, 2200),
    "water_intake_ml": (2000, 3500),
    "stress_level":    (1, 3),
    "heart_rate_bpm":  (60, 80),
}

_METRIC_LABELS: Dict[str, str] = {
    "sleep_hours":     "Sleep Duration",
    "steps":           "Daily Steps",
    "calories":        "Caloric Intake",
    "water_intake_ml": "Water Intake",
    "stress_level":    "Stress Level",
    "heart_rate_bpm":  "Heart Rate",
}


class HealthScorePredictor:
    """
    Thread-safe singleton that wraps the trained joblib pipeline.

    Usage
    -----
    predictor = HealthScorePredictor.get_instance()
    result    = predictor.predict_single(sleep_hours=7.5, steps=9000, ...)
    """

    _instance: Optional["HealthScorePredictor"] = None
    _lock = threading.Lock()

    def __init__(self, model_path: Path) -> None:
        self._model_path = model_path
        self._pipeline: Any = None
        self._loaded: bool = False

    # ── Singleton factory ─────────────────────────────────────────────────────

    @classmethod
    def get_instance(cls) -> "HealthScorePredictor":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    path = _resolve_model_path()
                    cls._instance = cls(path)
        return cls._instance

    # ── Load ──────────────────────────────────────────────────────────────────

    def load(self) -> None:
        """Load (or reload) the joblib pipeline from disk."""
        import sys
        import joblib

        if not self._model_path.exists():
            logger.warning(
                "ML model not found at %s — health-score predictions will use "
                "the rule-based fallback.",
                self._model_path,
            )
            self._loaded = False
            return

        try:
            # Register local feature engineering module into sys.modules to satisfy joblib
            import app.ml.feature_engineering as fe
            sys.modules['feature_engineering'] = fe

            self._pipeline = joblib.load(self._model_path)
            self._loaded = True
            size_kb = self._model_path.stat().st_size / 1024
            logger.info(
                "Health-score model loaded from %s (%.1f KB)", self._model_path, size_kb
            )
        except Exception as exc:
            logger.error("Failed to load health-score model: %s", exc)
            self._loaded = False


    @property
    def is_loaded(self) -> bool:
        return self._loaded

    # ── Predict ───────────────────────────────────────────────────────────────

    def predict_single(self, **kwargs: float) -> Dict[str, Any]:
        """
        Predict health score for a single set of health metrics.

        Parameters
        ----------
        sleep_hours     : hours of sleep (e.g. 7.5)
        steps           : daily step count (e.g. 9000)
        calories        : daily caloric intake kcal (e.g. 2100)
        water_intake_ml : water consumed in ml (e.g. 2500)
        stress_level    : 1–10 scale (1 = no stress, 10 = extreme)
        heart_rate_bpm  : resting heart rate in bpm (e.g. 68)

        Returns
        -------
        dict with keys: health_score, grade, letter, category_scores,
                        feedback, model_used
        """
        row = {f: float(kwargs.get(f, np.nan)) for f in FEATURES}
        df = pd.DataFrame([row])

        if self._loaded:
            try:
                raw_score = float(self._pipeline.predict(df)[0])
                score = float(np.clip(round(raw_score, 2), 0.0, 100.0))
                model_used = "ml_pipeline"
            except Exception as exc:
                logger.warning("ML pipeline inference failed (%s) — falling back", exc)
                score = _rule_based_score(row)
                model_used = "rule_based_fallback"
        else:
            score = _rule_based_score(row)
            model_used = "rule_based_fallback"

        letter, label = _grade(score)
        category_scores = _per_metric_scores(row)
        feedback = _generate_feedback(row, score)

        return {
            "health_score":      score,
            "grade":             f"{letter} — {label}",
            "letter":            letter,
            "label":             label,
            "category_scores":   category_scores,
            "feedback":          feedback,
            "model_used":        model_used,
            "inputs":            row,
        }

    def predict_batch(self, records: List[Dict[str, float]]) -> List[Dict[str, Any]]:
        """
        Predict health scores for a list of records.

        Parameters
        ----------
        records : list of dicts, each with the same keys as predict_single()

        Returns
        -------
        list of result dicts (same structure as predict_single())
        """
        if not records:
            return []

        rows = [{f: float(r.get(f, np.nan)) for f in FEATURES} for r in records]
        df = pd.DataFrame(rows)

        if self._loaded:
            try:
                raw_scores = self._pipeline.predict(df)
                scores = np.clip(np.round(raw_scores, 2), 0.0, 100.0).tolist()
                model_used = "ml_pipeline"
            except Exception as exc:
                logger.warning("Batch ML inference failed (%s) — falling back", exc)
                scores = [_rule_based_score(r) for r in rows]
                model_used = "rule_based_fallback"
        else:
            scores = [_rule_based_score(r) for r in rows]
            model_used = "rule_based_fallback"

        results = []
        for row, score in zip(rows, scores):
            letter, label = _grade(score)
            results.append({
                "health_score":    float(score),
                "grade":           f"{letter} — {label}",
                "letter":          letter,
                "label":           label,
                "category_scores": _per_metric_scores(row),
                "feedback":        _generate_feedback(row, score),
                "model_used":      model_used,
                "inputs":          row,
            })
        return results


# ── Helpers ───────────────────────────────────────────────────────────────────

def _resolve_model_path() -> Path:
    """Determine the model path — prefers backend's own copy."""
    from app.core.config import settings
    # backend's own models/ folder
    own = Path(__file__).parent / "models" / "full_pipeline.joblib"
    if own.exists():
        return own
    # configured path fallback
    return Path(settings.ML_MODEL_PATH) / "full_pipeline.joblib"


def _grade(score: float) -> tuple[str, str]:
    for threshold, letter, label in _GRADE_THRESHOLDS:
        if score >= threshold:
            return letter, label
    return "F", "Poor"


def _per_metric_scores(row: Dict[str, float]) -> Dict[str, float]:
    """Return a 0–100 score for each individual metric."""
    scores: Dict[str, float] = {}
    for feature, (lo, hi) in _OPTIMAL_RANGES.items():
        val = row.get(feature, np.nan)
        if np.isnan(val):
            scores[feature] = 50.0  # neutral when missing
            continue
        if feature == "stress_level":
            # Lower is better → invert
            scores[feature] = round(float(np.clip((10 - val) / 9 * 100, 0, 100)), 1)
        elif val < lo:
            scores[feature] = round(float(max(0.0, 100 * val / lo)), 1)
        elif val > hi:
            # Beyond high end — penalise proportionally
            scores[feature] = round(float(max(0.0, 100 - (val - hi) / hi * 50)), 1)
        else:
            scores[feature] = 100.0
    return scores


def _rule_based_score(row: Dict[str, float]) -> float:
    """Simple weighted rule-based health score when ML model isn't available."""
    weights = {
        "sleep_hours":     0.25,
        "steps":           0.20,
        "calories":        0.15,
        "water_intake_ml": 0.15,
        "stress_level":    0.15,
        "heart_rate_bpm":  0.10,
    }
    per = _per_metric_scores(row)
    total = sum(per.get(f, 50.0) * w for f, w in weights.items())
    return round(float(np.clip(total, 0.0, 100.0)), 2)


def _generate_feedback(row: Dict[str, float], score: float) -> List[Dict[str, str]]:
    """Generate brief per-metric feedback messages."""
    feedback = []
    tips = {
        "sleep_hours": {
            "low":  "You're sleeping less than the recommended 7–9 hours. Try a consistent bedtime.",
            "high": "Sleeping more than 9 hours may indicate fatigue or an underlying issue.",
            "ok":   "Your sleep duration is within the optimal range. Keep it up!",
        },
        "steps": {
            "low":  "Fewer than 8 000 steps daily increases sedentary risk. Aim for 10 000.",
            "high": "Excellent step count! You're well above the daily activity target.",
            "ok":   "Good activity level — you're hitting your step target consistently.",
        },
        "calories": {
            "low":  "Your caloric intake seems low. Ensure you're fuelling your body adequately.",
            "high": "High caloric intake may lead to weight gain over time. Consider portion control.",
            "ok":   "Your caloric intake is well-balanced.",
        },
        "water_intake_ml": {
            "low":  "You're under-hydrated. Aim for at least 2 000–2 500 ml of water daily.",
            "high": "Great hydration! Staying well-hydrated supports all body systems.",
            "ok":   "Your hydration is in an ideal range.",
        },
        "stress_level": {
            "low":  "Low stress — fantastic! Maintaining this supports long-term wellbeing.",
            "high": "High stress levels detected. Consider mindfulness, exercise, or speaking to someone.",
            "ok":   "Your stress level is manageable. Keep practising healthy coping strategies.",
        },
        "heart_rate_bpm": {
            "low":  "Resting heart rate below 60 bpm can be normal for athletes but consult a doctor if unexpected.",
            "high": "An elevated resting heart rate may signal stress, dehydration, or a health issue.",
            "ok":   "Your resting heart rate is in the healthy range.",
        },
    }

    for feature, (lo, hi) in _OPTIMAL_RANGES.items():
        val = row.get(feature, np.nan)
        if np.isnan(val):
            continue
        label = _METRIC_LABELS.get(feature, feature)
        if feature == "stress_level":
            status = "high" if val > hi else ("ok" if val <= hi else "low")
        elif val < lo:
            status = "low"
        elif val > hi:
            status = "high"
        else:
            status = "ok"

        feedback.append({
            "metric":  label,
            "status":  status,
            "message": tips[feature][status],
        })

    return feedback
