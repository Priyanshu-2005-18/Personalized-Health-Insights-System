"""
conftest.py
===========
Shared test fixtures. Uses in-memory SQLite — no Postgres required.
"""
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db.base import Base
from app.core.dependencies import get_db
from app.main import app

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"

_engine = create_async_engine(TEST_DB_URL, echo=False)
_SessionLocal = async_sessionmaker(_engine, class_=AsyncSession, expire_on_commit=False)


@pytest_asyncio.fixture(scope="session", autouse=True)
async def create_tables():
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db():
    async with _SessionLocal() as session:
        yield session


@pytest_asyncio.fixture
async def client(db: AsyncSession):
    async def _override():
        yield db

    app.dependency_overrides[get_db] = _override
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


# ── Registered user fixtures ───────────────────────────────────────────────────

USER_A = {
    "email": "alice@example.com",
    "username": "alice",
    "password": "Alice@Pass1",
    "full_name": "Alice Smith",
}

USER_B = {
    "email": "bob@example.com",
    "username": "bob",
    "password": "Bob@Pass123",
}


async def _register_and_login(client: AsyncClient, payload: dict) -> dict:
    await client.post("/api/v1/auth/signup", json=payload)
    resp = await client.post("/api/v1/auth/login", json={
        "email": payload["email"],
        "password": payload["password"],
    })
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def alice_headers(client: AsyncClient) -> dict:
    return await _register_and_login(client, USER_A)


@pytest_asyncio.fixture
async def bob_headers(client: AsyncClient) -> dict:
    return await _register_and_login(client, USER_B)
