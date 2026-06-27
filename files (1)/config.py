"""
Centralised configuration loaded from environment variables (or a .env file).

Usage
-----
    from app.config import settings
    print(settings.model_path)
"""

from functools import lru_cache
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # ── API ────────────────────────────────────────────────────────────────────
    app_name:    str = "Health Insights API"
    app_version: str = "1.0.0"
    debug:       bool = False
    log_level:   str = "INFO"

    # ── CORS ───────────────────────────────────────────────────────────────────
    cors_origins: list[str] = ["*"]

    # ── ML model ───────────────────────────────────────────────────────────────
    model_path: Path = (
        Path(__file__).resolve().parents[1] / "ml" / "artifacts" / "health_score_model.joblib"
    )
    model_version: str = "1.0.0"

    # ── Rate limiting (requests per minute per IP; 0 = disabled) ───────────────
    rate_limit_rpm: int = 0

    # ── Batch predict ──────────────────────────────────────────────────────────
    batch_max_size: int = 50

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached Settings singleton."""
    return Settings()


settings = get_settings()
