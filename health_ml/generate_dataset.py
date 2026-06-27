"""
generate_dataset.py
===================
Creates a realistic synthetic health dataset with 2 000 samples.

Health score formula (ground truth):
  Each metric contributes a weighted sub-score (0–100):
    sleep_hours      → 25 % weight  (optimal 7–9 h)
    steps            → 20 % weight  (optimal ≥ 10 000)
    calories         → 15 % weight  (optimal 1 800–2 200 kcal)
    water_intake_ml  → 15 % weight  (optimal ≥ 2 500 ml)
    stress_level     → 15 % weight  (lower = better, inverse)
    heart_rate_bpm   → 10 % weight  (optimal 60–80 bpm)

  health_score = weighted_sum + Gaussian noise (σ = 5)
  health_score is clipped to [0, 100].
"""

import numpy as np
import pandas as pd

RNG = np.random.default_rng(seed=42)
N   = 2_000


def _sleep_score(h: np.ndarray) -> np.ndarray:
    """Peaked around 7–9 hours."""
    s = np.where(h < 7,  (h / 7) * 100,
        np.where(h <= 9,  100.0,
                          100 - (h - 9) * 25))
    return np.clip(s, 0, 100)


def _steps_score(s: np.ndarray) -> np.ndarray:
    return np.clip(s / 100, 0, 100)


def _calories_score(c: np.ndarray) -> np.ndarray:
    """Optimal band 1 800–2 200 kcal."""
    s = np.where(c < 1_800, (c / 1_800) * 85,
        np.where(c <= 2_200, 100.0,
                              100 - ((c - 2_200) / 800) * 40))
    return np.clip(s, 0, 100)


def _water_score(w: np.ndarray) -> np.ndarray:
    return np.clip(w / 25, 0, 100)   # 2 500 ml → 100


def _stress_score(stress: np.ndarray) -> np.ndarray:
    """Inverse: lower stress → higher score."""
    return ((10 - stress) / 9) * 100


def _hr_score(hr: np.ndarray) -> np.ndarray:
    """Peaked at 60–80 bpm."""
    s = np.where(hr < 60,  (hr / 60) * 85,
        np.where(hr <= 80,  100.0,
                             100 - ((hr - 80) / 70) * 60))
    return np.clip(s, 0, 100)


# ── Generate raw features ─────────────────────────────────────────────────────

sleep_hours     = RNG.normal(loc=7.0, scale=1.5, size=N).clip(3.0, 12.0)
steps           = RNG.normal(loc=7_500, scale=3_000, size=N).clip(0, 20_000)
calories        = RNG.normal(loc=2_000, scale=400, size=N).clip(800, 4_000)
water_intake_ml = RNG.normal(loc=2_200, scale=600, size=N).clip(500, 4_000)
stress_level    = RNG.integers(1, 11, size=N).astype(float)
heart_rate_bpm  = RNG.normal(loc=72, scale=12, size=N).clip(40, 150)

# Introduce realistic missing values (~3 % each)
for arr in [sleep_hours, steps, calories, water_intake_ml, stress_level, heart_rate_bpm]:
    mask = RNG.random(N) < 0.03
    arr[mask] = np.nan

# ── Compute health score ──────────────────────────────────────────────────────

weights = dict(sleep=0.25, steps=0.20, calories=0.15, water=0.15, stress=0.15, hr=0.10)

health_score = (
    weights["sleep"]    * _sleep_score(np.nan_to_num(sleep_hours, nan=7.0)) +
    weights["steps"]    * _steps_score(np.nan_to_num(steps, nan=7500)) +
    weights["calories"] * _calories_score(np.nan_to_num(calories, nan=2000)) +
    weights["water"]    * _water_score(np.nan_to_num(water_intake_ml, nan=2200)) +
    weights["stress"]   * _stress_score(np.nan_to_num(stress_level, nan=5)) +
    weights["hr"]       * _hr_score(np.nan_to_num(heart_rate_bpm, nan=72))
)

noise        = RNG.normal(0, 5, size=N)
health_score = np.clip(health_score + noise, 0, 100).round(2)

# ── Assemble DataFrame ────────────────────────────────────────────────────────

df = pd.DataFrame({
    "sleep_hours":     sleep_hours.round(2),
    "steps":           steps.astype(float),          # keep float so NaN works
    "calories":        calories.astype(float),
    "water_intake_ml": water_intake_ml.astype(float),
    "stress_level":    stress_level.astype(float),
    "heart_rate_bpm":  heart_rate_bpm.astype(float),
    "health_score":    health_score,
})

df.to_csv("data/health_data.csv", index=False)
print(f"✅  Dataset saved → data/health_data.csv  ({N} rows)")
print(df.describe().round(2).to_string())
print(f"\nMissing values:\n{df.isnull().sum()}")
