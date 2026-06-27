"""
tests/test_auth.py
==================
Tests for every auth endpoint:
  signup, login, refresh, logout, change-password, /me, verify-token
"""

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio

BASE = "/api/v1/auth"


# ─────────────────────────────────────────────────────────────────────────────
#  Signup
# ─────────────────────────────────────────────────────────────────────────────

async def test_signup_success(client: AsyncClient):
    resp = await client.post(f"{BASE}/signup", json={
        "email": "alice@example.com",
        "username": "alice",
        "password": "Alice@1234",
        "confirm_password": "Alice@1234",
        "full_name": "Alice Smith",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["email"] == "alice@example.com"
    assert data["username"] == "alice"
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"
    # Password hash must never be in the response
    assert "password" not in data
    assert "password_hash" not in data


async def test_signup_duplicate_email(client: AsyncClient):
    payload = {
        "email": "dup@example.com",
        "username": "dupuser",
        "password": "Dup@12345",
        "confirm_password": "Dup@12345",
    }
    r1 = await client.post(f"{BASE}/signup", json=payload)
    assert r1.status_code == 201

    payload["username"] = "dupuser2"   # different username, same email
    r2 = await client.post(f"{BASE}/signup", json=payload)
    assert r2.status_code == 409
    assert "email" in r2.json()["detail"].lower()


async def test_signup_duplicate_username(client: AsyncClient):
    await client.post(f"{BASE}/signup", json={
        "email": "user1@example.com",
        "username": "sharedname",
        "password": "Pass@1234",
        "confirm_password": "Pass@1234",
    })
    resp = await client.post(f"{BASE}/signup", json={
        "email": "user2@example.com",
        "username": "sharedname",
        "password": "Pass@1234",
        "confirm_password": "Pass@1234",
    })
    assert resp.status_code == 409


async def test_signup_passwords_mismatch(client: AsyncClient):
    resp = await client.post(f"{BASE}/signup", json={
        "email": "mismatch@example.com",
        "username": "mismatch",
        "password": "Secure@123",
        "confirm_password": "Different@456",
    })
    assert resp.status_code == 422
    body = resp.json()
    assert any("match" in e["message"].lower() for e in body["errors"])


async def test_signup_weak_password(client: AsyncClient):
    """Password without special char should be rejected."""
    resp = await client.post(f"{BASE}/signup", json={
        "email": "weak@example.com",
        "username": "weakuser",
        "password": "password1",          # no uppercase, no special char
        "confirm_password": "password1",
    })
    assert resp.status_code == 422


async def test_signup_short_password(client: AsyncClient):
    resp = await client.post(f"{BASE}/signup", json={
        "email": "short@example.com",
        "username": "shortpass",
        "password": "Ab@1",              # < 8 chars
        "confirm_password": "Ab@1",
    })
    assert resp.status_code == 422


async def test_signup_invalid_email(client: AsyncClient):
    resp = await client.post(f"{BASE}/signup", json={
        "email": "not-an-email",
        "username": "bademail",
        "password": "Secure@123",
        "confirm_password": "Secure@123",
    })
    assert resp.status_code == 422


async def test_signup_email_normalised_to_lowercase(client: AsyncClient):
    resp = await client.post(f"{BASE}/signup", json={
        "email": "UPPER@Example.COM",
        "username": "upperuser",
        "password": "Upper@1234",
        "confirm_password": "Upper@1234",
    })
    assert resp.status_code == 201
    assert resp.json()["email"] == "upper@example.com"


# ─────────────────────────────────────────────────────────────────────────────
#  Login
# ─────────────────────────────────────────────────────────────────────────────

async def test_login_success(client: AsyncClient, registered: dict):
    resp = await client.post(f"{BASE}/login", json={
        "email": "testuser@example.com",
        "password": "Secure@123",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data


async def test_login_wrong_password(client: AsyncClient, registered: dict):
    resp = await client.post(f"{BASE}/login", json={
        "email": "testuser@example.com",
        "password": "WrongPass@999",
    })
    assert resp.status_code == 401
    # Generic message — must not say "wrong password" or "user not found"
    assert "incorrect" in resp.json()["detail"].lower()


async def test_login_nonexistent_email(client: AsyncClient):
    resp = await client.post(f"{BASE}/login", json={
        "email": "ghost@example.com",
        "password": "Secure@123",
    })
    assert resp.status_code == 401


async def test_login_missing_fields(client: AsyncClient):
    resp = await client.post(f"{BASE}/login", json={"email": "x@x.com"})
    assert resp.status_code == 422


# ─────────────────────────────────────────────────────────────────────────────
#  Token refresh
# ─────────────────────────────────────────────────────────────────────────────

async def test_refresh_success(client: AsyncClient, registered: dict):
    resp = await client.post(f"{BASE}/refresh", json={
        "refresh_token": registered["refresh_token"]
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data
    # New tokens must differ from old ones
    assert data["access_token"] != registered["access_token"]
    assert data["refresh_token"] != registered["refresh_token"]


async def test_refresh_old_token_revoked_after_rotation(
    client: AsyncClient, registered: dict
):
    """Using the same refresh token twice should fail on the second call."""
    original_rt = registered["refresh_token"]

    r1 = await client.post(f"{BASE}/refresh", json={"refresh_token": original_rt})
    assert r1.status_code == 200

    r2 = await client.post(f"{BASE}/refresh", json={"refresh_token": original_rt})
    assert r2.status_code == 401


async def test_refresh_invalid_token(client: AsyncClient):
    resp = await client.post(f"{BASE}/refresh", json={
        "refresh_token": "this.is.not.a.valid.jwt"
    })
    assert resp.status_code == 401


async def test_refresh_access_token_rejected(client: AsyncClient, registered: dict):
    """An access token must not work as a refresh token."""
    resp = await client.post(f"{BASE}/refresh", json={
        "refresh_token": registered["access_token"]
    })
    assert resp.status_code == 401


# ─────────────────────────────────────────────────────────────────────────────
#  Logout
# ─────────────────────────────────────────────────────────────────────────────

async def test_logout_success(client: AsyncClient, registered: dict):
    resp = await client.post(f"{BASE}/logout", json={
        "refresh_token": registered["refresh_token"]
    })
    assert resp.status_code == 200
    assert "logged out" in resp.json()["message"].lower()


async def test_logout_then_refresh_fails(client: AsyncClient, registered: dict):
    """After logout, the refresh token must not work."""
    rt = registered["refresh_token"]
    await client.post(f"{BASE}/logout", json={"refresh_token": rt})

    resp = await client.post(f"{BASE}/refresh", json={"refresh_token": rt})
    assert resp.status_code == 401


async def test_logout_idempotent(client: AsyncClient, registered: dict):
    """Calling logout twice with the same token should still return 200."""
    rt = registered["refresh_token"]
    r1 = await client.post(f"{BASE}/logout", json={"refresh_token": rt})
    r2 = await client.post(f"{BASE}/logout", json={"refresh_token": rt})
    assert r1.status_code == 200
    assert r2.status_code == 200


# ─────────────────────────────────────────────────────────────────────────────
#  Protected: /me and /verify-token
# ─────────────────────────────────────────────────────────────────────────────

async def test_get_me_success(client: AsyncClient, auth_headers: dict):
    resp = await client.get(f"{BASE}/me", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["email"] == "testuser@example.com"
    assert "password" not in data
    assert "password_hash" not in data


async def test_get_me_no_token(client: AsyncClient):
    resp = await client.get(f"{BASE}/me")
    assert resp.status_code == 401


async def test_get_me_invalid_token(client: AsyncClient):
    resp = await client.get(
        f"{BASE}/me",
        headers={"Authorization": "Bearer invalid.token.here"},
    )
    assert resp.status_code == 401


async def test_verify_token_success(client: AsyncClient, auth_headers: dict):
    resp = await client.get(f"{BASE}/verify-token", headers=auth_headers)
    assert resp.status_code == 200
    assert "valid" in resp.json()["message"].lower()


async def test_verify_token_expired_or_bad(client: AsyncClient):
    resp = await client.get(
        f"{BASE}/verify-token",
        headers={"Authorization": "Bearer tampered.token.value"},
    )
    assert resp.status_code == 401


# ─────────────────────────────────────────────────────────────────────────────
#  Change password
# ─────────────────────────────────────────────────────────────────────────────

async def test_change_password_success(client: AsyncClient, auth_headers: dict):
    resp = await client.post(
        f"{BASE}/change-password",
        headers=auth_headers,
        json={
            "current_password": "Secure@123",
            "new_password": "NewSecure@456",
            "confirm_new_password": "NewSecure@456",
        },
    )
    assert resp.status_code == 200
    assert "updated" in resp.json()["message"].lower()


async def test_change_password_wrong_current(client: AsyncClient, auth_headers: dict):
    resp = await client.post(
        f"{BASE}/change-password",
        headers=auth_headers,
        json={
            "current_password": "WrongCurrent@999",
            "new_password": "NewSecure@789",
            "confirm_new_password": "NewSecure@789",
        },
    )
    assert resp.status_code == 401


async def test_change_password_same_as_current(
    client: AsyncClient, auth_headers: dict
):
    resp = await client.post(
        f"{BASE}/change-password",
        headers=auth_headers,
        json={
            "current_password": "Secure@123",
            "new_password": "Secure@123",
            "confirm_new_password": "Secure@123",
        },
    )
    assert resp.status_code == 400


async def test_change_password_mismatch(client: AsyncClient, auth_headers: dict):
    resp = await client.post(
        f"{BASE}/change-password",
        headers=auth_headers,
        json={
            "current_password": "Secure@123",
            "new_password": "NewSecure@456",
            "confirm_new_password": "DifferentNew@789",
        },
    )
    assert resp.status_code == 422


async def test_change_password_requires_auth(client: AsyncClient):
    resp = await client.post(
        f"{BASE}/change-password",
        json={
            "current_password": "Secure@123",
            "new_password": "NewSecure@456",
            "confirm_new_password": "NewSecure@456",
        },
    )
    assert resp.status_code == 401
