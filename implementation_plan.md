# Implementation Plan — Personalized Health Insights System Integration

This plan details how to connect the React frontend, FastAPI backend, PostgreSQL database, ML model, and recommendation engine into a fully working, unified application.

## User Review Required

> [!IMPORTANT]
> The original codebase was built as a series of standalone microservice prototypes (`health_backend`, `jwt_auth`, `recommendation_engine`, `health_tracker`).
> To unify the system cleanly and prevent port conflicts (since multiple modules try to run on port 8000), we will integrate all features directly into **`health_backend`** as the single unified FastAPI service.
> 
> The database tables will be created automatically in PostgreSQL on startup. We will add columns to the `health_logs` table to store all 6 health metrics (sleep, steps, calories, heart rate, stress, and predicted health score) in a single row per day.

## Proposed Changes

### Backend: Models, Schemas, Services and API

---

#### [MODIFY] [health_log.py](file:///c:/Users/prasa/Desktop/Project/Personalized%20Health%20Insights%20System/health_backend/app/models/health_log.py)
- Import `Numeric` from `sqlalchemy`.
- Add columns:
  - `sleep_hours: Mapped[Optional[float]] = mapped_column(Numeric(4, 2), nullable=True)`
  - `steps: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)`
  - `calories: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)`
  - `heart_rate_bpm: Mapped[Optional[int]] = mapped_column(SmallInteger, nullable=True)`
  - `health_score: Mapped[Optional[float]] = mapped_column(Numeric(5, 2), nullable=True)`
- Add DB-level `CheckConstraint` check rules for the new fields (e.g. `sleep_hours` between 0 and 24, `steps` between 0 and 100k, etc.).

#### [MODIFY] [health_log.py](file:///c:/Users/prasa/Desktop/Project/Personalized%20Health%20Insights%20System/health_backend/app/schemas/health_log.py)
- Update `HealthLogCreate` and `HealthLogUpdate` to accept:
  - `sleep_hours` (float)
  - `steps` (int)
  - `calories` (int)
  - `heart_rate_bpm` (int)
- Update `HealthLogRead` to return all the above plus `health_score` (float).

#### [MODIFY] [predictor.py](file:///c:/Users/prasa/Desktop/Project/Personalized%20Health%20Insights%20System/health_backend/app/ml/predictor.py)
- Fix the joblib deserialization issue by copying the `HealthFeatureEngineer` custom transformer code to `app/ml/feature_engineering.py` and register it into `sys.modules['feature_engineering']` before loading the model.

#### [NEW] [feature_engineering.py](file:///c:/Users/prasa/Desktop/Project/Personalized%20Health%20Insights%20System/health_backend/app/ml/feature_engineering.py)
- Create local copy of `HealthFeatureEngineer` class with `FEATURES` hardcoded to resolve the missing dependency inside the container.

#### [NEW] [recommendation_engine](file:///c:/Users/prasa/Desktop/Project/Personalized%20Health%20Insights%20System/health_backend/app/recommendation_engine)
- Copy all files from `recommendation_engine/app/` into `health_backend/app/recommendation_engine/`:
  - `models/health.py`
  - `schemas/health.py`
  - `services/scorer.py`
  - `services/recommendation_service.py`
  - `rules/` (all python files: sleep, activity, nutrition, hydration, stress, heart rate, thresholds, etc.)
- Rewrite relative imports inside `app/recommendation_engine/` from `app.` prefix to `app.recommendation_engine.` prefix to make them work correctly.

#### [NEW] [recommendations.py](file:///c:/Users/prasa/Desktop/Project/Personalized%20Health%20Insights%20System/health_backend/app/api/v1/recommendations.py)
- Create `/recommendations` and `/recommendations/quick` FastAPI endpoints to expose the recommendation engine outputs directly on `health_backend`.

#### [MODIFY] [router.py](file:///c:/Users/prasa/Desktop/Project/Personalized%20Health%20Insights%20System/health_backend/app/api/v1/router.py)
- Include the new `/recommendations` router.

#### [MODIFY] [health_log_service.py](file:///c:/Users/prasa/Desktop/Project/Personalized%20Health%20Insights%20System/health_backend/app/services/health_log_service.py)
- In both `create` and `update` methods:
  - Retrieve the submitted metrics.
  - Call the ML pipeline `HealthScorePredictor.get_instance().predict_single(...)` to predict the overall health score.
  - Store the predicted score under `health_score` in the database.
  - Call the recommendation engine `generate_recommendations(...)` to get the list of recommendations.
  - Save the recommendations to the `recommendations` and `recommendation_actions` database tables.

---

### Frontend: Form Submission

#### [MODIFY] [HealthFormPage.tsx](file:///c:/Users/prasa/Desktop/Project/Personalized%20Health%20Insights%20System/health_frontend/health_frontend/src/pages/HealthFormPage.tsx)
- Update `handleSubmit` to include `sleep_hours`, `steps`, `calories`, and `heart_rate_bpm` inside the payload sent to `healthApi.createLog` / `healthApi.updateLog`.

---

### Configuration and Compose Files

#### [MODIFY] [docker-compose.yml](file:///c:/Users/prasa/Desktop/Project/Personalized%20Health%20Insights%20System/health_backend/docker-compose.yml)
- Ensure PostgreSQL env vars are configured correctly and that the database container exposes port 5432.
- Remove redundant services or ensure the backend runs perfectly.

---

## Verification Plan

### Automated Tests
- Run `pytest` inside the backend directory:
  `python -m pytest tests/`

### Manual Verification
- Launch the backend with docker-compose:
  `docker compose up --build`
- Launch the frontend:
  `npm run dev`
- Run the workflow:
  1. Register a new user account.
  2. Log in to the application.
  3. Navigate to "Log Health Data".
  4. Submit test values for all metrics.
  5. Go to "Recommendations" to verify:
     - Health Score ring displays the correct predicted score.
     - Metric radar chart and trend chart render correctly.
     - Personalised recommendations and action cards are shown.
     - Data is properly persisted in PostgreSQL.
