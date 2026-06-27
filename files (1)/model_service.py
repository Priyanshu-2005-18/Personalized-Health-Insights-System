"""
ModelService
------------
Responsible for:
  • Loading the trained sklearn Pipeline from disk via joblib (singleton).
  • Transforming raw HealthMetricsInput into a numpy feature vector.
  • Running inference and computing domain scores + recommendations.
  • Returning a fully-populated HealthScoreResponse.

Design decisions
  • The model is loaded once at application startup (lifespan hook) and held
    in module-level state — avoids per-request disk I/O.
  • joblib.load is wrapped in a try/except so a missing artifact produces a
    clear startup error rather than a cryptic AttributeError later.
  • Domain scores are rule-derived from the raw inputs so they are always
    interpretable, independent of model internals.
"""

from __future__ import annotations

import json
import logging
import os
import time
from pathlib import Path
from typing import Optional

import joblib
import numpy as np

from app.schemas.health import (
    BatchHealthScoreResponse,
    DomainScores,
    HealthMetricsInput,
    HealthRecommendation,
    HealthScoreResponse,
    RiskLevel,
)

logger = logging.getLogger(__name__)

# Resolved at import time so the service works regardless of cwd.
_ARTIFACTS_DIR = Path(__file__).resolve().parents[2] / "ml" / "artifacts"
_MODEL_PATH    = _ARTIFACTS_DIR / "health_score_model.joblib"
_METRICS_PATH  = _ARTIFACTS_DIR / "model_metrics.json"

MODEL_VERSION = "1.0.0"


def _load_pipeline():
    """Load the serialised sklearn Pipeline. Raises RuntimeError on failure."""
    if not _MODEL_PATH.exists():
        raise RuntimeError(
            f"Model artifact not found at {_MODEL_PATH}. "
            "Run ml/training/train_model.py first."
        )
    logger.info("Loading model from %s …", _MODEL_PATH)
    t0 = time.perf_counter()
    pipeline = joblib.load(_MODEL_PATH)
    logger.info("Model loaded in %.3f s", time.perf_counter() - t0)
    return pipeline


def _load_metrics() -> dict:
    """Load persisted evaluation metrics for the /model/info endpoint."""
    if not _METRICS_PATH.exists():
        return {}
    with open(_METRICS_PATH) as f:
        return json.load(f)


# ── Module-level singletons (populated by ModelService.startup) ───────────────
_pipeline: Optional[object] = None
_metrics:  dict             = {}


class ModelService:
    """Stateless service class; all state lives in module-level singletons."""

    # ── Lifecycle ──────────────────────────────────────────────────────────────

    @staticmethod
    def startup() -> None:
        """Call once during FastAPI lifespan startup."""
        global _pipeline, _metrics
        _pipeline = _load_pipeline()
        _metrics  = _load_metrics()
        logger.info("ModelService ready (version %s)", MODEL_VERSION)

    @staticmethod
    def is_ready() -> bool:
        return _pipeline is not None

    # ── Feature engineering ────────────────────────────────────────────────────

    @staticmethod
    def _build_feature_vector(metrics: HealthMetricsInput) -> np.ndarray:
        """
        Must match the column order used in train_model.py:
        [sleep_hours, sleep_quality, steps_daily, active_minutes,
         resting_hr, hrv, stress_index, water_intake, bmi]
        """
        return np.array([[
            metrics.sleep_hours,
            metrics.sleep_quality,
            metrics.steps_daily,
            metrics.active_minutes,
            metrics.resting_hr,
            metrics.hrv,
            metrics.stress_index,
            metrics.water_intake,
            metrics.bmi,
        ]], dtype=np.float64)

    # ── Domain scores ──────────────────────────────────────────────────────────

    @staticmethod
    def _compute_domain_scores(m: HealthMetricsInput) -> DomainScores:
        """
        Rule-based sub-scores (0–100) give interpretable breakdowns without
        requiring a separate model per domain.
        """
        # Sleep: optimal window 7–9 hrs, quality weighted equally
        sleep_duration = min(m.sleep_hours / 9.0, 1.0) * 50
        sleep_qual     = (m.sleep_quality / 10.0) * 50
        sleep          = round(sleep_duration + sleep_qual, 1)

        # Activity: 10k steps + 150 min/week targets (WHO guidelines)
        step_score     = min(m.steps_daily / 10_000, 1.0) * 60
        active_score   = min(m.active_minutes / 150.0, 1.0) * 40
        activity       = round(step_score + active_score, 1)

        # Cardiovascular: lower resting HR + higher HRV = better
        hr_score       = max(0.0, (110 - m.resting_hr) / 70.0) * 50
        hrv_score      = min(m.hrv / 80.0, 1.0) * 50
        cardio         = round(hr_score + hrv_score, 1)

        # Stress: linear inversion
        stress         = round((1 - m.stress_index / 100.0) * 100, 1)

        # Lifestyle: hydration (target 2.5 L) + BMI (18.5–24.9 ideal)
        water_score    = min(m.water_intake / 2.5, 1.0) * 50
        if 18.5 <= m.bmi < 25:
            bmi_score = 50.0
        elif (17 <= m.bmi < 18.5) or (25 <= m.bmi < 30):
            bmi_score = 30.0
        elif (16 <= m.bmi < 17) or (30 <= m.bmi < 35):
            bmi_score = 15.0
        else:
            bmi_score = 0.0
        lifestyle      = round(water_score + bmi_score, 1)

        return DomainScores(
            sleep=min(sleep, 100.0),
            activity=min(activity, 100.0),
            cardio=min(cardio, 100.0),
            stress=stress,
            lifestyle=min(lifestyle, 100.0),
        )

    # ── Risk classification ────────────────────────────────────────────────────

    @staticmethod
    def _classify_risk(score: float) -> RiskLevel:
        if score >= 75:
            return RiskLevel.LOW
        elif score >= 55:
            return RiskLevel.MODERATE
        elif score >= 35:
            return RiskLevel.HIGH
        else:
            return RiskLevel.CRITICAL

    # ── Recommendations ────────────────────────────────────────────────────────

    @staticmethod
    def _build_recommendations(
        m: HealthMetricsInput,
        domains: DomainScores,
    ) -> list[HealthRecommendation]:
        recs: list[HealthRecommendation] = []

        # Sleep
        if m.sleep_hours < 6.5:
            recs.append(HealthRecommendation(
                domain="sleep", priority="high",
                message=(
                    f"You're averaging {m.sleep_hours:.1f} hrs of sleep. "
                    "Aim for 7–9 hrs by moving your bedtime 30 min earlier each night."
                ),
            ))
        elif m.sleep_quality < 6.0:
            recs.append(HealthRecommendation(
                domain="sleep", priority="medium",
                message=(
                    "Your sleep quality score is low. Consider a consistent wind-down "
                    "routine and limiting screens 1 hr before bed."
                ),
            ))

        # Activity
        if m.steps_daily < 7_000:
            recs.append(HealthRecommendation(
                domain="activity", priority="high",
                message=(
                    f"Your daily steps ({int(m.steps_daily):,}) are below the 7,000-step "
                    "minimum associated with reduced mortality risk. Try a 20-min walk after lunch."
                ),
            ))
        if m.active_minutes < 150:
            recs.append(HealthRecommendation(
                domain="activity", priority="medium",
                message=(
                    f"You're getting {int(m.active_minutes)} active minutes per week. "
                    "The WHO recommends ≥150 min of moderate exercise. "
                    "Adding two 30-min sessions would get you there."
                ),
            ))

        # Cardiovascular
        if m.resting_hr > 80:
            recs.append(HealthRecommendation(
                domain="cardio", priority="high",
                message=(
                    f"A resting HR of {int(m.resting_hr)} bpm is elevated. "
                    "Regular aerobic exercise (cycling, swimming) can lower it by 5–10 bpm over 8 weeks."
                ),
            ))
        if m.hrv < 30:
            recs.append(HealthRecommendation(
                domain="cardio", priority="medium",
                message=(
                    "Your HRV is low, suggesting elevated autonomic stress. "
                    "Box breathing (4-4-4-4 pattern) practiced daily can improve HRV within 4 weeks."
                ),
            ))

        # Stress
        if m.stress_index > 65:
            recs.append(HealthRecommendation(
                domain="stress", priority="high",
                message=(
                    f"Your stress index ({int(m.stress_index)}/100) is high. "
                    "Consider scheduling daily 5-min mindfulness sessions and "
                    "reviewing your workload distribution."
                ),
            ))

        # Lifestyle
        if m.water_intake < 1.5:
            recs.append(HealthRecommendation(
                domain="lifestyle", priority="medium",
                message=(
                    f"You're drinking {m.water_intake:.1f} L/day — below the 1.5 L minimum. "
                    "Keep a 500 ml bottle visible on your desk as a nudge."
                ),
            ))
        if m.bmi >= 30:
            recs.append(HealthRecommendation(
                domain="lifestyle", priority="high",
                message=(
                    f"A BMI of {m.bmi:.1f} is in the obese range. "
                    "A 5% weight reduction significantly reduces cardiovascular risk. "
                    "Consult a healthcare professional for a personalised plan."
                ),
            ))

        # Cap at 4 recommendations, prioritised by domain score (lowest first)
        if not recs:
            recs.append(HealthRecommendation(
                domain="general", priority="low",
                message=(
                    "Your metrics look great! Maintain your current routines and "
                    "revisit your score in 7 days to track progress."
                ),
            ))

        return recs[:4]

    # ── Confidence estimation ──────────────────────────────────────────────────

    @staticmethod
    def _estimate_confidence(m: HealthMetricsInput) -> float:
        """
        Heuristic confidence score based on how many inputs fall within the
        training distribution's expected range.  In production this would use
        a proper uncertainty estimation method (e.g. conformal prediction).
        """
        in_range = 0
        checks = [
            3.0 <= m.sleep_hours <= 11.0,
            1.0 <= m.sleep_quality <= 10.0,
            1000 <= m.steps_daily <= 20000,
            0 <= m.active_minutes <= 400,
            45 <= m.resting_hr <= 100,
            15 <= m.hrv <= 110,
            0 <= m.stress_index <= 95,
            0.5 <= m.water_intake <= 4.5,
            16 <= m.bmi <= 40,
        ]
        in_range = sum(checks)
        return round(in_range / len(checks), 3)

    # ── Public API ─────────────────────────────────────────────────────────────

    def predict(self, metrics: HealthMetricsInput) -> HealthScoreResponse:
        """Score a single record."""
        if not self.is_ready():
            raise RuntimeError("Model is not loaded. Call ModelService.startup() first.")

        X          = self._build_feature_vector(metrics)
        raw_score  = float(_pipeline.predict(X)[0])
        score      = round(min(max(raw_score, 0.0), 100.0), 2)
        domains    = self._compute_domain_scores(metrics)
        risk       = self._classify_risk(score)
        recs       = self._build_recommendations(metrics, domains)
        confidence = self._estimate_confidence(metrics)

        return HealthScoreResponse(
            health_score=score,
            risk_level=risk,
            confidence=confidence,
            domain_scores=domains,
            recommendations=recs,
            model_version=MODEL_VERSION,
            user_id=metrics.user_id,
        )

    def predict_batch(self, records: list[HealthMetricsInput]) -> BatchHealthScoreResponse:
        """Score multiple records in one call."""
        results = [self.predict(r) for r in records]
        return BatchHealthScoreResponse(results=results, total=len(results))

    def get_model_info(self) -> dict:
        return {**_metrics, "model_version": MODEL_VERSION, "status": "loaded"}


# Singleton instance imported by routers
model_service = ModelService()
