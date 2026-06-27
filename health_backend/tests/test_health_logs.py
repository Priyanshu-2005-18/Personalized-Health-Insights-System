import pytest
from datetime import date
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio

TODAY = str(date.today())


async def test_create_health_log(client: AsyncClient, auth_headers: dict):
    resp = await client.post("/api/v1/health/logs", headers=auth_headers, json={
        "log_date": TODAY,
        "mood_score": 7,
        "stress_level": 4,
        "energy_level": 8,
        "water_ml": 2000,
        "notes": "Feeling good today",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["mood_score"] == 7
    assert data["water_ml"] == 2000


async def test_create_duplicate_log_fails(client: AsyncClient, auth_headers: dict):
    payload = {"log_date": "2024-01-15", "mood_score": 5}
    await client.post("/api/v1/health/logs", headers=auth_headers, json=payload)
    resp = await client.post("/api/v1/health/logs", headers=auth_headers, json=payload)
    assert resp.status_code == 409


async def test_list_health_logs(client: AsyncClient, auth_headers: dict):
    resp = await client.get("/api/v1/health/logs", headers=auth_headers)
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


async def test_get_today_log(client: AsyncClient, auth_headers: dict):
    await client.post("/api/v1/health/logs", headers=auth_headers, json={
        "log_date": TODAY, "mood_score": 6,
    })
    resp = await client.get("/api/v1/health/logs/today", headers=auth_headers)
    assert resp.status_code == 200


async def test_update_health_log(client: AsyncClient, auth_headers: dict):
    create_resp = await client.post("/api/v1/health/logs", headers=auth_headers, json={
        "log_date": "2024-03-10", "mood_score": 5, "water_ml": 1000,
    })
    log_id = create_resp.json()["id"]
    resp = await client.patch(
        f"/api/v1/health/logs/{log_id}", headers=auth_headers,
        json={"water_ml": 2500}
    )
    assert resp.status_code == 200
    assert resp.json()["water_ml"] == 2500


async def test_delete_health_log(client: AsyncClient, auth_headers: dict):
    create_resp = await client.post("/api/v1/health/logs", headers=auth_headers, json={
        "log_date": "2024-04-01", "mood_score": 3,
    })
    log_id = create_resp.json()["id"]
    resp = await client.delete(f"/api/v1/health/logs/{log_id}", headers=auth_headers)
    assert resp.status_code == 200


async def test_invalid_mood_score(client: AsyncClient, auth_headers: dict):
    resp = await client.post("/api/v1/health/logs", headers=auth_headers, json={
        "log_date": "2024-05-01", "mood_score": 11,
    })
    assert resp.status_code == 422


async def test_unauthenticated_access(client: AsyncClient):
    resp = await client.get("/api/v1/health/logs")
    assert resp.status_code == 403
