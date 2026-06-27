"""
main.py
=======
FastAPI application entry point for the Health Tracking module.
"""

import logging
import uuid
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.db.init_db import init_db
from app.routers.auth import router as auth_router
from app.routers.health import router as health_router

logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    logger.info("Starting Health Tracker API ...")
    await init_db()
    logger.info("Database tables ready.")
    yield
    logger.info("Shutting down.")


def create_app() -> FastAPI:
    app = FastAPI(
        title="Health Tracking API",
        description="""
## Health Tracking Module

Track six daily health metrics per user:

| Metric | Range | Unit |
|---|---|---|
| `sleep_hours` | 0.0 – 24.0 | hours |
| `steps` | 0 – 100 000 | steps/day |
| `calories_consumed` | 0 – 10 000 | kcal |
| `water_intake_ml` | 0 – 10 000 | ml |
| `stress_level` | 1 – 10 | subjective scale |
| `heart_rate_bpm` | 30 – 250 | bpm (resting) |

### Quick start
1. `POST /api/v1/auth/signup` — create account
2. `POST /api/v1/auth/login` — get `access_token`
3. Add header `Authorization: Bearer <access_token>` to all `/health` requests
4. `POST /api/v1/health` — log today's metrics
        """,
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # ── CORS ──────────────────────────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "http://localhost:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Security headers ──────────────────────────────────────────────────────
    @app.middleware("http")
    async def security_headers(request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Request-ID"] = str(uuid.uuid4())
        return response

    # ── Routers ───────────────────────────────────────────────────────────────
    app.include_router(auth_router,   prefix="/api/v1")
    app.include_router(health_router, prefix="/api/v1")

    # ── System endpoints ──────────────────────────────────────────────────────
    @app.get("/health-check", tags=["System"])
    async def health_check() -> dict:
        return {"status": "ok", "version": "1.0.0"}

    @app.get("/", tags=["System"])
    async def root() -> dict:
        return {
            "service": "Health Tracking API",
            "docs": "/docs",
            "health_check": "/health-check",
        }

    # ── Validation error handler ──────────────────────────────────────────────
    @app.exception_handler(RequestValidationError)
    async def validation_handler(request: Request, exc: RequestValidationError):
        errors = []
        for err in exc.errors():
            field = " → ".join(str(loc) for loc in err["loc"] if loc != "body")
            errors.append({
                "field": field or "body",
                "message": err["msg"].replace("Value error, ", ""),
                "type": err["type"],
            })
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"detail": "Validation failed", "errors": errors},
        )

    # ── Unhandled exception handler ───────────────────────────────────────────
    @app.exception_handler(Exception)
    async def unhandled_handler(request: Request, exc: Exception):
        logger.exception("Unhandled error: %s", exc)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "An unexpected error occurred"},
        )

    return app


app = create_app()
