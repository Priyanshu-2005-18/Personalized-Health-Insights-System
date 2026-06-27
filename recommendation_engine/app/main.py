"""
main.py
=======
FastAPI application entry point for the Health Recommendation Engine.
"""

import logging
import uuid
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.routers.recommendations import router as rec_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    app = FastAPI(
        title="Health Recommendation Engine",
        description="""
## Personalised Health Recommendation Engine

A **rule-based recommendation system** that analyses user health metrics
and returns evidence-based, personalised health recommendations.

### Supported metrics
| Metric | Range | Optimal |
|---|---|---|
| `sleep_hours` | 0–24 h | 7–9 h |
| `steps` | 0–100,000 | ≥ 10,000/day |
| `calories` | 0–10,000 kcal | 1,600–2,400 kcal |
| `water_intake_ml` | 0–10,000 ml | 2,000–3,000 ml |
| `stress_level` | 1–10 | 1–3 (low) |
| `heart_rate_bpm` | 30–250 bpm | 55–75 bpm |

### Quick start
```
POST /api/v1/recommendations
{
  "sleep_hours": 5.5,
  "steps": 3200,
  "stress_level": 8,
  "heart_rate_bpm": 95
}
```
        """,
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # ── CORS ──────────────────────────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "http://localhost:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Security + request ID headers ─────────────────────────────────────────
    @app.middleware("http")
    async def add_headers(request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Request-ID"]       = str(uuid.uuid4())
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Cache-Control"]       = "no-store"
        return response

    # ── Routers ───────────────────────────────────────────────────────────────
    app.include_router(rec_router, prefix="/api/v1")

    # ── System endpoints ──────────────────────────────────────────────────────
    @app.get("/", tags=["System"])
    async def root():
        return {
            "service": "Health Recommendation Engine",
            "version": "1.0.0",
            "docs":    "/docs",
            "health":  "/api/v1/recommendations/health",
        }

    @app.get("/health-check", tags=["System"])
    async def health_check():
        return {"status": "ok"}

    # ── Validation error handler ──────────────────────────────────────────────
    @app.exception_handler(RequestValidationError)
    async def validation_handler(request: Request, exc: RequestValidationError):
        errors = []
        for err in exc.errors():
            field = " → ".join(str(loc) for loc in err["loc"] if loc != "body")
            errors.append({
                "field":   field or "body",
                "message": err["msg"].replace("Value error, ", ""),
                "type":    err["type"],
            })
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"detail": "Validation failed", "errors": errors},
        )

    # ── Global exception handler ──────────────────────────────────────────────
    @app.exception_handler(Exception)
    async def global_handler(request: Request, exc: Exception):
        logger.exception("Unhandled error: %s", exc)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Internal server error"},
        )

    return app


app = create_app()
