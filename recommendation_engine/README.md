# Health Recommendation Engine

A **rule-based, evidence-backed recommendation system** built with FastAPI.
Takes user health metrics as input and returns personalised, prioritised
recommendations with actionable steps.

---

## Architecture

```
recommendation_engine/
├── app/
│   ├── rules/               # Rule definitions — one file per health domain
│   │   ├── thresholds.py    # Single source of truth for all health thresholds
│   │   ├── sleep_rules.py   # 5 sleep rules (critical → optimal)
│   │   ├── activity_rules.py# 5 activity rules (sedentary → highly active)
│   │   ├── hydration_rules.py# 4 hydration rules
│   │   ├── stress_rules.py  # 5 stress rules
│   │   ├── nutrition_rules.py# 5 calorie rules
│   │   └── heart_rate_rules.py# 5 heart rate rules
│   ├── services/
│   │   ├── scorer.py        # Sub-score computation + composite health score
│   │   └── recommendation_service.py  # Full engine pipeline
│   ├── models/health.py     # Domain dataclasses (no dependencies)
│   ├── schemas/health.py    # Pydantic v2 request/response schemas
│   ├── routers/recommendations.py  # FastAPI routes
│   └── main.py              # App factory + middleware
├── tests/
│   ├── test_scorer.py       # 42 unit tests for scoring functions
│   ├── test_rules.py        # 52 unit tests for all rule functions
│   └── test_recommendation_service.py  # 36 integration tests
├── api_examples.http        # 30+ ready-to-run API examples
├── Dockerfile
└── docker-compose.yml
```

---

## How It Works

### Pipeline

```
HealthMetrics input
       │
       ▼
  1. Validate & normalise (domain bounds check)
       │
       ▼
  2. Compute sub-scores (0–100 per metric)
       │
       ▼
  3. Resolve health score (use supplied ML score OR compute composite)
       │
       ▼
  4. Run rule registries (29 rules across 6 categories)
       │  Each rule: fires → returns Recommendation | None
       │  Only the FIRST firing rule per category (most severe)
       ▼
  5. Rank by priority → score_impact → category weight
       │
       ▼
  6. Deduplicate + cap (max 8 total, max 3 per category)
       │
       ▼
  7. Build RecommendationResponse with metric statuses + summary
```

### Scoring

| Metric | Optimal Range | Score 100 at |
|---|---|---|
| `sleep_hours` | 7–9 h | 7.0–9.0 h |
| `steps` | ≥ 10,000 | 10,000 steps |
| `calories` | 1,600–2,400 kcal | 1,600–2,400 kcal |
| `water_intake_ml` | 2,000–3,000 ml | 3,000 ml |
| `stress_level` | 1–3 | 1 (no stress) |
| `heart_rate_bpm` | 55–75 bpm | 60–65 bpm |

**Composite score** = weighted average of available sub-scores  
(weights: sleep 1.20 · stress 1.15 · activity 1.10 · HR 1.05 · nutrition 1.00 · hydration 0.95)

**Score bands:** Critical (<40) · Poor (40–55) · Fair (55–70) · Good (70–85) · Excellent (≥85)

### Priority Levels

| Priority | Meaning | Example |
|---|---|---|
| 🆘 Critical | Immediate action needed | Sleep < 5h, Stress = 10 |
| 🔴 High | Address today | Sleep 5–6h, Steps < 2,500 |
| 🟡 Medium | Address this week | Slightly below targets |
| 🟢 Low | Maintenance / positive | Optimal range, keep it up |

### Compound Rules

Some rules check multiple metrics together:
- **High stress + poor sleep** → stress recommendation mentions combined risk
- **Very active + high calories** → nutrition advice adjusts for athlete needs
- **Elevated HR + high stress** → HR recommendation mentions cortisol link
- **Active user + low water** → hydration target adjusted for sweat losses

---

## Quick Start

### Docker

```bash
cp .env.example .env
docker compose up --build
# API: http://localhost:8000
# Docs: http://localhost:8000/docs
```

### Local

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

---

## API Reference

All endpoints at `/api/v1/`.

### `POST /recommendations`
Full personalised recommendation report.

```json
// Request
{
  "sleep_hours": 5.5,
  "steps": 3200,
  "calories": 2800,
  "water_intake_ml": 1200,
  "stress_level": 8,
  "heart_rate_bpm": 92,
  "health_score": 42.0
}
```

```json
// Response
{
  "health_score": 42.0,
  "health_score_label": "Poor",
  "overall_summary": "Your overall health score is 42/100 — Poor...",
  "metric_statuses": [
    { "name": "Sleep", "value": 5.5, "unit": "hours",
      "status": "poor", "status_label": "Poor 🔴",
      "target": "7–9 hours", "score": 31.25 }
  ],
  "recommendations": [
    {
      "id": "sleep_poor",
      "category": "sleep",
      "priority": "high",
      "title": "Insufficient Sleep — Build a Better Bedtime Routine",
      "summary": "You slept 5.5 hours, below the recommended 7–9 hours...",
      "detail": "Adults sleeping 6 hours instead of 8 hours show 4× more...",
      "actions": [
        { "order": 1, "description": "Set a fixed bedtime and wake time...",
          "frequency": "Daily" }
      ],
      "metric_value": 5.5,
      "target_value": "7–9 hours",
      "icon": "😴",
      "score_impact": 12.0,
      "tags": ["sleep", "routine", "immune", "stress"]
    }
  ],
  "total_count": 6,
  "critical_count": 0,
  "high_count": 4,
  "score_improvement_potential": 45.2,
  "generated_at": "2024-06-15T10:30:00+00:00"
}
```

### `POST /recommendations/quick`
Same as above but returns top 3 recommendations only.
Designed for mobile push notifications and dashboard widgets.

### `GET /recommendations/categories`
Returns metadata for all 6 supported categories.

### `GET /recommendations/health`
Engine status: rule counts, version, category count.

---

## Integration with ML Pipeline

The `health_score` field bridges the ML model and this engine:

```python
# In your FastAPI health tracking service:
from health_ml.src.predictor import HealthScorePredictor
import httpx

predictor = HealthScorePredictor()

async def get_insights(user_metrics: dict):
    # Step 1: ML model predicts health score
    ml_result = predictor.predict_single(user_metrics)

    # Step 2: Recommendation engine generates personalised advice
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/api/v1/recommendations",
            json={**user_metrics, "health_score": ml_result["predicted_score"]}
        )
    return response.json()
```

---

## Running Tests

```bash
# All 130 tests (pure Python, no server needed)
python -m unittest discover -s tests -v

# Or with pytest (if installed)
pytest

# Single file
python -m unittest tests.test_scorer -v
python -m unittest tests.test_rules -v
python -m unittest tests.test_recommendation_service -v
```

**Test coverage:** 130 tests across 3 files
- `test_scorer.py`  — 42 tests: every scoring function, boundary values, composite score
- `test_rules.py`   — 52 tests: every rule fires/no-fires, compound rules, structure
- `test_recommendation_service.py` — 36 tests: full pipeline, validation, dedup, capping

---

## Adding a New Rule

1. Open the relevant `app/rules/<category>_rules.py`
2. Define a new function following the pattern:

```python
def rule_my_new_rule(m: HealthMetrics) -> Optional[Recommendation]:
    if m.some_metric is None or not my_condition(m.some_metric):
        return None
    return Recommendation(
        id="category_my_rule",
        category=Category.SLEEP,
        priority=Priority.MEDIUM,
        title="My Rule Title",
        summary="One sentence why this matters.",
        detail="Deeper context and evidence.",
        actions=[
            ActionStep(1, "Concrete action step.", frequency="Daily"),
        ],
        metric_value=float(m.some_metric),
        target_value="optimal range",
        icon="💡",
        score_impact=5.0,
        tags=["sleep", "my-tag"],
    )
```

3. Add it to the `<CATEGORY>_RULES` list (in severity order, most severe first)
4. Write a test in `tests/test_rules.py`

---

## Adding a New Category

1. Create `app/rules/new_category_rules.py`
2. Define rules and a `NEW_CATEGORY_RULES` list
3. Register in `app/rules/__init__.py`:
   ```python
   from app.rules.new_category_rules import NEW_CATEGORY_RULES
   ALL_RULE_SETS["new_category"] = NEW_CATEGORY_RULES
   ```
4. Add threshold constants to `app/rules/thresholds.py`
5. Add scoring function to `app/services/scorer.py`
6. Add `MetricStatus` entry in `build_metric_statuses()`
