"""
Health Insights API — Python client SDK
========================================

Thin, dependency-light wrapper around the REST API.
Requires only the standard library + `httpx` (already a FastAPI dependency).

Usage
-----
    from sdk.client import HealthInsightsClient, HealthMetrics

    client = HealthInsightsClient(base_url="http://localhost:8000")

    score = client.predict(HealthMetrics(
        sleep_hours=7.5,
        sleep_quality=7.0,
        steps_daily=9500,
        active_minutes=180,
        resting_hr=64,
        hrv=58,
        stress_index=35,
        water_intake=2.2,
        bmi=23.5,
        user_id="usr_demo",
    ))
    print(score.health_score, score.risk_level)
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field, asdict
from typing import Optional
import httpx


# ── Request dataclass ──────────────────────────────────────────────────────────

@dataclass
class HealthMetrics:
    sleep_hours:    float
    sleep_quality:  float
    steps_daily:    float
    active_minutes: float
    resting_hr:     float
    hrv:            float
    stress_index:   float
    water_intake:   float
    bmi:            float
    user_id:        Optional[str] = None

    def to_dict(self) -> dict:
        return {k: v for k, v in asdict(self).items() if v is not None}


# ── Response dataclasses ───────────────────────────────────────────────────────

@dataclass
class DomainScores:
    sleep:     float
    activity:  float
    cardio:    float
    stress:    float
    lifestyle: float


@dataclass
class Recommendation:
    domain:   str
    message:  str
    priority: str


@dataclass
class HealthScoreResult:
    health_score:    float
    risk_level:      str
    confidence:      float
    domain_scores:   DomainScores
    recommendations: list[Recommendation]
    model_version:   str
    user_id:         Optional[str]

    @classmethod
    def from_dict(cls, data: dict) -> "HealthScoreResult":
        return cls(
            health_score=data["health_score"],
            risk_level=data["risk_level"],
            confidence=data["confidence"],
            domain_scores=DomainScores(**data["domain_scores"]),
            recommendations=[Recommendation(**r) for r in data["recommendations"]],
            model_version=data["model_version"],
            user_id=data.get("user_id"),
        )

    def summary(self) -> str:
        lines = [
            f"Health score : {self.health_score:.1f} / 100",
            f"Risk level   : {self.risk_level.upper()}",
            f"Confidence   : {self.confidence * 100:.0f}%",
            "",
            "Domain breakdown:",
            f"  Sleep      {self.domain_scores.sleep:.1f}",
            f"  Activity   {self.domain_scores.activity:.1f}",
            f"  Cardio     {self.domain_scores.cardio:.1f}",
            f"  Stress     {self.domain_scores.stress:.1f}",
            f"  Lifestyle  {self.domain_scores.lifestyle:.1f}",
            "",
            "Recommendations:",
        ]
        for rec in self.recommendations:
            lines.append(f"  [{rec.priority.upper()}] {rec.domain}: {rec.message}")
        return "\n".join(lines)


@dataclass
class BatchResult:
    results: list[HealthScoreResult]
    total:   int

    @classmethod
    def from_dict(cls, data: dict) -> "BatchResult":
        return cls(
            results=[HealthScoreResult.from_dict(r) for r in data["results"]],
            total=data["total"],
        )


@dataclass
class ModelInfo:
    model_version:  str
    feature_names:  list[str]
    mae:            float
    r2:             float
    cv_r2_mean:     float
    train_samples:  int
    test_samples:   int
    status:         str


# ── Client ─────────────────────────────────────────────────────────────────────

class HealthInsightsClient:
    """
    Synchronous HTTP client for the Health Insights API.

    Parameters
    ----------
    base_url  : API root, e.g. "http://localhost:8000"
    api_prefix: URL prefix (default "/api/v1")
    timeout   : Request timeout in seconds (default 10)
    retries   : Number of retries on transient failures (default 2)
    """

    def __init__(
        self,
        base_url:   str = "http://localhost:8000",
        api_prefix: str = "/api/v1",
        timeout:    float = 10.0,
        retries:    int = 2,
    ) -> None:
        self._base    = base_url.rstrip("/") + api_prefix
        self._timeout = timeout
        self._retries = retries
        self._client  = httpx.Client(timeout=timeout)

    def _post(self, path: str, json: dict) -> dict:
        url = self._base + path
        last_exc: Exception | None = None
        for attempt in range(self._retries + 1):
            try:
                resp = self._client.post(url, json=json)
                resp.raise_for_status()
                return resp.json()
            except httpx.HTTPStatusError as exc:
                raise HealthInsightsAPIError(
                    status_code=exc.response.status_code,
                    detail=exc.response.text,
                ) from exc
            except httpx.TransportError as exc:
                last_exc = exc
                if attempt < self._retries:
                    time.sleep(0.5 * (attempt + 1))
        raise HealthInsightsConnectionError(str(last_exc)) from last_exc

    def _get(self, path: str) -> dict:
        url = self._base + path
        resp = self._client.get(url)
        resp.raise_for_status()
        return resp.json()

    # ── Public methods ─────────────────────────────────────────────────────────

    def predict(self, metrics: HealthMetrics) -> HealthScoreResult:
        """Score a single health metric record."""
        data = self._post("/predict", metrics.to_dict())
        return HealthScoreResult.from_dict(data)

    def predict_batch(self, records: list[HealthMetrics]) -> BatchResult:
        """Score up to 50 records in one request."""
        if len(records) > 50:
            raise ValueError("Batch size cannot exceed 50 records.")
        payload = {"records": [r.to_dict() for r in records]}
        data = self._post("/predict/batch", payload)
        return BatchResult.from_dict(data)

    def model_info(self) -> ModelInfo:
        """Retrieve model version, feature names, and evaluation metrics."""
        data = self._get("/model/info")
        return ModelInfo(**data)

    def is_healthy(self) -> bool:
        """Return True if the API is up and the model is loaded."""
        try:
            data = self._get("/health")
            return data.get("model_loaded", False)
        except Exception:
            return False

    def close(self) -> None:
        self._client.close()

    # ── Context manager support ────────────────────────────────────────────────

    def __enter__(self) -> "HealthInsightsClient":
        return self

    def __exit__(self, *_) -> None:
        self.close()


# ── Exceptions ─────────────────────────────────────────────────────────────────

class HealthInsightsError(Exception):
    """Base exception for the SDK."""


class HealthInsightsAPIError(HealthInsightsError):
    def __init__(self, status_code: int, detail: str) -> None:
        self.status_code = status_code
        self.detail = detail
        super().__init__(f"API error {status_code}: {detail}")


class HealthInsightsConnectionError(HealthInsightsError):
    """Raised when the API cannot be reached."""


# ── Quick demo ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    with HealthInsightsClient() as client:
        if not client.is_healthy():
            print("API is not reachable. Start with: uvicorn app.main:app --port 8000")
            raise SystemExit(1)

        info = client.model_info()
        print(f"Model v{info.model_version} | MAE={info.mae} | R²={info.r2}\n")

        result = client.predict(HealthMetrics(
            sleep_hours=7.5,    sleep_quality=7.0,
            steps_daily=9500,   active_minutes=180,
            resting_hr=64,      hrv=58,
            stress_index=35,    water_intake=2.2,
            bmi=23.5,           user_id="sdk_demo",
        ))
        print(result.summary())

        print("\n── Batch example ──")
        batch = client.predict_batch([
            HealthMetrics(7.5,7.0,9500,180,64,58,35,2.2,23.5,"user_1"),
            HealthMetrics(4.0,2.0,1500,20,95,18,85,0.8,33.0,"user_2"),
            HealthMetrics(8.5,9.5,14000,300,52,90,10,3.0,22.0,"user_3"),
        ])
        for r in batch.results:
            print(f"  {r.user_id}: score={r.health_score:.1f} risk={r.risk_level}")
