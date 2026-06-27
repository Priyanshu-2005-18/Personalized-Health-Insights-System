import pytest
from datetime import date, timedelta
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


async def _seed_data(client: AsyncClient, headers: dict):
    """Seed enough data to trigger recommendation generation."""
    base = date.today() - timedelta(days=7)
    for i in range(7):
        d = str(base + timedelta(days=i))
        await client.post("/api/v1/health/logs", headers=headers, json={
            "log_date": d, "mood_score": 5, "stress_level": 8,
            "energy_level": 4, "water_ml": 1000,
        })
        await client.post("/api/v1/sleep", headers=headers, json={
            "sleep_date": d,
            "bedtime": f"{d}T22:00:00Z",
            "wake_time": f"{d}T04:00:00Z",  # only 6h → triggers recommendation
            "quality_score": 4,
        })
        await client.post("/api/v1/activity", headers=headers, json={
            "activity_date": d,
            "activity_type": "walking",
            "steps": 3000,  # below 5k → triggers recommendation
            "duration_min": 20,
        })


async def test_generate_recommendations(client: AsyncClient, auth_headers: dict):
    await _seed_data(client, auth_headers)
    resp = await client.post("/api/v1/insights/generate", headers=auth_headers)
    assert resp.status_code == 201
    data = resp.json()
    assert "items" in data
    assert data["total"] >= 1


async def test_list_recommendations(client: AsyncClient, auth_headers: dict):
    resp = await client.get("/api/v1/insights", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data
    assert "unread_count" in data


async def test_mark_recommendation_read(client: AsyncClient, auth_headers: dict):
    list_resp = await client.get("/api/v1/insights", headers=auth_headers)
    items = list_resp.json()["items"]
    if not items:
        pytest.skip("No recommendations to test")

    rec_id = items[0]["id"]
    resp = await client.patch(f"/api/v1/insights/{rec_id}/read", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["is_read"] is True


async def test_dismiss_recommendation(client: AsyncClient, auth_headers: dict):
    list_resp = await client.get("/api/v1/insights", headers=auth_headers)
    items = list_resp.json()["items"]
    if not items:
        pytest.skip("No recommendations to test")

    rec_id = items[0]["id"]
    resp = await client.patch(f"/api/v1/insights/{rec_id}/dismiss", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["is_dismissed"] is True


async def test_generate_without_data_fails(client: AsyncClient):
    # Register a fresh user with zero data
    reg = await client.post("/api/v1/auth/register", json={
        "email": "empty@example.com",
        "password": "Empty123",
        "first_name": "E", "last_name": "U",
    })
    headers = {"Authorization": f"Bearer {reg.json()['access_token']}"}
    resp = await client.post("/api/v1/insights/generate", headers=headers)
    assert resp.status_code == 400
