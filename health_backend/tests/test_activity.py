import pytest
from datetime import date, timedelta
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio

BASE_DATE = str(date.today() - timedelta(days=4))


async def test_create_activity_log(client: AsyncClient, auth_headers: dict):
    resp = await client.post("/api/v1/activity", headers=auth_headers, json={
        "activity_date": BASE_DATE,
        "activity_type": "running",
        "duration_min": 45,
        "distance_m": 6500,
        "calories_burned": 420,
        "intensity": 4,
        "steps": 8200,
        "avg_heart_rate": 158.5,
        "max_heart_rate": 178.0,
        "source": "manual",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["activity_type"] == "running"
    assert data["duration_min"] == 45
    assert data["steps"] == 8200


async def test_multiple_activities_same_day(client: AsyncClient, auth_headers: dict):
    """Multiple activities per day are allowed."""
    d = str(date.today() - timedelta(days=2))
    r1 = await client.post("/api/v1/activity", headers=auth_headers, json={
        "activity_date": d, "activity_type": "cycling", "duration_min": 30,
    })
    r2 = await client.post("/api/v1/activity", headers=auth_headers, json={
        "activity_date": d, "activity_type": "yoga", "duration_min": 20,
    })
    assert r1.status_code == 201
    assert r2.status_code == 201


async def test_list_activity_logs(client: AsyncClient, auth_headers: dict):
    resp = await client.get("/api/v1/activity", headers=auth_headers)
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


async def test_filter_by_activity_type(client: AsyncClient, auth_headers: dict):
    resp = await client.get(
        "/api/v1/activity",
        headers=auth_headers,
        params={"activity_type": "running"},
    )
    assert resp.status_code == 200
    logs = resp.json()
    assert all(log["activity_type"] == "running" for log in logs)


async def test_filter_by_date_range(client: AsyncClient, auth_headers: dict):
    resp = await client.get(
        "/api/v1/activity",
        headers=auth_headers,
        params={"start_date": BASE_DATE, "end_date": BASE_DATE},
    )
    assert resp.status_code == 200


async def test_get_activity_log_by_id(client: AsyncClient, auth_headers: dict):
    d = str(date.today() - timedelta(days=7))
    create_resp = await client.post("/api/v1/activity", headers=auth_headers, json={
        "activity_date": d,
        "activity_type": "swimming",
        "duration_min": 60,
        "calories_burned": 500,
    })
    log_id = create_resp.json()["id"]

    resp = await client.get(f"/api/v1/activity/{log_id}", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["activity_type"] == "swimming"


async def test_invalid_intensity(client: AsyncClient, auth_headers: dict):
    resp = await client.post("/api/v1/activity", headers=auth_headers, json={
        "activity_date": BASE_DATE,
        "activity_type": "running",
        "duration_min": 30,
        "intensity": 6,  # > 5 — invalid
    })
    assert resp.status_code == 422


async def test_negative_duration_fails(client: AsyncClient, auth_headers: dict):
    resp = await client.post("/api/v1/activity", headers=auth_headers, json={
        "activity_date": BASE_DATE,
        "activity_type": "walking",
        "duration_min": -5,
    })
    assert resp.status_code == 422


async def test_delete_activity_log(client: AsyncClient, auth_headers: dict):
    d = str(date.today() - timedelta(days=9))
    create_resp = await client.post("/api/v1/activity", headers=auth_headers, json={
        "activity_date": d, "activity_type": "pilates", "duration_min": 40,
    })
    log_id = create_resp.json()["id"]

    del_resp = await client.delete(f"/api/v1/activity/{log_id}", headers=auth_headers)
    assert del_resp.status_code == 200

    get_resp = await client.get(f"/api/v1/activity/{log_id}", headers=auth_headers)
    assert get_resp.status_code == 404


async def test_activity_requires_auth(client: AsyncClient):
    resp = await client.get("/api/v1/activity")
    assert resp.status_code == 403
