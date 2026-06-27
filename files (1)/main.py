"""
FastAPI application entry point.

Startup sequence
----------------
1. lifespan loads the ML model via ModelService.startup()
2. Middleware stack: CORS → logging
3. Routers: /api/v1/health prefix

Run locally
-----------
    uvicorn app.main:app --reload --port 8000
"""

import logging
import logging.config
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from app.middleware.logging import LoggingMiddleware
from app.routers import health as health_router
from app.services.model_service import model_service

# ── Logging config ─────────────────────────────────────────────────────────────
logging.config.dictConfig({
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "default",
        }
    },
    "root": {"level": "INFO", "handlers": ["console"]},
})

logger = logging.getLogger(__name__)


# ── Lifespan ───────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load the ML model before accepting requests; clean up on shutdown."""
    logger.info("=== Health Insights API starting up ===")
    try:
        model_service.startup()
        logger.info("ML model loaded successfully.")
    except RuntimeError as exc:
        logger.critical("Failed to load ML model: %s", exc)
        # Don't raise — the /health endpoint will report 503 until the artifact exists.
    yield
    logger.info("=== Health Insights API shutting down ===")


# ── App factory ────────────────────────────────────────────────────────────────
def create_app() -> FastAPI:
    app = FastAPI(
        title="Health Insights API",
        description=(
            "ML-powered API that accepts personal health metrics and returns "
            "a personalised health score, risk classification, and actionable "
            "recommendations. Part of the Personalised Health Insights System."
        ),
        version="1.0.0",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    # ── Middleware ─────────────────────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],          # Tighten in production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(LoggingMiddleware)

    # ── Exception handlers ─────────────────────────────────────────────────────
    @app.exception_handler(ValidationError)
    async def validation_exception_handler(request: Request, exc: ValidationError):
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"detail": exc.errors(), "error_code": "VALIDATION_ERROR"},
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception):
        logger.exception("Unhandled exception on %s %s", request.method, request.url.path)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "An internal error occurred.", "error_code": "INTERNAL_ERROR"},
        )

    # ── Routers ────────────────────────────────────────────────────────────────
    app.include_router(health_router.router, prefix="/api/v1", tags=["Health Score"])

    # ── Root redirect ──────────────────────────────────────────────────────────
    @app.get("/", include_in_schema=False)
    async def root():
        return JSONResponse({"message": "Health Insights API v1.0.0 — see /docs"})

    return app


app = create_app()
