"""
Health score router
-------------------
POST /predict          — single prediction
POST /predict/batch    — batch prediction (up to 50 records)
GET  /model/info       — model metadata and evaluation metrics
GET  /health           — liveness probe
"""

import logging
import time
from fastapi import APIRouter, HTTPException, Request, status
from fastapi.responses import JSONResponse

from app.schemas.health import (
    BatchHealthMetricsInput,
    BatchHealthScoreResponse,
    HealthMetricsInput,
    HealthScoreResponse,
    ModelInfoResponse,
)
from app.services.model_service import model_service

logger = logging.getLogger(__name__)
router = APIRouter()


# ── Helpers ────────────────────────────────────────────────────────────────────

def _require_model() -> None:
    if not model_service.is_ready():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Model is not loaded. Service is starting up — retry in a moment.",
        )


# ── Endpoints ──────────────────────────────────────────────────────────────────

@router.post(
    "/predict",
    response_model=HealthScoreResponse,
    status_code=status.HTTP_200_OK,
    summary="Predict health score",
    description=(
        "Accept a set of personal health metrics and return a personalised "
        "health score (0–100), risk classification, domain breakdown, and "
        "actionable recommendations."
    ),
    responses={
        422: {"description": "Validation error — one or more fields are out of range."},
        503: {"description": "Model not loaded yet."},
    },
)
async def predict_health_score(
    payload: HealthMetricsInput,
    request: Request,
) -> HealthScoreResponse:
    _require_model()
    t0 = time.perf_counter()

    try:
        result = model_service.predict(payload)
    except Exception as exc:
        logger.exception("Prediction failed for user_id=%s", payload.user_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Prediction error: {exc}",
        ) from exc

    elapsed_ms = round((time.perf_counter() - t0) * 1000, 2)
    logger.info(
        "predict | user=%s score=%.2f risk=%s latency=%sms",
        payload.user_id, result.health_score, result.risk_level, elapsed_ms,
    )
    return result


@router.post(
    "/predict/batch",
    response_model=BatchHealthScoreResponse,
    status_code=status.HTTP_200_OK,
    summary="Batch predict health scores",
    description="Score up to 50 health metric records in a single request.",
    responses={
        422: {"description": "Validation error in one or more records."},
        503: {"description": "Model not loaded yet."},
    },
)
async def predict_batch(
    payload: BatchHealthMetricsInput,
    request: Request,
) -> BatchHealthScoreResponse:
    _require_model()
    t0 = time.perf_counter()

    try:
        result = model_service.predict_batch(payload.records)
    except Exception as exc:
        logger.exception("Batch prediction failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Batch prediction error: {exc}",
        ) from exc

    elapsed_ms = round((time.perf_counter() - t0) * 1000, 2)
    logger.info("batch_predict | n=%d latency=%sms", result.total, elapsed_ms)
    return result


@router.get(
    "/model/info",
    response_model=ModelInfoResponse,
    summary="Model metadata",
    description="Returns the loaded model's version, feature names, and evaluation metrics.",
)
async def model_info() -> ModelInfoResponse:
    _require_model()
    info = model_service.get_model_info()
    return ModelInfoResponse(**info)


@router.get(
    "/health",
    summary="Liveness probe",
    description="Returns 200 when the service is up and the model is loaded.",
)
async def health_check() -> JSONResponse:
    if not model_service.is_ready():
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "starting", "model_loaded": False},
        )
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"status": "ok", "model_loaded": True},
    )
