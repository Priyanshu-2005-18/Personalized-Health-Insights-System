import pytest
from datetime import date, timedelta
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio

BASE_DATE = str(date.today() - timedelta(days=5))


async def test_create_sleep_log(client: AsyncClient, auth_headers: dict):
    next_day = str(date.today() - timedelta(days=4))  # day after BASE_DATE
    resp = await client.post("/api/v1/sleep", headers=auth_headers, json={
        "sleep_date": BASE_DATE,
        "bedtime": f"{BASE_DATE}T22:30:00Z",
        "wake_time": f"{next_day}T06:30:00Z",  # next morning
        "quality_score": 8,
        "interruptions": 1,
        "source": "manual",
        "sleep_stages": {
            "deep_min": 90,
            "light_min": 150,
            "rem_min": 60,
            "awake_min": 20,
        },
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["quality_score"] == 8
    assert data["interruptions"] == 1
    assert data["duration_min"] == 480  # 8 hours


async def test_wake_before_bed_fails(client: AsyncClient, auth_headers: dict):
    d = str(date.today() - timedelta(days=10))
    resp = await client.post("/api/v1/sleep", headers=auth_headers, json={
        "sleep_date": d,
        "bedtime": f"{d}T08:00:00Z",
        "wake_time": f"{d}T06:00:00Z",  # wake before bed
    })
    assert resp.status_code == 422


async def test_list_sleep_logs(client: AsyncClient, auth_headers: dict):
    resp = await client.get("/api/v1/sleep", headers=auth_headers)
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


async def test_list_sleep_logs_with_date_filter(client: AsyncClient, auth_headers: dict):
    resp = await client.get(
        "/api/v1/sleep",
        headers=auth_headers,
        params={"start_date": BASE_DATE, "end_date": BASE_DATE},
    )
    assert resp.status_code == 200
    logs = resp.json()
    assert all(log["sleep_date"] == BASE_DATE for log in logs)


async def test_get_sleep_log_by_id(client: AsyncClient, auth_headers: dict):
    d = str(date.today() - timedelta(days=3))
    d_next = str(date.today() - timedelta(days=2))
    create_resp = await client.post("/api/v1/sleep", headers=auth_headers, json={
        "sleep_date": d,
        "bedtime": f"{d}T23:00:00Z",
        "wake_time": f"{d_next}T07:00:00Z",  # next morning
        "quality_score": 7,
    })
    log_id = create_resp.json()["id"]

    resp = await client.get(f"/api/v1/sleep/{log_id}", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["id"] == log_id


async def test_get_nonexistent_sleep_log(client: AsyncClient, auth_headers: dict):
    resp = await client.get(
        "/api/v1/sleep/00000000-0000-0000-0000-000000000000",
        headers=auth_headers,
    )
    assert resp.status_code == 404


async def test_delete_sleep_log(client: AsyncClient, auth_headers: dict):
    d = str(date.today() - timedelta(days=6))
    d_next = str(date.today() - timedelta(days=5))
    create_resp = await client.post("/api/v1/sleep", headers=auth_headers, json={
        "sleep_date": d,
        "bedtime": f"{d}T21:00:00Z",
        "wake_time": f"{d_next}T05:00:00Z",  # next morning
    })
    log_id = create_resp.json()["id"]

    del_resp = await client.delete(f"/api/v1/sleep/{log_id}", headers=auth_headers)
    assert del_resp.status_code == 200
    assert del_resp.json()["message"] == "Sleep log deleted"

    # Confirm gone
    get_resp = await client.get(f"/api/v1/sleep/{log_id}", headers=auth_headers)
    assert get_resp.status_code == 404


async def test_quality_score_out_of_range(client: AsyncClient, auth_headers: dict):
    d = str(date.today() - timedelta(days=8))
    resp = await client.post("/api/v1/sleep", headers=auth_headers, json={
        "sleep_date": d,
        "bedtime": f"{d}T22:00:00Z",
        "wake_time": f"{d}T06:00:00Z",
        "quality_score": 15,  # > 10
    })
    assert resp.status_code == 422


async def test_sleep_requires_auth(client: AsyncClient):
    resp = await client.get("/api/v1/sleep")
    assert resp.status_code == 403
