"""
generate_data.py
================
Generates a realistic synthetic health dataset with 2,000 samples.

Feature distributions are calibrated to real-world ranges:
  sleep_hours      → Normal(7.0, 1.5), clipped [3, 12]
  steps            → Normal(8000, 3000), clipped [500, 20000]
  calories         → Normal(2000, 400), clipped [1000, 4000]
  water_intake_ml  → Normal(2200, 600), clipped [500, 5000]
  stress_level     → Uniform(1, 10) integer
  heart_rate_bpm   → Normal(72, 12), clipped [45, 120]

Health score (0–100) is computed as a weighted function of all features,
with realistic noise added to prevent perfect linearity.
"""

import numpy as np
import pandas as pd

np.random.seed(42)
N = 2000


def generate_health_dataset(n: int = N) -> pd.DataFrame:
    rng = np.random.default_rng(42)

    # ── Raw features ──────────────────────────────────────────────────────────
    sleep_hours     = np.clip(rng.normal(7.0, 1.5, n), 3.0, 12.0)
    steps           = np.clip(rng.normal(8000, 3000, n), 500, 20000)
    calories        = np.clip(rng.normal(2000, 400, n), 1000, 4000)
    water_intake_ml = np.clip(rng.normal(2200, 600, n), 500, 5000)
    stress_level    = rng.integers(1, 11, n).astype(float)
    heart_rate_bpm  = np.clip(rng.normal(72, 12, n), 45, 120)

    # ── Health score construction ─────────────────────────────────────────────
    # Each component contributes 0–100; weights sum to 1.0
    sleep_score    = np.clip((sleep_hours - 3) / (9 - 3) * 100, 0, 100)   # optimal ~7-9h
    step_score     = np.clip(steps / 10000 * 100, 0, 100)                  # 10k steps = 100
    calorie_score  = 100 - np.abs(calories - 2000) / 20                    # penalty away from 2000
    calorie_score  = np.clip(calorie_score, 0, 100)
    water_score    = np.clip(water_intake_ml / 3000 * 100, 0, 100)         # 3L = 100
    stress_score   = (10 - stress_level) / 9 * 100                         # lower stress = higher score
    hr_score       = 100 - np.abs(heart_rate_bpm - 65) * 1.5              # optimal ~65 bpm
    hr_score       = np.clip(hr_score, 0, 100)

    # Weighted composite
    health_score = (
        0.22 * sleep_score  +
        0.20 * step_score   +
        0.15 * calorie_score +
        0.15 * water_score  +
        0.18 * stress_score +
        0.10 * hr_score
    )

    # Add realistic noise (± ~3 points)
    noise = rng.normal(0, 3, n)
    health_score = np.clip(health_score + noise, 0, 100).round(2)

    df = pd.DataFrame({
        "sleep_hours":     sleep_hours.round(2),
        "steps":           steps.round(0).astype(int),
        "calories":        calories.round(0).astype(int),
        "water_intake_ml": water_intake_ml.round(0).astype(int),
        "stress_level":    stress_level.astype(int),
        "heart_rate_bpm":  heart_rate_bpm.round(1),
        "health_score":    health_score,
    })
    return df


if __name__ == "__main__":
    df = generate_health_dataset()
    df.to_csv("data/health_data.csv", index=False)
    print(f"✅ Dataset generated: {df.shape[0]} rows × {df.shape[1]} columns")
    print(df.describe().round(2))
