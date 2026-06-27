"""
api/v1/predict.py
=================
Health Score Prediction endpoints.

Routes
------
POST /api/v1/predict            — single prediction (authenticated)
POST /api/v1/predict/batch      — batch predictions (authenticated)
POST /api/v1/predict/anonymous  — single prediction, no auth required
GET  /api/v1/predict/model-info — model metadata (authenticated)
"""
from __future__ import annotations

import math
from typing import Any, Dict

from fastapi import APIRouter, Depends, status

from app.core.deps import CurrentUser, get_current_user
from app.ml.predictor import HealthScorePredictor, FEATURES
from app.schemas.predict import (
    BatchHealthMetricsInput,
    BatchHealthScoreResponse,
    HealthMetricsInput,
    HealthScoreResponse,
    ModelInfoResponse,
)

router = APIRouter()


# ── Helper ────────────────────────────────────────────────────────────────────

def _to_kwargs(payload: HealthMetricsInput) -> Dict[str, Any]:
    """Convert Pydantic payload to keyword dict, replacing None with NaN."""
    import math
    return {
        k: (v if v is not None else math.nan)
        for k, v in payload.model_dump().items()
    }


def _sanitise_result(result: dict) -> dict:
    """Replace NaN / inf floats with None so JSON serialisation works."""
    def fix(v: Any) -> Any:
        if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
            return None
        if isinstance(v, dict):
            return {k2: fix(v2) for k2, v2 in v.items()}
        if isinstance(v, list):
            return [fix(i) for i in v]
        return v

    return {k: fix(v) for k, v in result.items()}


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post(
    "",
    response_model=HealthScoreResponse,
    status_code=status.HTTP_200_OK,
    summary="Predict health score from personal health metrics",
    description=(
        "Submit your health metrics and receive an AI-powered health score (0–100), "
        "a letter grade, per-metric sub-scores, and personalised feedback. "
        "Requires authentication."
    ),
)
async def predict_health_score(
    payload: HealthMetricsInput,
    current_user: CurrentUser,
) -> HealthScoreResponse:
    """
    **Predict health score (authenticated)**

    | Field            | Type  | Range / Unit          |
    |------------------|-------|-----------------------|
    | sleep_hours      | float | 0–24 h                |
    | steps            | float | steps/day             |
    | calories         | float | kcal/day              |
    | water_intake_ml  | float | ml/day                |
    | stress_level     | float | 1–10                  |
    | heart_rate_bpm   | float | bpm                   |

    All fields are **optional** — missing values use pipeline imputation or
    neutral defaults in the rule-based fallback.
    """
    predictor = HealthScorePredictor.get_instance()
    kwargs = _to_kwargs(payload)
    result = predictor.predict_single(**kwargs)
    return HealthScoreResponse(**_sanitise_result(result))


@router.post(
    "/batch",
    response_model=BatchHealthScoreResponse,
    status_code=status.HTTP_200_OK,
    summary="Batch-predict health scores for multiple records",
    description=(
        "Submit up to 50 health metric records and receive health scores for each. "
        "Useful for historical analysis or comparing multiple users."
    ),
)
async def predict_health_score_batch(
    payload: BatchHealthMetricsInput,
    current_user: CurrentUser,
) -> BatchHealthScoreResponse:
    """
    **Batch prediction (authenticated)**

    Accepts a JSON body with a `records` array (1–50 items), each following
    the same structure as the single-predict endpoint.
    """
    predictor = HealthScorePredictor.get_instance()
    records = [_to_kwargs(r) for r in payload.records]
    results = predictor.predict_batch(records)
    sanitised = [_sanitise_result(r) for r in results]
    predictions = [HealthScoreResponse(**r) for r in sanitised]

    model_used = sanitised[0]["model_used"] if sanitised else "unknown"
    return BatchHealthScoreResponse(
        predictions=predictions,
        count=len(predictions),
        model_used=model_used,
    )


@router.post(
    "/anonymous",
    response_model=HealthScoreResponse,
    status_code=status.HTTP_200_OK,
    summary="Predict health score without authentication",
    description=(
        "Public endpoint — no login required. "
        "Useful for demos, onboarding previews, or calculator widgets."
    ),
)
async def predict_health_score_anonymous(
    payload: HealthMetricsInput,
) -> HealthScoreResponse:
    """
    **Predict health score (no auth)**

    Same as the authenticated endpoint but accessible without a JWT token.
    Rate-limited by the API gateway in production.
    """
    predictor = HealthScorePredictor.get_instance()
    kwargs = _to_kwargs(payload)
    result = predictor.predict_single(**kwargs)
    return HealthScoreResponse(**_sanitise_result(result))


@router.get(
    "/model-info",
    response_model=ModelInfoResponse,
    status_code=status.HTTP_200_OK,
    summary="Get ML model status and metadata",
)
async def get_model_info(
    current_user: CurrentUser,
) -> ModelInfoResponse:
    """
    Returns whether the trained model is loaded, which feature columns it
    expects, and the grade-to-score thresholds used.
    """
    predictor = HealthScorePredictor.get_instance()
    return ModelInfoResponse(
        model_loaded=predictor.is_loaded,
        model_path=str(predictor._model_path),
        features=FEATURES,
        feature_count=len(FEATURES),
        grade_thresholds={"A": 85, "B": 70, "C": 55, "D": 40, "F": 0},
    )
