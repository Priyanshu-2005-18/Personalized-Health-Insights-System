"""
conftest.py
===========
Shared pytest fixtures for the entire test suite.

Uses an in-memory SQLite database via aiosqlite so no PostgreSQL
instance is required to run tests.
"""

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db.base import Base
from app.core.dependencies import get_db
from app.main import app

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
_TestSession = async_sessionmaker(_engine, class_=AsyncSession, expire_on_commit=False)


# ── Create / drop schema once per session ──────────────────────────────────────

@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_db():
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


# ── Per-test DB session ────────────────────────────────────────────────────────

@pytest_asyncio.fixture
async def db():
    async with _TestSession() as session:
        yield session


# ── HTTP client with DB override ──────────────────────────────────────────────

@pytest_asyncio.fixture
async def client(db: AsyncSession):
    async def _override_get_db():
        yield db

    app.dependency_overrides[get_db] = _override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


# ── Convenience: pre-registered user ──────────────────────────────────────────

VALID_USER = {
    "email": "testuser@example.com",
    "username": "testuser",
    "password": "Secure@123",
    "confirm_password": "Secure@123",
    "full_name": "Test User",
}


@pytest_asyncio.fixture
async def registered(client: AsyncClient) -> dict:
    """Register a user and return the full signup response body."""
    resp = await client.post("/api/v1/auth/signup", json=VALID_USER)
    assert resp.status_code == 201, resp.text
    return resp.json()


@pytest_asyncio.fixture
def auth_headers(registered: dict) -> dict:
    """Return Authorization header for the registered test user."""
    return {"Authorization": f"Bearer {registered['access_token']}"}
