import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


async def test_get_profile(client: AsyncClient, auth_headers: dict):
    """Profile is auto-created on registration."""
    resp = await client.get("/api/v1/users/me/profile", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["first_name"] == "Test"
    assert data["last_name"] == "User"


async def test_update_profile(client: AsyncClient, auth_headers: dict):
    resp = await client.patch("/api/v1/users/me/profile", headers=auth_headers, json={
        "height_cm": 175.5,
        "weight_kg": 70.0,
        "activity_level": "moderately_active",
        "health_goals": ["lose_weight", "improve_sleep"],
        "timezone": "Asia/Kolkata",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["height_cm"] == 175.5
    assert data["activity_level"] == "moderately_active"
    assert "lose_weight" in data["health_goals"]


async def test_update_profile_invalid_height(client: AsyncClient, auth_headers: dict):
    resp = await client.patch("/api/v1/users/me/profile", headers=auth_headers, json={
        "height_cm": -10,
    })
    assert resp.status_code == 422


async def test_get_me(client: AsyncClient, auth_headers: dict):
    resp = await client.get("/api/v1/users/me", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["email"] == "test@example.com"
