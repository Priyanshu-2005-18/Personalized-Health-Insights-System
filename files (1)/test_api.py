"""
Test suite for the Health Insights API.

Run with:
    pytest tests/test_api.py -v
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.model_service import model_service

# Ensure model is loaded before any test runs
model_service.startup()

client = TestClient(app)

# ── Fixtures ───────────────────────────────────────────────────────────────────

VALID_PAYLOAD = {
    "sleep_hours":    7.5,
    "sleep_quality":  7.0,
    "steps_daily":    9500.0,
    "active_minutes": 180.0,
    "resting_hr":     64.0,
    "hrv":            58.0,
    "stress_index":   35.0,
    "water_intake":   2.2,
    "bmi":            23.5,
    "user_id":        "test_user_001",
}

LOW_HEALTH_PAYLOAD = {
    "sleep_hours":    4.0,
    "sleep_quality":  2.0,
    "steps_daily":    1500.0,
    "active_minutes": 20.0,
    "resting_hr":     95.0,
    "hrv":            18.0,
    "stress_index":   85.0,
    "water_intake":   0.8,
    "bmi":            33.0,
}

HIGH_HEALTH_PAYLOAD = {
    "sleep_hours":    8.5,
    "sleep_quality":  9.5,
    "steps_daily":    14000.0,
    "active_minutes": 300.0,
    "resting_hr":     52.0,
    "hrv":            90.0,
    "stress_index":   10.0,
    "water_intake":   3.0,
    "bmi":            22.0,
}


# ── /health ────────────────────────────────────────────────────────────────────

class TestHealthCheck:
    def test_returns_200_when_model_loaded(self):
        r = client.get("/api/v1/health")
        assert r.status_code == 200
        body = r.json()
        assert body["status"] == "ok"
        assert body["model_loaded"] is True


# ── /model/info ────────────────────────────────────────────────────────────────

class TestModelInfo:
    def test_returns_model_metadata(self):
        r = client.get("/api/v1/model/info")
        assert r.status_code == 200
        body = r.json()
        assert "model_version" in body
        assert "feature_names" in body
        assert isinstance(body["feature_names"], list)
        assert len(body["feature_names"]) == 9
        assert "mae" in body
        assert "r2" in body
        assert body["status"] == "loaded"


# ── /predict ───────────────────────────────────────────────────────────────────

class TestPredict:
    def test_valid_payload_returns_200(self):
        r = client.post("/api/v1/predict", json=VALID_PAYLOAD)
        assert r.status_code == 200

    def test_response_schema(self):
        r = client.post("/api/v1/predict", json=VALID_PAYLOAD)
        body = r.json()
        assert "health_score" in body
        assert "risk_level" in body
        assert "confidence" in body
        assert "domain_scores" in body
        assert "recommendations" in body
        assert "model_version" in body

    def test_health_score_in_range(self):
        r = client.post("/api/v1/predict", json=VALID_PAYLOAD)
        score = r.json()["health_score"]
        assert 0.0 <= score <= 100.0

    def test_domain_scores_all_present(self):
        r = client.post("/api/v1/predict", json=VALID_PAYLOAD)
        ds = r.json()["domain_scores"]
        for key in ("sleep", "activity", "cardio", "stress", "lifestyle"):
            assert key in ds
            assert 0.0 <= ds[key] <= 100.0

    def test_risk_level_valid_enum(self):
        r = client.post("/api/v1/predict", json=VALID_PAYLOAD)
        risk = r.json()["risk_level"]
        assert risk in ("low", "moderate", "high", "critical")

    def test_user_id_echoed(self):
        r = client.post("/api/v1/predict", json=VALID_PAYLOAD)
        assert r.json()["user_id"] == "test_user_001"

    def test_low_health_metrics_give_high_risk(self):
        r = client.post("/api/v1/predict", json=LOW_HEALTH_PAYLOAD)
        risk = r.json()["risk_level"]
        assert risk in ("high", "critical")

    def test_high_health_metrics_give_low_risk(self):
        r = client.post("/api/v1/predict", json=HIGH_HEALTH_PAYLOAD)
        risk = r.json()["risk_level"]
        assert risk in ("low", "moderate")

    def test_high_score_gt_low_score(self):
        high_score = client.post("/api/v1/predict", json=HIGH_HEALTH_PAYLOAD).json()["health_score"]
        low_score  = client.post("/api/v1/predict", json=LOW_HEALTH_PAYLOAD).json()["health_score"]
        assert high_score > low_score

    def test_recommendations_are_list(self):
        r = client.post("/api/v1/predict", json=VALID_PAYLOAD)
        recs = r.json()["recommendations"]
        assert isinstance(recs, list)
        assert len(recs) >= 1
        for rec in recs:
            assert "domain" in rec
            assert "message" in rec
            assert "priority" in rec
            assert rec["priority"] in ("high", "medium", "low")

    def test_response_headers_include_request_id(self):
        r = client.post("/api/v1/predict", json=VALID_PAYLOAD)
        assert "x-request-id" in r.headers
        assert "x-response-time-ms" in r.headers

    # ── Validation failures ────────────────────────────────────────────────────

    def test_missing_required_field_returns_422(self):
        bad = {k: v for k, v in VALID_PAYLOAD.items() if k != "sleep_hours"}
        r = client.post("/api/v1/predict", json=bad)
        assert r.status_code == 422

    def test_sleep_hours_out_of_range_returns_422(self):
        bad = {**VALID_PAYLOAD, "sleep_hours": 25.0}  # > 24 hrs
        r = client.post("/api/v1/predict", json=bad)
        assert r.status_code == 422

    def test_negative_steps_returns_422(self):
        bad = {**VALID_PAYLOAD, "steps_daily": -100.0}
        r = client.post("/api/v1/predict", json=bad)
        assert r.status_code == 422

    def test_bmi_too_low_returns_422(self):
        bad = {**VALID_PAYLOAD, "bmi": 5.0}  # < 10
        r = client.post("/api/v1/predict", json=bad)
        assert r.status_code == 422

    def test_stress_index_over_100_returns_422(self):
        bad = {**VALID_PAYLOAD, "stress_index": 110.0}
        r = client.post("/api/v1/predict", json=bad)
        assert r.status_code == 422

    def test_string_where_float_expected_returns_422(self):
        bad = {**VALID_PAYLOAD, "resting_hr": "fast"}
        r = client.post("/api/v1/predict", json=bad)
        assert r.status_code == 422

    def test_empty_body_returns_422(self):
        r = client.post("/api/v1/predict", json={})
        assert r.status_code == 422

    # ── Optional field ─────────────────────────────────────────────────────────

    def test_user_id_is_optional(self):
        payload = {k: v for k, v in VALID_PAYLOAD.items() if k != "user_id"}
        r = client.post("/api/v1/predict", json=payload)
        assert r.status_code == 200
        assert r.json()["user_id"] is None

    def test_confidence_between_0_and_1(self):
        r = client.post("/api/v1/predict", json=VALID_PAYLOAD)
        conf = r.json()["confidence"]
        assert 0.0 <= conf <= 1.0


# ── /predict/batch ─────────────────────────────────────────────────────────────

class TestPredictBatch:
    def test_batch_two_records(self):
        r = client.post(
            "/api/v1/predict/batch",
            json={"records": [VALID_PAYLOAD, LOW_HEALTH_PAYLOAD]},
        )
        assert r.status_code == 200
        body = r.json()
        assert body["total"] == 2
        assert len(body["results"]) == 2

    def test_each_result_has_health_score(self):
        r = client.post(
            "/api/v1/predict/batch",
            json={"records": [VALID_PAYLOAD, HIGH_HEALTH_PAYLOAD]},
        )
        for result in r.json()["results"]:
            assert "health_score" in result
            assert 0.0 <= result["health_score"] <= 100.0

    def test_empty_records_returns_422(self):
        r = client.post("/api/v1/predict/batch", json={"records": []})
        assert r.status_code == 422

    def test_batch_exceeding_50_returns_422(self):
        r = client.post(
            "/api/v1/predict/batch",
            json={"records": [VALID_PAYLOAD] * 51},
        )
        assert r.status_code == 422
