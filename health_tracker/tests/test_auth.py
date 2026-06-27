"""
tests/test_auth.py
==================
Tests for POST /auth/signup and POST /auth/login.
"""

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio
BASE = "/api/v1/auth"


async def test_signup_success(client: AsyncClient):
    resp = await client.post(f"{BASE}/signup", json={
        "email": "newuser@test.com",
        "username": "newuser",
        "password": "Pass@word1",
        "full_name": "New User",
    })
    assert resp.status_code == 201
    assert "created" in resp.json()["message"].lower()


async def test_signup_duplicate_email(client: AsyncClient):
    payload = {"email": "dup@test.com", "username": "dup1", "password": "Dup@word1"}
    await client.post(f"{BASE}/signup", json=payload)
    payload["username"] = "dup2"
    resp = await client.post(f"{BASE}/signup", json=payload)
    assert resp.status_code == 409


async def test_login_success(client: AsyncClient):
    await client.post(f"{BASE}/signup", json={
        "email": "login@test.com", "username": "loginuser", "password": "Login@123"
    })
    resp = await client.post(f"{BASE}/login", json={
        "email": "login@test.com", "password": "Login@123"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


async def test_login_wrong_password(client: AsyncClient):
    await client.post(f"{BASE}/signup", json={
        "email": "pw@test.com", "username": "pwuser", "password": "Right@123"
    })
    resp = await client.post(f"{BASE}/login", json={
        "email": "pw@test.com", "password": "Wrong@999"
    })
    assert resp.status_code == 401


async def test_login_nonexistent_user(client: AsyncClient):
    resp = await client.post(f"{BASE}/login", json={
        "email": "nobody@test.com", "password": "Any@pass1"
    })
    assert resp.status_code == 401


async def test_protected_route_without_token(client: AsyncClient):
    resp = await client.get("/api/v1/health")
    assert resp.status_code == 401


async def test_protected_route_with_bad_token(client: AsyncClient):
    resp = await client.get(
        "/api/v1/health",
        headers={"Authorization": "Bearer bad.token.value"}
    )
    assert resp.status_code == 401
