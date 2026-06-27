# Personalized Health Insights System — Backend

A production-ready FastAPI backend for tracking sleep, activity, nutrition, and daily health metrics, with a Scikit-learn ML pipeline that generates personalised recommendations.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Framework | FastAPI 0.111 + Uvicorn |
| Database | PostgreSQL 16 + SQLAlchemy 2 (async) |
| Migrations | Alembic |
| Auth | JWT (access + refresh token rotation) |
| Cache | Redis |
| ML | Scikit-learn + NumPy + Pandas |
| Testing | Pytest + HTTPX (async) |
| Containers | Docker + Docker Compose |

---

## Project Structure

```
health_backend/
├── app/
│   ├── api/v1/          # Route handlers (auth, users, health, sleep, activity, nutrition, insights)
│   ├── core/            # Config, security, dependencies, exceptions
│   ├── db/              # SQLAlchemy engine, session, init
│   ├── ml/              # Feature engineering + inference pipeline
│   ├── models/          # SQLAlchemy ORM models
│   ├── schemas/         # Pydantic request/response schemas
│   ├── services/        # Business logic layer
│   └── main.py          # FastAPI app factory + lifespan
├── alembic/             # Database migrations
├── tests/               # Pytest test suite
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── pytest.ini
└── .env.example
```

---

## Quick Start

### 1. Clone and configure

```bash
git clone <repo-url>
cd health_backend
cp .env.example .env
# Edit .env — set SECRET_KEY and DATABASE_URL at minimum
```

### 2. Run with Docker Compose (recommended)

```bash
docker compose up --build
```

API available at `http://localhost:8000`
Interactive docs at `http://localhost:8000/docs`

### 3. Run locally (without Docker)

```bash
# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start PostgreSQL and Redis (via Docker or native)
docker compose up db redis -d

# Run migrations
alembic upgrade head

# Start the server
uvicorn app.main:app --reload --port 8000
```

---

## Environment Variables

| Variable | Description | Default |
|---|---|---|
| `DATABASE_URL` | Async PostgreSQL DSN | required |
| `SECRET_KEY` | JWT signing key (≥ 32 chars) | required |
| `REDIS_URL` | Redis connection URL | `redis://localhost:6379/0` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Access token TTL | `15` |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Refresh token TTL | `7` |
| `CORS_ORIGINS` | JSON array of allowed origins | `["http://localhost:3000"]` |
| `DEBUG` | Enable debug logging + SQL echo | `False` |
| `ML_MODEL_PATH` | Path to `.pkl` model files | `app/ml/models` |

---

## API Reference

All endpoints are prefixed with `/api/v1/`.
Full interactive documentation: `GET /docs`

### Authentication

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/auth/register` | Create account → returns tokens |
| `POST` | `/auth/login` | Email/password → returns tokens |
| `POST` | `/auth/refresh` | Rotate refresh token |
| `POST` | `/auth/logout` | Revoke refresh token |

### Users & Profile

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/users/me` | Current user details |
| `PATCH` | `/users/me` | Update email / status |
| `DELETE` | `/users/me` | Delete account |
| `GET` | `/users/me/profile` | Health profile |
| `POST` | `/users/me/profile` | Create profile |
| `PATCH` | `/users/me/profile` | Update profile |

### Health Logs

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/health/logs` | Submit daily log |
| `GET` | `/health/logs` | List logs (paginated) |
| `GET` | `/health/logs/today` | Today's log |
| `GET` | `/health/logs/{id}` | Single log |
| `PATCH` | `/health/logs/{id}` | Update log |
| `DELETE` | `/health/logs/{id}` | Delete log |

### Sleep / Activity / Nutrition

Each module follows the same pattern:

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/{module}` | Create log |
| `GET` | `/{module}` | List logs |
| `GET` | `/{module}/{id}` | Get single log |
| `DELETE` | `/{module}/{id}` | Delete log |

Modules: `sleep`, `activity`, `nutrition`

### Insights (ML Recommendations)

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/insights` | List recommendations |
| `GET` | `/insights/{id}` | Single recommendation |
| `POST` | `/insights/generate` | Run ML pipeline |
| `PATCH` | `/insights/{id}/read` | Mark as read |
| `PATCH` | `/insights/{id}/dismiss` | Dismiss |
| `PATCH` | `/insights/{id}/actions/{action_id}/complete` | Complete action step |

---

## Database Migrations

```bash
# Create a new migration after model changes
alembic revision --autogenerate -m "describe_your_change"

# Apply all pending migrations
alembic upgrade head

# Roll back one migration
alembic downgrade -1

# View migration history
alembic history
```

---

## Running Tests

```bash
# Run full test suite
pytest

# Run with coverage report
pytest --cov=app --cov-report=html

# Run a specific test file
pytest tests/test_auth.py -v

# Skip slow tests
pytest -m "not slow"
```

Tests use an **in-memory SQLite** database via `aiosqlite` — no PostgreSQL instance required.

---

## ML Pipeline

### How it works

1. `POST /api/v1/insights/generate` triggers the pipeline
2. Last 30 days of health, sleep, activity, and nutrition data are loaded
3. `app/ml/features.py` extracts 20 numeric features
4. `app/ml/pipeline.py` runs inference:
   - **If `.pkl` models exist** in `ML_MODEL_PATH` → Scikit-learn model predictions
   - **Otherwise** → rule-based engine (always active as a fallback)
5. Resulting `Recommendation` rows are persisted and returned

### Training your own models

```python
from app.ml.features import FEATURE_COLUMNS, build_feature_vector
from sklearn.ensemble import GradientBoostingClassifier
import joblib, numpy as np

# X: (n_samples, len(FEATURE_COLUMNS)), y: binary risk label
model = GradientBoostingClassifier()
model.fit(X_train, y_train)

# Save with the naming convention {category}_model.pkl
joblib.dump(model, "app/ml/models/sleep_model.pkl")
```

Supported model names: `sleep_model`, `activity_model`, `nutrition_model`, `stress_model`.

---

## Authentication Flow

```
Register / Login  →  access_token (15 min) + refresh_token (7 days, stored hashed)
Protected request →  Authorization: Bearer <access_token>
Token expired     →  POST /auth/refresh  →  new token pair (old refresh revoked)
Logout            →  POST /auth/logout   →  refresh token revoked in DB
```

Refresh tokens are stored as SHA-256 hashes. On every refresh call the old token is revoked and a new one issued (rotation strategy — detects token theft).

---

## Docker

```bash
# Build production image
docker build -t health-api:latest .

# Run with external DB
docker run -p 8000:8000 \
  -e DATABASE_URL=postgresql+asyncpg://user:pass@host/db \
  -e SECRET_KEY=your-secret-key \
  health-api:latest
```

---

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feat/my-feature`)
3. Write tests for new functionality
4. Ensure all tests pass (`pytest`)
5. Open a pull request
