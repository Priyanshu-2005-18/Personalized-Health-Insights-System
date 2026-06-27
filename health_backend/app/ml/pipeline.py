"""
ML Pipeline — loads trained Scikit-learn models and produces
Recommendation ORM objects ready to be persisted.
"""
import os
import logging
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import numpy as np

logger = logging.getLogger(__name__)

# Lazy-loaded model registry: { model_name: (model, label_encoder) }
_model_registry: Dict[str, object] = {}


def _model_dir() -> Path:
    from app.core.config import settings
    return Path(settings.ML_MODEL_PATH)


def load_models() -> None:
    """Called on startup — loads all .pkl models from ML_MODEL_PATH."""
    import joblib

    model_dir = _model_dir()
    if not model_dir.exists():
        logger.warning("ML model directory %s not found — using rule-based fallback", model_dir)
        return

    for pkl_file in model_dir.glob("*.pkl"):
        name = pkl_file.stem
        try:
            _model_registry[name] = joblib.load(pkl_file)
            logger.info("Loaded ML model: %s", name)
        except Exception as exc:
            logger.error("Failed to load model %s: %s", name, exc)


def _features_to_array(features: Dict[str, float]) -> np.ndarray:
    from app.ml.features import FEATURE_COLUMNS
    return np.array([[features.get(col, 0.0) for col in FEATURE_COLUMNS]])


# ─── Rule-based fallback ──────────────────────────────────────────────────────

_RULE_BASED_RECOMMENDATIONS = [
    {
        "category": "sleep",
        "condition": lambda f: f.get("avg_sleep_duration_min", 480) < 360,
        "priority": "high",
        "title": "Increase your sleep duration",
        "content": (
            "Your average sleep is below 6 hours. Adults need 7–9 hours for optimal "
            "cognitive function, immune health, and metabolic regulation."
        ),
        "actions": [
            "Set a consistent bedtime 30 minutes earlier than usual",
            "Avoid screens for 1 hour before bed",
            "Keep your bedroom temperature between 18–20 °C",
        ],
        "confidence": 0.90,
    },
    {
        "category": "sleep",
        "condition": lambda f: f.get("avg_sleep_quality", 8) < 5,
        "priority": "medium",
        "title": "Improve your sleep quality",
        "content": (
            "Your self-reported sleep quality is low. Poor sleep quality is linked "
            "to increased stress and reduced recovery."
        ),
        "actions": [
            "Try a 10-minute wind-down routine (light stretching or reading)",
            "Limit caffeine after 2 PM",
            "Consider a white-noise app if ambient noise is an issue",
        ],
        "confidence": 0.82,
    },
    {
        "category": "activity",
        "condition": lambda f: f.get("avg_steps", 10000) < 5000,
        "priority": "high",
        "title": "Boost your daily step count",
        "content": (
            "You're averaging fewer than 5 000 steps per day. "
            "Increasing to 7 000–10 000 steps is associated with a 50–70 % lower "
            "risk of all-cause mortality."
        ),
        "actions": [
            "Take a 15-minute walk after each meal",
            "Use stairs instead of lifts",
            "Park farther away or get off one stop early",
        ],
        "confidence": 0.88,
    },
    {
        "category": "activity",
        "condition": lambda f: f.get("activity_frequency", 5) < 3,
        "priority": "medium",
        "title": "Exercise more consistently",
        "content": (
            "You've logged fewer than 3 workouts in the past week. "
            "Aim for at least 150 minutes of moderate-intensity activity per week."
        ),
        "actions": [
            "Schedule 3 × 30-minute workouts this week",
            "Try a workout you enjoy — cycling, swimming, or yoga",
            "Find an accountability partner or class",
        ],
        "confidence": 0.85,
    },
    {
        "category": "hydration",
        "condition": lambda f: f.get("avg_water_ml", 2500) < 1500,
        "priority": "high",
        "title": "Drink more water daily",
        "content": (
            "Your average daily water intake is below 1 500 ml. "
            "Chronic mild dehydration reduces concentration, energy, and kidney function."
        ),
        "actions": [
            "Keep a 500 ml water bottle on your desk at all times",
            "Drink a full glass of water immediately after waking",
            "Set an hourly hydration reminder on your phone",
        ],
        "confidence": 0.92,
    },
    {
        "category": "nutrition",
        "condition": lambda f: f.get("avg_protein_g", 60) < 50,
        "priority": "medium",
        "title": "Increase your daily protein intake",
        "content": (
            "Your average protein intake appears low. "
            "Adequate protein (0.8 g/kg body weight) supports muscle repair, "
            "satiety, and metabolic rate."
        ),
        "actions": [
            "Add a serving of eggs, legumes, or lean meat to each main meal",
            "Consider a Greek yogurt or cottage cheese snack",
            "Track your protein for one week to identify gaps",
        ],
        "confidence": 0.80,
    },
    {
        "category": "stress",
        "condition": lambda f: f.get("avg_stress_level", 3) >= 7,
        "priority": "high",
        "title": "Actively manage elevated stress",
        "content": (
            "Your logged stress levels are consistently high. "
            "Chronic stress raises cortisol, disrupts sleep, and suppresses immune function."
        ),
        "actions": [
            "Practice 5 minutes of box breathing (inhale 4 s, hold 4 s, exhale 4 s)",
            "Identify and schedule at least one stress-reducing activity this week",
            "Consider speaking with a mental health professional",
        ],
        "confidence": 0.87,
    },
    {
        "category": "nutrition",
        "condition": lambda f: f.get("avg_fiber_g", 25) < 15,
        "priority": "low",
        "title": "Increase dietary fibre",
        "content": (
            "Your fibre intake looks low. "
            "A high-fibre diet is linked to improved gut health, lower cholesterol, "
            "and better blood-sugar control."
        ),
        "actions": [
            "Add a serving of vegetables to every meal",
            "Swap white bread/rice for wholegrain alternatives",
            "Snack on fruit, nuts, or seeds instead of processed foods",
        ],
        "confidence": 0.78,
    },
]


def generate_recommendations(features: Dict[str, float]) -> List[dict]:
    """
    Try ML models first; fall back to rule-based engine if models unavailable.
    Returns a list of recommendation dicts.
    """
    if _model_registry:
        return _ml_based_recommendations(features)
    return _rule_based_recommendations(features)


def _rule_based_recommendations(features: Dict[str, float]) -> List[dict]:
    results = []
    for rule in _RULE_BASED_RECOMMENDATIONS:
        if rule["condition"](features):
            results.append({
                "category":         rule["category"],
                "priority":         rule["priority"],
                "title":            rule["title"],
                "content":          rule["content"],
                "actions":          rule["actions"],
                "confidence_score": rule["confidence"],
                "model_version":    "rule-based-v1",
            })
    return results


def _ml_based_recommendations(features: Dict[str, float]) -> List[dict]:
    """Placeholder for trained model inference."""
    X = _features_to_array(features)
    results = []
    # Example: each model predicts a risk flag; map to recommendation
    for model_name, model in _model_registry.items():
        try:
            proba = model.predict_proba(X)[0]  # [neg_prob, pos_prob]
            if proba[1] > 0.55:
                results.append({
                    "category":         _model_to_category(model_name),
                    "priority":         _proba_to_priority(proba[1]),
                    "title":            f"Health alert: {model_name.replace('_', ' ')}",
                    "content":          "Our model detected a pattern that may need your attention.",
                    "actions":          [],
                    "confidence_score": round(float(proba[1]), 3),
                    "model_version":    f"sklearn-{model_name}-v1",
                })
        except Exception as exc:
            logger.warning("Model %s inference failed: %s", model_name, exc)
    # Always augment ML results with rule-based ones for actionability
    rule_results = _rule_based_recommendations(features)
    seen_categories = {r["category"] for r in results}
    for r in rule_results:
        if r["category"] not in seen_categories:
            results.append(r)
    return results


def _model_to_category(model_name: str) -> str:
    mapping = {
        "sleep_model": "sleep",
        "activity_model": "activity",
        "nutrition_model": "nutrition",
        "stress_model": "stress",
    }
    return mapping.get(model_name, "general")


def _proba_to_priority(proba: float) -> str:
    if proba >= 0.80:
        return "high"
    if proba >= 0.60:
        return "medium"
    return "low"
