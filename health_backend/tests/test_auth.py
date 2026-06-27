import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


async def test_register_success(client: AsyncClient):
    resp = await client.post("/api/v1/auth/register", json={
        "email": "newuser@example.com",
        "password": "Secure123",
        "first_name": "New",
        "last_name": "User",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


async def test_register_duplicate_email(client: AsyncClient):
    payload = {
        "email": "dup@example.com",
        "password": "Secure123",
        "first_name": "A",
        "last_name": "B",
    }
    await client.post("/api/v1/auth/register", json=payload)
    resp = await client.post("/api/v1/auth/register", json=payload)
    assert resp.status_code == 409


async def test_register_weak_password(client: AsyncClient):
    resp = await client.post("/api/v1/auth/register", json={
        "email": "weak@example.com",
        "password": "short",
        "first_name": "A",
        "last_name": "B",
    })
    assert resp.status_code == 422


async def test_login_success(client: AsyncClient):
    await client.post("/api/v1/auth/register", json={
        "email": "login@example.com",
        "password": "Secure123",
        "first_name": "L",
        "last_name": "U",
    })
    resp = await client.post("/api/v1/auth/login", json={
        "email": "login@example.com",
        "password": "Secure123",
    })
    assert resp.status_code == 200
    assert "access_token" in resp.json()


async def test_login_wrong_password(client: AsyncClient):
    await client.post("/api/v1/auth/register", json={
        "email": "wrong@example.com",
        "password": "Correct1",
        "first_name": "X",
        "last_name": "Y",
    })
    resp = await client.post("/api/v1/auth/login", json={
        "email": "wrong@example.com",
        "password": "WrongPass1",
    })
    assert resp.status_code == 401


async def test_refresh_token(client: AsyncClient, registered_user: dict):
    resp = await client.post("/api/v1/auth/refresh", json={
        "refresh_token": registered_user["refresh_token"]
    })
    assert resp.status_code == 200
    assert "access_token" in resp.json()


async def test_logout(client: AsyncClient, registered_user: dict):
    resp = await client.post("/api/v1/auth/logout", json={
        "refresh_token": registered_user["refresh_token"]
    })
    assert resp.status_code == 200
    assert resp.json()["message"] == "Logged out successfully"
