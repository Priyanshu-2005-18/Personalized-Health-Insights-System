# Health Tracking Module — FastAPI + PostgreSQL

A production-ready FastAPI module for tracking six daily health metrics per user,
with analytics, streak tracking, and full CRUD operations.

---

## Tracked Metrics

| Metric | Min | Max | Unit | Computed fields |
|---|---|---|---|---|
| `sleep_hours` | 0.0 | 24.0 | hours | `sleep_minutes` |
| `steps` | 0 | 100 000 | steps/day | — |
| `calories_consumed` | 0 | 10 000 | kcal | — |
| `water_intake_ml` | 0 | 10 000 | ml | `water_intake_glasses` |
| `stress_level` | 1 | 10 | subjective scale | `stress_label` |
| `heart_rate_bpm` | 30 | 250 | bpm (resting) | `heart_rate_zone` |

All metrics are **optional per entry** — log only what you have.
At least one metric must be present per submission.

---

## Project Structure

```
health_tracker/
├── app/
│   ├── core/
│   │   ├── config.py          # Settings via pydantic-settings + .env
│   │   ├── security.py        # JWT creation/verification, bcrypt hashing
│   │   ├── dependencies.py    # DB session DI, current-user DI
│   │   └── exceptions.py      # Typed HTTP exception classes
│   ├── db/
│   │   ├── base.py            # DeclarativeBase + UUIDMixin + TimestampMixin
│   │   ├── session.py         # Async SQLAlchemy engine + session factory
│   │   └── init_db.py         # Auto-create tables on startup
│   ├── models/
│   │   ├── user.py            # User ORM model
│   │   └── health_entry.py    # HealthEntry ORM model (6 metrics + computed props)
│   ├── schemas/
│   │   └── health_entry.py    # Pydantic schemas: Create, Update, Read, Summary
│   ├── routers/
│   │   ├── auth.py            # POST /auth/signup, POST /auth/login
│   │   └── health.py          # 9 health tracking endpoints
│   ├── services/
│   │   └── health_service.py  # All CRUD + analytics business logic
│   └── main.py                # App factory, middleware, lifespan
├── alembic/                   # Database migrations
├── tests/
│   ├── conftest.py            # Fixtures (in-memory SQLite, HTTP client)
│   ├── test_auth.py           # Auth endpoint tests
│   ├── test_health_crud.py    # CRUD tests (55+ cases)
│   └── test_health_analytics.py # Summary, streak, computed fields tests
├── api_examples.http          # REST Client file (33 example requests)
├── Dockerfile
├── docker-compose.yml
├── alembic.ini
├── pytest.ini
└── requirements.txt
```

---

## Quick Start

### Docker (one command)

```bash
cp .env.example .env
docker compose up --build
```

API: `http://localhost:8000`
Docs: `http://localhost:8000/docs`

### Local development

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env       # configure DATABASE_URL and SECRET_KEY

docker compose up db -d    # Postgres only
alembic upgrade head       # run migrations
uvicorn app.main:app --reload
```

---

## API Endpoints

All routes prefixed with `/api/v1`.

### Auth

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `POST` | `/auth/signup` | — | Create account |
| `POST` | `/auth/login` | — | Get access token |

### Health Tracking

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/health` | Log daily metrics |
| `GET` | `/health` | List entries (paginated + filtered) |
| `GET` | `/health/today` | Today's entry shortcut |
| `GET` | `/health/summary` | Aggregate statistics over date range |
| `GET` | `/health/streak` | Current + longest logging streak |
| `GET` | `/health/date/{date}` | Entry for a specific date |
| `GET` | `/health/{id}` | Entry by UUID |
| `PATCH` | `/health/{id}` | Partial update |
| `DELETE` | `/health/{id}` | Delete entry |

---

## Usage Flow

```bash
# 1. Create account
curl -X POST http://localhost:8000/api/v1/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"email":"you@example.com","username":"you","password":"You@12345"}'

# 2. Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"you@example.com","password":"You@12345"}'
# → copy access_token

# 3. Log today's health
curl -X POST http://localhost:8000/api/v1/health \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "entry_date": "2024-06-15",
    "sleep_hours": 7.5,
    "steps": 9200,
    "calories_consumed": 2100,
    "water_intake_ml": 2500,
    "stress_level": 4,
    "heart_rate_bpm": 68
  }'

# 4. Get weekly summary
curl "http://localhost:8000/api/v1/health/summary?start_date=2024-06-09&end_date=2024-06-15" \
  -H "Authorization: Bearer YOUR_TOKEN"

# 5. Check streak
curl http://localhost:8000/api/v1/health/streak \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## Validation Rules

### Per-metric constraints (enforced at Pydantic + DB level)

| Metric | Constraint | Error |
|---|---|---|
| `sleep_hours` | `0.0 ≤ x ≤ 24.0` | 422 |
| `steps` | `0 ≤ x ≤ 100 000` | 422 |
| `calories_consumed` | `0 ≤ x ≤ 10 000` | 422 |
| `water_intake_ml` | `0 ≤ x ≤ 10 000` | 422 |
| `stress_level` | `1 ≤ x ≤ 10` | 422 |
| `heart_rate_bpm` | `30 ≤ x ≤ 250` | 422 |

### Business rules

| Rule | HTTP error |
|---|---|
| One entry per user per date | 409 Conflict |
| At least one metric per submission | 422 Unprocessable |
| At least one field per PATCH | 422 Unprocessable |
| Can't access another user's entry | 403 Forbidden |
| `start_date` after `end_date` in summary | 400 Bad Request |

---

## Computed Fields (auto-calculated, never submitted)

```json
{
  "sleep_hours": 7.5,
  "sleep_minutes": 450,

  "water_intake_ml": 2500,
  "water_intake_glasses": 10.0,

  "stress_level": 4,
  "stress_label": "Mild",

  "heart_rate_bpm": 68,
  "heart_rate_zone": "Excellent (60–70 bpm)"
}
```

**Stress labels:** `Low` (1–2) · `Mild` (3–4) · `Moderate` (5–6) · `High` (7–8) · `Extreme` (9–10)

**Heart rate zones:** `Athlete` (<60) · `Excellent` (60–70) · `Good` (71–80) · `Above average` (81–90) · `High normal` (91–100) · `Elevated` (>100)

---

## List Filters

```
GET /api/v1/health?start_date=2024-06-01&end_date=2024-06-30
GET /api/v1/health?min_sleep_hours=7
GET /api/v1/health?max_stress_level=4
GET /api/v1/health?min_steps=8000
GET /api/v1/health?source=fitbit
GET /api/v1/health?page=2&size=10
```

Filters combine: `?start_date=...&max_stress_level=4&min_steps=5000`

---

## Summary Response Example

```json
{
  "period_start": "2024-06-01",
  "period_end": "2024-06-30",
  "total_entries": 22,
  "avg_sleep_hours": 7.18,
  "min_sleep_hours": 5.0,
  "max_sleep_hours": 9.0,
  "avg_steps": 8432.0,
  "total_steps": 185504,
  "max_steps": 14200,
  "avg_calories_consumed": 2050.0,
  "total_calories_consumed": 45100,
  "avg_water_intake_ml": 2250.0,
  "total_water_intake_ml": 49500,
  "avg_stress_level": 3.86,
  "min_stress_level": 1,
  "max_stress_level": 8,
  "avg_heart_rate_bpm": 67.5,
  "min_heart_rate_bpm": 58,
  "max_heart_rate_bpm": 88
}
```

---

## Running Tests

```bash
# All tests — uses in-memory SQLite, no Postgres needed
pytest

# With coverage
pytest --cov=app --cov-report=html

# Specific file
pytest tests/test_health_crud.py -v

# Fast unit-only (no HTTP)
pytest tests/test_auth.py
```

**Test coverage:** 65+ test cases across:
- `test_auth.py` — signup, login, bad token (7 tests)
- `test_health_crud.py` — full CRUD, boundary values, ownership (40+ tests)
- `test_health_analytics.py` — summary, streak, computed fields (20+ tests)

---

## Database Migrations

```bash
# Auto-generate after model changes
alembic revision --autogenerate -m "add_bmi_column"

# Apply all pending
alembic upgrade head

# Rollback one
alembic downgrade -1
```

---

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | SQLite (dev) | `postgresql+asyncpg://user:pass@host/db` |
| `SECRET_KEY` | insecure | Generate: `openssl rand -hex 32` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `15` | JWT access token TTL |
| `DEBUG` | `False` | Enable SQL query logging |

---

## Example API Requests

Open `api_examples.http` in VS Code with the
[REST Client](https://marketplace.visualstudio.com/items?itemName=humao.rest-client)
extension, or in JetBrains IDEs natively.

Contains 33 ready-to-run example requests covering every endpoint,
all filter combinations, and all error cases.
