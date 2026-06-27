"""
main.py
=======
FastAPI application entry point.

Responsibilities:
  - Create the FastAPI instance via create_app()
  - Register lifespan (startup / shutdown hooks)
  - Add CORS, security headers, and request-ID middleware
  - Mount all routers
  - Install global exception handlers
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
from app.routers.protected import router as protected_router

logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
#  Lifespan (replaces deprecated @app.on_event)
# ─────────────────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    logger.info("⚡  Starting JWT Auth API ...")
    await init_db()
    logger.info("✅  Database tables ready.")
    yield
    logger.info("🛑  Shutting down.")


# ─────────────────────────────────────────────────────────────────────────────
#  App factory
# ─────────────────────────────────────────────────────────────────────────────

def create_app() -> FastAPI:
    app = FastAPI(
        title="JWT Authentication API",
        description="""
## JWT Authentication System

A production-ready FastAPI authentication backend featuring:

- **Signup** with password strength validation
- **Login** with timing-safe credential verification
- **JWT access tokens** (short-lived, 15 min)
- **Refresh token rotation** (long-lived, 7 days, stored hashed)
- **Protected routes** with role-based access control
- **Password change** with session invalidation
- **Logout** with token revocation

### Authentication Flow

```
POST /auth/signup  →  { access_token, refresh_token }
POST /auth/login   →  { access_token, refresh_token }

Authorization: Bearer <access_token>   ← include on every protected request

POST /auth/refresh  →  new { access_token, refresh_token }   (old refresh revoked)
POST /auth/logout   →  refresh token revoked
```
        """,
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
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

    # ── Security headers middleware ────────────────────────────────────────────
    @app.middleware("http")
    async def add_security_headers(request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Cache-Control"] = "no-store"
        return response

    # ── Request ID middleware ─────────────────────────────────────────────────
    @app.middleware("http")
    async def add_request_id(request: Request, call_next):
        request_id = str(uuid.uuid4())
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response

    # ── Routers ───────────────────────────────────────────────────────────────
    app.include_router(auth_router,      prefix="/api/v1")
    app.include_router(protected_router, prefix="/api/v1")

    # ── Health check ──────────────────────────────────────────────────────────
    @app.get("/health", tags=["System"])
    async def health() -> dict:
        return {"status": "ok", "version": "1.0.0"}

    # ── Root ──────────────────────────────────────────────────────────────────
    @app.get("/", tags=["System"])
    async def root() -> dict:
        return {
            "message": "JWT Authentication API",
            "docs": "/docs",
            "health": "/health",
        }

    # ── Exception handlers ────────────────────────────────────────────────────

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        """Return structured validation errors instead of FastAPI's default."""
        errors = []
        for err in exc.errors():
            field_path = " → ".join(str(loc) for loc in err["loc"] if loc != "body")
            errors.append({
                "field": field_path or "body",
                "message": err["msg"].replace("Value error, ", ""),
                "type": err["type"],
            })
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"detail": "Validation failed", "errors": errors},
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        logger.exception("Unhandled error on %s %s", request.method, request.url)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "An unexpected error occurred. Please try again."},
        )

    return app


app = create_app()
