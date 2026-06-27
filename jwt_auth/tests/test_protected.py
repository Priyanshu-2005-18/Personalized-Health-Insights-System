"""
tests/test_protected.py
=======================
Tests for role-based access control on protected routes.
"""

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio

BASE = "/api/v1/protected"
AUTH_BASE = "/api/v1/auth"


# ─────────────────────────────────────────────────────────────────────────────
#  Helpers
# ─────────────────────────────────────────────────────────────────────────────

async def _make_user(client: AsyncClient, email: str, username: str) -> dict:
    resp = await client.post(f"{AUTH_BASE}/signup", json={
        "email": email,
        "username": username,
        "password": "Test@12345",
        "confirm_password": "Test@12345",
    })
    assert resp.status_code == 201
    return resp.json()


def _headers(token_resp: dict) -> dict:
    return {"Authorization": f"Bearer {token_resp['access_token']}"}


# ─────────────────────────────────────────────────────────────────────────────
#  User-only route
# ─────────────────────────────────────────────────────────────────────────────

async def test_user_only_authenticated(client: AsyncClient, auth_headers: dict):
    resp = await client.get(f"{BASE}/user-only", headers=auth_headers)
    assert resp.status_code == 200
    assert "authenticated" in resp.json()["message"].lower()


async def test_user_only_unauthenticated(client: AsyncClient):
    resp = await client.get(f"{BASE}/user-only")
    assert resp.status_code == 401


async def test_user_only_bad_token(client: AsyncClient):
    resp = await client.get(
        f"{BASE}/user-only",
        headers={"Authorization": "Bearer bad.token.here"},
    )
    assert resp.status_code == 401


# ─────────────────────────────────────────────────────────────────────────────
#  Profile route
# ─────────────────────────────────────────────────────────────────────────────

async def test_profile_returns_user_data(client: AsyncClient, auth_headers: dict):
    resp = await client.get(f"{BASE}/profile", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "email" in data
    assert "password_hash" not in data
    assert "password" not in data


# ─────────────────────────────────────────────────────────────────────────────
#  Token claims route
# ─────────────────────────────────────────────────────────────────────────────

async def test_token_claims_shows_sub_and_role(
    client: AsyncClient, auth_headers: dict
):
    resp = await client.get(f"{BASE}/token-claims", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "sub" in data
    assert "role" in data
    assert "type" in data
    assert data["type"] == "access"


async def test_token_claims_no_token(client: AsyncClient):
    resp = await client.get(f"{BASE}/token-claims")
    assert resp.status_code == 200
    assert "error" in resp.json()


# ─────────────────────────────────────────────────────────────────────────────
#  Admin-only route
# ─────────────────────────────────────────────────────────────────────────────

async def test_admin_route_blocked_for_normal_user(
    client: AsyncClient, auth_headers: dict
):
    """Regular users (role='user') must receive 403."""
    resp = await client.get(f"{BASE}/admin-only", headers=auth_headers)
    assert resp.status_code == 403


async def test_admin_route_unauthenticated(client: AsyncClient):
    resp = await client.get(f"{BASE}/admin-only")
    assert resp.status_code == 401


# ─────────────────────────────────────────────────────────────────────────────
#  Moderator-plus route
# ─────────────────────────────────────────────────────────────────────────────

async def test_moderator_route_blocked_for_normal_user(
    client: AsyncClient, auth_headers: dict
):
    resp = await client.get(f"{BASE}/moderator-plus", headers=auth_headers)
    assert resp.status_code == 403


# ─────────────────────────────────────────────────────────────────────────────
#  Token type enforcement
# ─────────────────────────────────────────────────────────────────────────────

async def test_refresh_token_rejected_on_protected_route(
    client: AsyncClient, registered: dict
):
    """A refresh token must not be accepted as an access token."""
    headers = {"Authorization": f"Bearer {registered['refresh_token']}"}
    resp = await client.get(f"{BASE}/user-only", headers=headers)
    assert resp.status_code == 401


# ─────────────────────────────────────────────────────────────────────────────
#  Expired / tampered token
# ─────────────────────────────────────────────────────────────────────────────

async def test_tampered_token_rejected(client: AsyncClient, auth_headers: dict):
    # Take a valid token and flip the last character
    good_token = auth_headers["Authorization"].split(" ")[1]
    bad_token = good_token[:-1] + ("X" if good_token[-1] != "X" else "Y")
    resp = await client.get(
        f"{BASE}/user-only",
        headers={"Authorization": f"Bearer {bad_token}"},
    )
    assert resp.status_code == 401
