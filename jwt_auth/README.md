# JWT Authentication System — FastAPI

A complete, production-ready JWT authentication backend built with FastAPI,
SQLAlchemy 2 (async), and PostgreSQL. Every security decision is documented
inline in the source code.

---

## Features

| Feature | Detail |
|---|---|
| **Signup** | Email + username uniqueness, bcrypt password hashing (rounds=12), strength validation |
| **Login** | Timing-safe credential check, generic error messages (prevents user enumeration) |
| **Access tokens** | Short-lived JWT (15 min), carries `sub`, `role`, `email`, `type` claims |
| **Refresh tokens** | Long-lived (7 days), stored as SHA-256 hash in DB, rotated on every use |
| **Token rotation** | Old refresh token revoked immediately; reuse triggers full session revocation |
| **Logout** | Revokes refresh token; idempotent |
| **Change password** | Re-authenticates first; revokes all refresh tokens on success |
| **Protected routes** | `CurrentActiveUser` dependency; role guards via `require_role()` |
| **Security headers** | `X-Content-Type-Options`, `X-Frame-Options`, `Cache-Control: no-store` |
| **Request IDs** | Every response carries `X-Request-ID` for tracing |

---

## Project Structure

```
jwt_auth/
├── app/
│   ├── core/
│   │   ├── config.py        # Settings (pydantic-settings, .env)
│   │   ├── security.py      # bcrypt hashing, JWT create/decode, token hash
│   │   ├── dependencies.py  # FastAPI DI: get_db, get_current_user, require_role
│   │   └── exceptions.py    # Typed HTTP exception classes
│   ├── db/
│   │   ├── base.py          # DeclarativeBase + UUIDMixin + TimestampMixin
│   │   ├── session.py       # Async engine + session factory
│   │   └── init_db.py       # Create tables on startup
│   ├── models/
│   │   └── user.py          # User + RefreshToken ORM models
│   ├── schemas/
│   │   └── auth.py          # Pydantic request/response schemas
│   ├── routers/
│   │   ├── auth.py          # /auth/* endpoints
│   │   └── protected.py     # /protected/* demo endpoints
│   ├── services/
│   │   └── auth_service.py  # All business logic
│   └── main.py              # App factory, middleware, lifespan
├── alembic/                 # Database migrations
├── tests/
│   ├── conftest.py          # Fixtures (in-memory SQLite, HTTP client)
│   ├── test_auth.py         # Auth endpoint tests (30+ cases)
│   ├── test_protected.py    # Role-based access tests
│   └── test_security.py     # Unit tests for cryptographic functions
├── Dockerfile
├── docker-compose.yml
├── alembic.ini
├── pytest.ini
├── requirements.txt
└── .env.example
```

---

## Quick Start

### Docker (recommended)

```bash
cp .env.example .env
# Edit .env — set SECRET_KEY to: openssl rand -hex 32

docker compose up --build
```

API: `http://localhost:8000`
Docs: `http://localhost:8000/docs`

### Local

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env   # configure DATABASE_URL and SECRET_KEY

# Start Postgres
docker compose up db -d

# Run migrations
alembic upgrade head

# Start server
uvicorn app.main:app --reload
```

---

## Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `DATABASE_URL` | Yes | SQLite (dev) | `postgresql+asyncpg://user:pass@host/db` |
| `SECRET_KEY` | Yes | insecure default | Generate: `openssl rand -hex 32` |
| `ALGORITHM` | No | `HS256` | JWT signing algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | No | `15` | Access token TTL |
| `REFRESH_TOKEN_EXPIRE_DAYS` | No | `7` | Refresh token TTL |
| `DEBUG` | No | `False` | Enable SQL logging |

---

## API Endpoints

All endpoints are prefixed with `/api/v1`.

### Public (no token required)

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/auth/signup` | Register new account |
| `POST` | `/auth/login` | Login, get token pair |
| `POST` | `/auth/refresh` | Rotate refresh token |
| `POST` | `/auth/logout` | Revoke refresh token |

### Protected (Bearer access token required)

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/auth/me` | Current user profile |
| `GET` | `/auth/verify-token` | Validate token (returns 200 or 401) |
| `POST` | `/auth/change-password` | Update password, revoke all sessions |
| `GET` | `/protected/user-only` | Any authenticated user |
| `GET` | `/protected/profile` | Full user object |
| `GET` | `/protected/token-claims` | Decoded JWT payload |
| `GET` | `/protected/admin-only` | role=admin only |
| `GET` | `/protected/moderator-plus` | role=admin or moderator |
| `GET` | `/protected/clinician-only` | role=clinician or admin |

---

## Authentication Flow

```
1. Signup / Login
   POST /auth/signup  →  { access_token, refresh_token }
   POST /auth/login   →  { access_token, refresh_token }

2. Authenticated requests
   GET /api/v1/protected/user-only
   Authorization: Bearer <access_token>

3. Access token expired (after 15 min)
   POST /auth/refresh
   Body: { "refresh_token": "..." }
   →  { new access_token, new refresh_token }
   (old refresh token is revoked immediately)

4. Logout
   POST /auth/logout
   Body: { "refresh_token": "..." }
   →  token revoked; client discards access token locally
```

---

## Password Requirements

Passwords must be **8–128 characters** and contain at least:
- One uppercase letter (`A-Z`)
- One lowercase letter (`a-z`)
- One digit (`0-9`)
- One special character (`@$!%*?&_-#^`)

---

## Role-Based Access Control

Roles are stored on the `User` model and embedded in the access token payload.

```python
# In any route file:
from app.core.dependencies import require_role
from typing import Annotated
from fastapi import Depends
from app.models.user import User

@router.get("/admin-only")
async def admin_route(
    user: Annotated[User, Depends(require_role("admin"))]
):
    ...
```

Built-in aliases in `dependencies.py`:

```python
AdminUser     = Annotated[User, Depends(require_role("admin"))]
ModeratorUser = Annotated[User, Depends(require_role("admin", "moderator"))]
```

To assign a role, update the `role` column directly via DB or an admin API.

---

## Running Tests

```bash
# All tests (uses in-memory SQLite — no DB required)
pytest

# With coverage
pytest --cov=app --cov-report=html

# Specific file
pytest tests/test_security.py -v

# Unit tests only (fastest)
pytest tests/test_security.py
```

**Test counts:**
- `test_security.py` — 16 unit tests (no DB, no HTTP)
- `test_auth.py` — 24 integration tests
- `test_protected.py` — 12 integration tests

---

## Database Migrations

```bash
# Auto-generate after model changes
alembic revision --autogenerate -m "add_avatar_url_to_users"

# Apply
alembic upgrade head

# Rollback one
alembic downgrade -1

# History
alembic history --verbose
```

---

## Security Notes

| Concern | Mitigation |
|---|---|
| Password storage | bcrypt with work factor 12 — never stored plain |
| User enumeration | Generic "incorrect email or password" on login failure |
| Token theft | Refresh token rotation — reuse triggers full revocation |
| Token confusion | `type` claim (`access`/`refresh`) checked on every decode |
| DB breach | Refresh tokens stored as SHA-256 hashes only |
| Session hijack | Short-lived access tokens (15 min); change-password revokes all sessions |
| CORS | Configurable; defaults to `localhost:3000` and `localhost:5173` |
| Clickjacking | `X-Frame-Options: DENY` header on all responses |
| Cache poisoning | `Cache-Control: no-store` on all responses |

---

## Extending

### Add email verification

1. Add `verification_token` column to `User`
2. Add `POST /auth/verify-email?token=...` route
3. Send email in `AuthService.signup()` using FastAPI-Mail or SMTP

### Add password reset

1. Add `reset_token_hash` + `reset_token_expires_at` to `User`
2. Add `POST /auth/forgot-password` (generate + email token)
3. Add `POST /auth/reset-password` (verify token, update hash, revoke sessions)

### Add OAuth2 (Google / GitHub)

Use `authlib` or `python-social-auth` alongside the existing JWT system.
Issue the same JWT pair after successful OAuth callback.
