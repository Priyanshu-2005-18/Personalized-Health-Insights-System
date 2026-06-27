# Health Insights API

ML-powered FastAPI service that accepts personal health metrics and returns a
personalised **health score (0–100)**, risk classification, domain breakdown,
and actionable recommendations.

---

## Project structure

```
health_api/
├── app/
│   ├── main.py                  # FastAPI app factory + lifespan
│   ├── routers/
│   │   └── health.py            # /predict, /predict/batch, /model/info, /health
│   ├── schemas/
│   │   └── health.py            # Pydantic request / response models
│   ├── services/
│   │   └── model_service.py     # joblib load, inference, domain scores, recs
│   └── middleware/
│       └── logging.py           # Request-ID + latency logging
├── ml/
│   ├── artifacts/
│   │   ├── health_score_model.joblib   # Serialised sklearn Pipeline
│   │   └── model_metrics.json          # MAE, R², CV R²
│   └── training/
│       └── train_model.py       # Training script
├── tests/
│   └── test_api.py              # Full pytest test suite
├── requirements.txt
└── README.md
```

---

## Quick start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Train and save the model
python ml/training/train_model.py

# 3. Start the API server
uvicorn app.main:app --reload --port 8000

# 4. Open interactive docs
open http://localhost:8000/docs
```

---

## API reference

### `POST /api/v1/predict`

Predict the health score for a single user.

**Request body**

| Field            | Type    | Range          | Description                            |
|------------------|---------|----------------|----------------------------------------|
| `sleep_hours`    | float   | 0 – 24         | Average nightly sleep (hours)          |
| `sleep_quality`  | float   | 1 – 10         | Self-rated sleep quality               |
| `steps_daily`    | float   | 0 – 100 000    | Average daily steps                    |
| `active_minutes` | float   | 0 – 1 440      | Weekly moderate-to-vigorous exercise   |
| `resting_hr`     | float   | 30 – 200       | Resting heart rate (bpm)               |
| `hrv`            | float   | 1 – 300        | Heart-rate variability — RMSSD (ms)    |
| `stress_index`   | float   | 0 – 100        | Stress index (0 = none, 100 = max)     |
| `water_intake`   | float   | 0 – 20         | Daily water intake (litres)            |
| `bmi`            | float   | 10 – 70        | Body-mass index (kg/m²)               |
| `user_id`        | string  | —              | Optional opaque user identifier        |

**Example request**

```bash
curl -X POST http://localhost:8000/api/v1/predict \
  -H "Content-Type: application/json" \
  -d '{
    "sleep_hours": 7.5,
    "sleep_quality": 7.0,
    "steps_daily": 9500,
    "active_minutes": 180,
    "resting_hr": 64,
    "hrv": 58,
    "stress_index": 35,
    "water_intake": 2.2,
    "bmi": 23.5,
    "user_id": "usr_abc123"
  }'
```

**Example response**

```json
{
  "health_score": 73.84,
  "risk_level": "moderate",
  "confidence": 1.0,
  "domain_scores": {
    "sleep": 83.3,
    "activity": 79.0,
    "cardio": 76.4,
    "stress": 65.0,
    "lifestyle": 91.0
  },
  "recommendations": [
    {
      "domain": "stress",
      "message": "Your stress index (35/100) is moderate. Consider scheduling daily 5-min mindfulness sessions.",
      "priority": "medium"
    }
  ],
  "model_version": "1.0.0",
  "user_id": "usr_abc123"
}
```

---

### `POST /api/v1/predict/batch`

Score up to 50 records in one request.

```bash
curl -X POST http://localhost:8000/api/v1/predict/batch \
  -H "Content-Type: application/json" \
  -d '{"records": [{...}, {...}]}'
```

**Response**
```json
{
  "results": [ { "health_score": 73.84, ... }, { "health_score": 41.2, ... } ],
  "total": 2
}
```

---

### `GET /api/v1/model/info`

```json
{
  "model_version": "1.0.0",
  "feature_names": ["sleep_hours", "sleep_quality", "steps_daily", ...],
  "mae": 2.043,
  "r2": 0.8648,
  "cv_r2_mean": 0.879,
  "train_samples": 1600,
  "test_samples": 400,
  "status": "loaded"
}
```

---

### `GET /api/v1/health`

Liveness probe — returns `200 OK` when the model is loaded.

---

## Risk levels

| Score    | Risk level |
|----------|------------|
| 75 – 100 | `low`      |
| 55 – 74  | `moderate` |
| 35 – 54  | `high`     |
| 0  – 34  | `critical` |

---

## Running tests

```bash
pytest tests/test_api.py -v
```

All 28 tests cover happy paths, validation failures, edge cases, response
schema, headers, and batch limits.

---

## Replacing the synthetic model

1. Collect labelled data with the same 9 features.
2. Modify `ml/training/train_model.py` — swap `generate_dataset()` for your data loader.
3. Re-run `python ml/training/train_model.py` — the API picks up the new artifact automatically on next restart.
4. No changes needed to the API layer.

---

## Technology

| Layer       | Technology                        |
|-------------|-----------------------------------|
| API         | FastAPI 0.115 + Uvicorn           |
| Validation  | Pydantic v2                       |
| ML pipeline | scikit-learn `Pipeline`           |
| Serialisation | joblib                          |
| Model       | `GradientBoostingRegressor`       |
| Tests       | pytest + `TestClient`             |
