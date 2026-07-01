# 🏥 Personalized Health Insights System

A full-stack, AI-powered health tracking and recommendation platform. Users log daily health metrics — sleep, activity, nutrition, hydration, stress, and heart rate — and receive a machine-learning-predicted health score alongside personalised, evidence-based recommendations.

---

## 📁 Project Structure

```
personalized-health-insights/
│
├── health_backend/          # FastAPI REST API
├── health_frontend/         # React + Vite + Tailwind frontend
├── health_ml/               # Scikit-learn ML pipeline
├── health_tracker/          # Health tracking module
├── recommendation_engine/   # Rule-based recommendation system
├── jwt_auth/                # Standalone JWT authentication
└── HealthDashboard.jsx      # Standalone React dashboard component
```

---

## 🗂️ Module Overview

| Module | Tech | Purpose |
|---|---|---|
| `health_backend` | FastAPI · PostgreSQL · SQLAlchemy | REST API, auth, CRUD for all health data |
| `health_frontend` | React 18 · Vite · Tailwind · Recharts | 6-page SPA with charts and forms |
| `health_ml` | Python · Scikit-learn · Pandas | ML pipeline predicting health score (0–100) |
| `health_tracker` | FastAPI · PostgreSQL | Standalone health metric tracking module |
| `recommendation_engine` | Python · FastAPI | Rule-based engine, 29 rules across 6 domains |
| `jwt_auth` | FastAPI · JWT · bcrypt | Standalone JWT auth with refresh token rotation |
| `HealthDashboard.jsx` | React · Recharts | Standalone dark-mode dashboard component |

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Node.js 20+
- PostgreSQL 16+
- Docker + Docker Compose (optional but recommended)

### 1. Clone the Repository

```bash
git clone https://github.com/Priyanshu-2005-18/Personalized-Health-Insights-System.git
cd Personalized-Health-Insights-System
```

---

### 2. Start the Backend

```bash
cd health_backend

# Create virtual environment (first time only)
python -m venv venv

# Activate virtual environment

# Windows
venv\Scripts\activate

# Linux / macOS
source venv/bin/activate

# Install dependencies (first time only)
pip install -r requirements.txt

# Create environment file
cp .env.example .env
# (Windows: copy .env.example .env)

# Run database migrations
alembic upgrade head

# Start FastAPI server
uvicorn app.main:app --reload
```

Backend will run at:

```
http://localhost:8000
```

Swagger Documentation:

```
http://localhost:8000/docs
```

---

### 3. (Optional) Train ML Models

Only required if you want to retrain the machine learning models.

```bash
cd health_ml

pip install -r requirements.txt

python -c "from src.pipeline import run_pipeline; run_pipeline()"
```

Trained models will be saved inside:

```
health_ml/models/
```

---

### 4. Start the Frontend

Open a **new terminal**.

```bash
cd health_frontend

npm install

npm run dev
```

Frontend will run at:

```
http://localhost:5173
```

---

## Project Startup Order

Always start the services in this order:

1. Backend
2. Frontend
3. (Optional) ML Training

The recommendation engine is integrated into the backend and starts automatically with FastAPI.

---

## 🔧 Module Details

### 1. `health_backend` — FastAPI Backend

Production-ready REST API built with FastAPI, async SQLAlchemy 2, and PostgreSQL.

**Key features:**
- JWT authentication with refresh token rotation (bcrypt, 15 min access / 7 day refresh)
- 8 fully normalised database modules (3NF throughout)
- Async endpoints with connection pooling
- Alembic migrations
- Docker multi-stage build

**API base:** `http://localhost:8000/api/v1`

| Group | Endpoints | Description |
|---|---|---|
| Auth | `/auth/signup` `/auth/login` `/auth/refresh` `/auth/logout` | JWT lifecycle |
| Users | `/users/me` `/users/me/profile` | Account + health profile |
| Health logs | `/health/logs` | Daily mood, stress, energy, water |
| Sleep | `/sleep` | Sleep session tracking |
| Activity | `/activity` | Workout and step tracking |
| Nutrition | `/nutrition` | Meal and macro logging |
| Insights | `/insights` `/insights/generate` | ML recommendations |

**Database tables:** `users`, `refresh_tokens`, `user_profiles`, `health_logs`, `sleep_logs`, `activity_logs`, `nutrition_logs`, `nutrition_items`, `recommendations`, `recommendation_actions`, `notifications`

```bash
cd health_backend
cp .env.example .env
docker compose up --build
```

---

### 2. `health_frontend` — React SPA

68-file React 18 frontend with TypeScript, Tailwind CSS, and Recharts.

**Pages:**

| Route | Page | Description |
|---|---|---|
| `/login` | LoginPage | Email + password with demo credentials |
| `/register` | RegisterPage | Signup with password strength meter |
| `/dashboard` | DashboardPage | Score ring, 6 metric cards, trend charts |
| `/health-form` | HealthFormPage | Sliders and steppers for all 6 metrics |
| `/recommendations` | RecommendationsPage | Filterable cards with expandable action steps |
| `/profile` | ProfilePage | BMI gauge, health goals, personal details |

**Key components:**
- `ScoreRing` — animated SVG health score ring (0–100)
- `MetricRadarChart` — radar chart for 6-metric breakdown
- `HealthTrendChart` — 14-day score trend line chart
- `Modal`, `Tooltip`, `Tabs`, `Badge`, `Alert` — full UI system

```bash
cd health_frontend
cp .env.example .env    # VITE_API_URL=http://localhost:8000/api/v1
npm install && npm run dev
```

---

### 3. `health_ml` — Machine Learning Pipeline

End-to-end Scikit-learn pipeline predicting a 0–100 health score from 6 raw metrics.

**Pipeline steps:**

```
Raw data → Validation → Imputation → Outlier capping
         → Feature engineering (26 features from 6 raw)
         → Train/val/test split (70/15/15)
         → RobustScaler
         → Baseline comparison (6 models)
         → RandomizedSearchCV on top 2
         → Final test evaluation
         → joblib artifact saving
```

**Feature engineering categories:**
- Original 6 metrics
- Domain sub-scores (0–100 per metric)
- Interaction features (active_sleep_score, recovery_score, etc.)
- Ratio features (water_per_cal, sleep_per_stress)
- Polynomial features (sleep_hours², stress_level², log(steps))
- Binned features (sleep_category, activity_category, stress_category)

**Models compared:** Linear Regression, Ridge, Random Forest, Gradient Boosting, SVR, KNN

**Typical result:** Ridge Regression, R² ≈ 0.92, MAE ≈ ±2.3 score points

```bash
cd health_ml
pip install -r requirements.txt

# Train
python -c "from src.pipeline import run_pipeline; run_pipeline()"

# Predict
python -c "
from src.predictor import HealthScorePredictor
p = HealthScorePredictor()
print(p.predict_single({
    'sleep_hours': 7.5, 'steps': 9000, 'calories': 2100,
    'water_intake_ml': 2500, 'stress_level': 3, 'heart_rate_bpm': 65
}))
"
```

**Saved artifacts:**
```
health_ml/models/
├── best_model.joblib      # Trained estimator
├── scaler.joblib          # Fitted RobustScaler
├── feature_cols.joblib    # Ordered feature column names
├── imputer.joblib         # Fitted SimpleImputer
├── model_metadata.joblib  # Metrics, version, training info
└── evaluation_plots.png   # 6-panel evaluation figure
```

---

### 4. `recommendation_engine` — Rule-Based Engine

29 rules across 6 health categories producing prioritised, actionable recommendations.

**Categories and rules:**

| Category | Rules | Example triggers |
|---|---|---|
| Sleep (5) | critical_deprivation, poor, suboptimal, oversleeping, optimal | sleep < 5h → CRITICAL |
| Activity (5) | sedentary, low, moderate, active, highly_active | steps < 2,500 → CRITICAL |
| Hydration (4) | severe, dehydrated, below_target, well_hydrated | water < 1,000ml → CRITICAL |
| Stress (5) | extreme, high, moderate, mild, low | stress = 10 → CRITICAL |
| Nutrition (5) | critical_low, low, optimal, high, very_high | calories < 1,200 → CRITICAL |
| Heart Rate (5) | elevated, above_normal, normal, good, athlete | HR > 100 bpm → HIGH |

**Compound rules:** High stress + poor sleep → combined risk warning; active user + high calories → athlete-adjusted advice.

**API:**
```bash
POST http://localhost:8001/api/v1/recommendations
{
  "sleep_hours": 5.5,
  "steps": 3200,
  "stress_level": 8,
  "heart_rate_bpm": 92
}
```

```bash
cd recommendation_engine
pip install fastapi uvicorn pydantic
uvicorn app.main:app --port 8001 --reload
# Docs → http://localhost:8001/docs

# Run 130 tests (no server needed)
python -m unittest discover -s tests -v
```

---

### 5. `jwt_auth` — JWT Authentication Module

Standalone production-ready JWT authentication with refresh token rotation.

**Security features:**
- bcrypt password hashing (rounds=12)
- Access tokens: 15 min, carry `sub`, `role`, `email`, `type` claims
- Refresh tokens: 7 days, stored as SHA-256 hash in DB (never plaintext)
- Token rotation: old refresh revoked on every use
- Token reuse detection: triggers full session revocation
- Generic error messages on login (prevents user enumeration)
- Timing-safe password comparison

**Endpoints:**
```
POST /api/v1/auth/register        Create account
POST /api/v1/auth/login           Get token pair
POST /api/v1/auth/refresh         Rotate refresh token
POST /api/v1/auth/logout          Revoke refresh token
GET  /api/v1/auth/me              Current user (protected)
GET  /api/v1/auth/verify-token    Validate access token
POST /api/v1/auth/change-password Update password + revoke all sessions
```

```bash
cd jwt_auth
pip install -r requirements.txt
cp .env.example .env    # set SECRET_KEY=openssl rand -hex 32
uvicorn app.main:app --reload

# Run 52 tests
python -m unittest discover -s tests -v
```

---

### 6. `health_tracker` — Health Tracking Module

Standalone FastAPI module for the 6 core health metrics with full CRUD and analytics.

**Tracked metrics:**

| Metric | Range | Unit | Computed |
|---|---|---|---|
| `sleep_hours` | 0–24 | hours | `sleep_minutes` |
| `steps` | 0–100,000 | steps/day | — |
| `calories` | 0–10,000 | kcal | — |
| `water_intake_ml` | 0–10,000 | ml | `water_intake_glasses` |
| `stress_level` | 1–10 | scale | `stress_label` |
| `heart_rate_bpm` | 30–250 | bpm | `heart_rate_zone` |

**Endpoints:**
```
POST   /api/v1/health          Log metrics
GET    /api/v1/health          List (paginated + filtered)
GET    /api/v1/health/today    Today's entry shortcut
GET    /api/v1/health/summary  Aggregate stats over date range
GET    /api/v1/health/streak   Consecutive-day logging streak
PATCH  /api/v1/health/{id}     Partial update
DELETE /api/v1/health/{id}     Delete entry
```

```bash
cd health_tracker
pip install -r requirements.txt
uvicorn app.main:app --reload
# Docs → http://localhost:8000/docs

# Run 65+ tests (in-memory SQLite, no DB needed)
python -m unittest discover -s tests -v
```

---

### 7. `HealthDashboard.jsx` — Standalone Dashboard

A single self-contained React component (400 lines) that runs in any React project.

**Displays:**
- Animated health score ring (0–100) with colour-coded zones
- Sleep trend area chart (7/14/30 day)
- Activity bar chart with daily goal progress bar
- Stress trend line chart with gradient colour encoding
- 14-day score history sparkline
- Expandable recommendation cards with priority badges

**Requires:** `react`, `recharts` only.

```bash
# Drop into any React project:
cp HealthDashboard.jsx src/
```

```jsx
import HealthDashboard from './HealthDashboard'
export default function App() {
  return <HealthDashboard />
}
```

---

## 🗄️ Database Schema

14 PostgreSQL tables across 8 modules:

```
users ──────────────── user_profiles
     └── refresh_tokens
     └── health_logs
     └── sleep_logs
     └── activity_logs
     └── nutrition_logs ── nutrition_items
     └── recommendations ── recommendation_actions
     └── notifications
```

**Normalization:** 3NF throughout. Notable decisions:
- `nutrition_items` separate from `nutrition_logs` (1NF — no repeating food groups)
- `user_profiles` separate from `users` (2NF — no partial dependencies)
- `sleep_logs.duration_min` is a `GENERATED ALWAYS AS STORED` column
- `JSONB` columns for `sleep_stages` and `notifications.metadata`
- Partial indexes on `WHERE is_read = FALSE` for unread queries

Full schema SQL: `health_insights_schema.sql`

---

## 🤖 ML Integration Flow

```
User logs metrics (health_frontend)
         │
         ▼
POST /api/v1/insights/generate (health_backend)
         │
         ▼
Feature engineering (health_ml/src/features.py)
  6 raw features → 26 engineered features
         │
         ▼
ML inference (health_ml/models/best_model.joblib)
  Predicts health_score (0–100)
         │
         ▼
POST /api/v1/recommendations (recommendation_engine)
  29 rules → prioritised recommendations
         │
         ▼
Stored in recommendations table
Displayed on /recommendations page
```

---

## 🧪 Testing

| Module | Framework | Tests | Command |
|---|---|---|---|
| `health_backend` | pytest + httpx | 65+ | `pytest` |
| `health_frontend` | — (manual) | — | `npm run dev` |
| `health_ml` | unittest | 7 integration | `python -m unittest` |
| `health_tracker` | unittest | 65+ | `python -m unittest discover -s tests` |
| `recommendation_engine` | unittest | **130** | `python -m unittest discover -s tests -v` |
| `jwt_auth` | unittest | 52 | `python -m unittest discover -s tests -v` |

All test suites use **in-memory SQLite** — no database instance needed.

---

## 📊 Metrics & Performance

### ML Model Performance

| Metric | Value |
|---|---|
| Algorithm | Ridge Regression (best of 6) |
| R² (test) | **0.9205** |
| MAE (test) | **±2.26 score points** |
| 10-fold CV R² | 0.9073 ± 0.0094 |
| Features | 26 (engineered from 6 raw) |
| Training samples | 1,400 (70% of 2,000) |

### Recommendation Engine

| Metric | Value |
|---|---|
| Total rules | 29 |
| Health categories | 6 |
| Tests passing | 130/130 |
| Compound rules | 4 (cross-metric logic) |
| Max recommendations | 8 per request |
| Response time | < 5ms (pure rule evaluation) |

---

## 🔐 Environment Variables

### `health_backend/.env`

```env
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/health_insights_db
SECRET_KEY=                    # openssl rand -hex 32
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7
CORS_ORIGINS=["http://localhost:3000","http://localhost:5173"]
DEBUG=True
```

### `health_frontend/.env`

```env
VITE_API_URL=http://localhost:8000/api/v1
```

### `recommendation_engine/.env`

```env
APP_ENV=development
DEBUG=True
MAX_RECOMMENDATIONS=8
MAX_PER_CATEGORY=3
```

---

## 📚 Datasets

Suitable public datasets for training (instead of synthetic data):

| Domain | Dataset | Source | Size |
|---|---|---|---|
| Sleep | Sleep Health & Lifestyle | Kaggle | 400 rows |
| Sleep (clinical) | Sleep-EDF (PhysioNet) | physionet.org | 61 PSG recordings |
| Stress | WESAD | UCI ML Repo | 15 subjects |
| Stress (simple) | Human Stress Detection | Kaggle | 2,001 rows |
| Activity | PAMAP2 | UCI ML Repo | 3.85M samples |
| Activity | UCI HAR | UCI ML Repo | 10,299 samples |
| Nutrition | USDA FoodData Central | fdc.nal.usda.gov | 7,793+ foods |
| Nutrition | Food Nutrition Dataset | Kaggle | 1,000+ items |

---

## 🛣️ Roadmap

- [ ] Email verification during registration
- [ ] Password reset via email
- [ ] Wearable device integration (Google Fit, Apple Health, Fitbit)
- [ ] Push notifications for health reminders
- [ ] Advanced ML-based health trend prediction
- [ ] Admin dashboard with user analytics
- [ ] Mobile application (React Native)
- [ ] Export health reports as PDF

---

## 📄 License

MIT License — see `LICENSE` for details.

---

## 🙏 Acknowledgements

- [FastAPI](https://fastapi.tiangolo.com/) — modern Python web framework
- [Scikit-learn](https://scikit-learn.org/) — ML algorithms
- [Recharts](https://recharts.org/) — composable React charts
- [Tailwind CSS](https://tailwindcss.com/) — utility-first CSS
- [Zustand](https://github.com/pmndrs/zustand) — lightweight state management
- [PhysioNet](https://physionet.org/) — open health data
- [UCI ML Repository](https://archive.ics.uci.edu/) — WESAD, PAMAP2, HAR datasets
