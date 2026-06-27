"""
tests/test_predict.py
=====================
Test suite for the health-score prediction endpoints.

Tests cover:
  - Authenticated single prediction
  - Anonymous prediction (no auth required)
  - Batch prediction
  - Model-info endpoint
  - Input validation (out-of-range, missing fields)
  - Score is within 0–100
  - Grade letter is one of A/B/C/D/F
  - Category scores are returned
"""
import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio

# ── Fixtures ──────────────────────────────────────────────────────────────────

HEALTHY_PAYLOAD = {
    "sleep_hours":     8.0,
    "steps":           10500,
    "calories":        2050,
    "water_intake_ml": 2800,
    "stress_level":    2,
    "heart_rate_bpm":  65,
}

AVERAGE_PAYLOAD = {
    "sleep_hours":     6.5,
    "steps":           6200,
    "calories":        2400,
    "water_intake_ml": 1800,
    "stress_level":    5,
    "heart_rate_bpm":  74,
}

UNHEALTHY_PAYLOAD = {
    "sleep_hours":     4.5,
    "steps":           1800,
    "calories":        3200,
    "water_intake_ml": 800,
    "stress_level":    9,
    "heart_rate_bpm":  98,
}


# ── Single prediction (authenticated) ─────────────────────────────────────────

async def test_predict_healthy_profile(client: AsyncClient, auth_headers: dict):
    resp = await client.post("/api/v1/predict", headers=auth_headers, json=HEALTHY_PAYLOAD)
    assert resp.status_code == 200
    data = resp.json()

    assert "health_score" in data
    assert 0.0 <= data["health_score"] <= 100.0
    assert data["letter"] in ("A", "B", "C", "D", "F")
    assert "category_scores" in data
    assert "feedback" in data
    assert isinstance(data["feedback"], list)
    assert "model_used" in data


async def test_predict_average_profile(client: AsyncClient, auth_headers: dict):
    resp = await client.post("/api/v1/predict", headers=auth_headers, json=AVERAGE_PAYLOAD)
    assert resp.status_code == 200
    assert 0.0 <= resp.json()["health_score"] <= 100.0


async def test_predict_unhealthy_profile(client: AsyncClient, auth_headers: dict):
    resp = await client.post("/api/v1/predict", headers=auth_headers, json=UNHEALTHY_PAYLOAD)
    assert resp.status_code == 200
    data = resp.json()
    assert 0.0 <= data["health_score"] <= 100.0
    # Unhealthy profile should score lower than healthy
    healthy_resp = await client.post("/api/v1/predict", headers=auth_headers, json=HEALTHY_PAYLOAD)
    assert resp.json()["health_score"] <= healthy_resp.json()["health_score"]


async def test_predict_requires_auth(client: AsyncClient):
    """Without auth headers, should return 403."""
    resp = await client.post("/api/v1/predict", json=HEALTHY_PAYLOAD)
    assert resp.status_code == 403


async def test_predict_partial_data(client: AsyncClient, auth_headers: dict):
    """Missing fields are handled gracefully."""
    partial = {"sleep_hours": 7.0, "steps": 8000}
    resp = await client.post("/api/v1/predict", headers=auth_headers, json=partial)
    assert resp.status_code == 200
    data = resp.json()
    assert 0.0 <= data["health_score"] <= 100.0


async def test_predict_empty_payload(client: AsyncClient, auth_headers: dict):
    """Empty dict should still return a response using fallback defaults."""
    resp = await client.post("/api/v1/predict", headers=auth_headers, json={})
    assert resp.status_code == 200


async def test_predict_invalid_sleep_hours(client: AsyncClient, auth_headers: dict):
    """sleep_hours > 24 should fail validation."""
    resp = await client.post("/api/v1/predict", headers=auth_headers, json={
        **HEALTHY_PAYLOAD,
        "sleep_hours": 25.0,
    })
    assert resp.status_code == 422


async def test_predict_invalid_stress_level(client: AsyncClient, auth_headers: dict):
    """stress_level > 10 should fail validation."""
    resp = await client.post("/api/v1/predict", headers=auth_headers, json={
        **HEALTHY_PAYLOAD,
        "stress_level": 11,
    })
    assert resp.status_code == 422


async def test_predict_invalid_heart_rate(client: AsyncClient, auth_headers: dict):
    """heart_rate_bpm > 220 should fail validation."""
    resp = await client.post("/api/v1/predict", headers=auth_headers, json={
        **HEALTHY_PAYLOAD,
        "heart_rate_bpm": 250,
    })
    assert resp.status_code == 422


async def test_predict_category_scores_range(client: AsyncClient, auth_headers: dict):
    """All category scores must be in [0, 100]."""
    resp = await client.post("/api/v1/predict", headers=auth_headers, json=HEALTHY_PAYLOAD)
    assert resp.status_code == 200
    for metric, score in resp.json()["category_scores"].items():
        assert 0.0 <= score <= 100.0, f"{metric} score {score} out of range"


# ── Anonymous endpoint ────────────────────────────────────────────────────────

async def test_predict_anonymous_no_auth(client: AsyncClient):
    """Anonymous endpoint should work without auth."""
    resp = await client.post("/api/v1/predict/anonymous", json=HEALTHY_PAYLOAD)
    assert resp.status_code == 200
    assert 0.0 <= resp.json()["health_score"] <= 100.0


async def test_predict_anonymous_result_consistent(client: AsyncClient, auth_headers: dict):
    """Anonymous and authenticated should return same score for same inputs."""
    auth_resp   = await client.post("/api/v1/predict",           headers=auth_headers, json=AVERAGE_PAYLOAD)
    anon_resp   = await client.post("/api/v1/predict/anonymous", json=AVERAGE_PAYLOAD)

    assert auth_resp.status_code == 200
    assert anon_resp.status_code == 200
    # Scores must be identical (same model, same inputs)
    assert auth_resp.json()["health_score"] == anon_resp.json()["health_score"]


# ── Batch endpoint ────────────────────────────────────────────────────────────

async def test_predict_batch(client: AsyncClient, auth_headers: dict):
    payload = {
        "records": [HEALTHY_PAYLOAD, AVERAGE_PAYLOAD, UNHEALTHY_PAYLOAD]
    }
    resp = await client.post("/api/v1/predict/batch", headers=auth_headers, json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["count"] == 3
    assert len(data["predictions"]) == 3
    for pred in data["predictions"]:
        assert 0.0 <= pred["health_score"] <= 100.0
        assert pred["letter"] in ("A", "B", "C", "D", "F")


async def test_predict_batch_empty_records(client: AsyncClient, auth_headers: dict):
    """Batch with empty list should fail validation."""
    resp = await client.post("/api/v1/predict/batch", headers=auth_headers, json={"records": []})
    assert resp.status_code == 422


async def test_predict_batch_too_many_records(client: AsyncClient, auth_headers: dict):
    """Batch with > 50 records should fail validation."""
    records = [HEALTHY_PAYLOAD] * 51
    resp = await client.post("/api/v1/predict/batch", headers=auth_headers, json={"records": records})
    assert resp.status_code == 422


async def test_predict_batch_requires_auth(client: AsyncClient):
    payload = {"records": [HEALTHY_PAYLOAD]}
    resp = await client.post("/api/v1/predict/batch", json=payload)
    assert resp.status_code == 403


# ── Model-info endpoint ───────────────────────────────────────────────────────

async def test_predict_model_info(client: AsyncClient, auth_headers: dict):
    resp = await client.get("/api/v1/predict/model-info", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "model_loaded" in data
    assert isinstance(data["model_loaded"], bool)
    assert "features" in data
    assert data["feature_count"] == 6
    assert set(data["features"]) == {
        "sleep_hours", "steps", "calories",
        "water_intake_ml", "stress_level", "heart_rate_bpm",
    }
    assert "grade_thresholds" in data


async def test_predict_model_info_requires_auth(client: AsyncClient):
    resp = await client.get("/api/v1/predict/model-info")
    assert resp.status_code == 403
