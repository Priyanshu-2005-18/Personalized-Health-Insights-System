"""
tests/test_scorer.py
====================
Unit tests for all sub-score and composite-score functions.
No external dependencies required — pure Python.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import unittest
from app.models.health import HealthMetrics, HealthScoreLabel
from app.services.scorer import (
    compute_composite_score,
    compute_sub_scores,
    get_health_score_label,
    score_calories,
    score_heart_rate,
    score_sleep,
    score_steps,
    score_stress,
    score_water,
)


class TestSleepScore(unittest.TestCase):

    def test_optimal_low_boundary(self):
        self.assertEqual(score_sleep(7.0), 100.0)

    def test_optimal_high_boundary(self):
        self.assertEqual(score_sleep(9.0), 100.0)

    def test_optimal_midpoint(self):
        self.assertEqual(score_sleep(8.0), 100.0)

    def test_minimum_zero(self):
        self.assertEqual(score_sleep(0.0), 0.0)

    def test_below_minimum(self):
        self.assertEqual(score_sleep(3.0), 0.0)

    def test_ramp_midpoint(self):
        # 5h is halfway between 3h (0) and 7h (100) → 50
        self.assertAlmostEqual(score_sleep(5.0), 50.0, places=1)

    def test_oversleeping_penalty(self):
        score_10h = score_sleep(10.0)
        score_12h = score_sleep(12.0)
        self.assertLess(score_10h, 100.0)
        self.assertLess(score_12h, score_10h)

    def test_never_below_zero(self):
        self.assertGreaterEqual(score_sleep(24.0), 0.0)

    def test_never_above_100(self):
        self.assertLessEqual(score_sleep(8.5), 100.0)


class TestStepScore(unittest.TestCase):

    def test_target_is_100(self):
        self.assertEqual(score_steps(10_000), 100.0)

    def test_zero_steps(self):
        self.assertEqual(score_steps(0), 0.0)

    def test_half_target(self):
        self.assertAlmostEqual(score_steps(5_000), 50.0, places=1)

    def test_above_target_capped(self):
        self.assertEqual(score_steps(20_000), 100.0)

    def test_proportional(self):
        self.assertLess(score_steps(3_000), score_steps(7_000))


class TestCalorieScore(unittest.TestCase):

    def test_optimal_range_is_100(self):
        self.assertEqual(score_calories(1_600), 100.0)
        self.assertEqual(score_calories(2_000), 100.0)
        self.assertEqual(score_calories(2_400), 100.0)

    def test_critically_low(self):
        self.assertLess(score_calories(800), 50.0)

    def test_very_high(self):
        self.assertLess(score_calories(4_000), 80.0)

    def test_low_penalty_gradual(self):
        self.assertGreater(score_calories(1_500), score_calories(1_000))

    def test_high_penalty_gradual(self):
        self.assertGreater(score_calories(2_500), score_calories(3_000))

    def test_never_negative(self):
        self.assertGreaterEqual(score_calories(100), 0.0)


class TestWaterScore(unittest.TestCase):

    def test_target_is_100(self):
        self.assertEqual(score_water(3_000), 100.0)

    def test_zero_is_zero(self):
        self.assertEqual(score_water(0), 0.0)

    def test_half_target(self):
        self.assertAlmostEqual(score_water(1_500), 50.0, places=1)

    def test_above_target_capped(self):
        self.assertEqual(score_water(5_000), 100.0)


class TestStressScore(unittest.TestCase):

    def test_lowest_stress_max_score(self):
        self.assertEqual(score_stress(1), 100.0)

    def test_highest_stress_zero_score(self):
        self.assertEqual(score_stress(10), 0.0)

    def test_midpoint(self):
        # stress=5.5 → midpoint → ~50
        self.assertAlmostEqual(score_stress(5), 55.56, places=1)

    def test_monotonically_decreasing(self):
        scores = [score_stress(i) for i in range(1, 11)]
        self.assertEqual(scores, sorted(scores, reverse=True))


class TestHeartRateScore(unittest.TestCase):

    def test_optimal_range_is_100(self):
        self.assertEqual(score_heart_rate(62), 100.0)
        self.assertEqual(score_heart_rate(65), 100.0)

    def test_athlete_near_perfect(self):
        self.assertGreaterEqual(score_heart_rate(50), 90.0)

    def test_elevated_low(self):
        self.assertLess(score_heart_rate(110), 50.0)

    def test_never_negative(self):
        self.assertGreaterEqual(score_heart_rate(200), 0.0)


class TestCompositeScore(unittest.TestCase):

    def test_all_optimal(self):
        m = HealthMetrics(
            sleep_hours=8.0, steps=10_000, calories=2_000,
            water_intake_ml=3_000, stress_level=1, heart_rate_bpm=62
        )
        sub = compute_sub_scores(m)
        score = compute_composite_score(sub)
        self.assertGreater(score, 95.0)

    def test_all_poor(self):
        m = HealthMetrics(
            sleep_hours=3.5, steps=500, calories=800,
            water_intake_ml=400, stress_level=10, heart_rate_bpm=115
        )
        sub = compute_sub_scores(m)
        score = compute_composite_score(sub)
        self.assertLess(score, 20.0)

    def test_partial_input_returns_score(self):
        m = HealthMetrics(sleep_hours=7.0)
        sub = compute_sub_scores(m)
        score = compute_composite_score(sub)
        self.assertGreater(score, 0.0)
        self.assertLessEqual(score, 100.0)

    def test_no_input_returns_neutral(self):
        sub = {k: None for k in ["sleep", "activity", "nutrition", "hydration", "stress", "heart_rate"]}
        score = compute_composite_score(sub)
        self.assertEqual(score, 50.0)


class TestHealthScoreLabel(unittest.TestCase):

    def test_excellent(self):
        self.assertEqual(get_health_score_label(90.0), HealthScoreLabel.EXCELLENT)

    def test_good(self):
        self.assertEqual(get_health_score_label(75.0), HealthScoreLabel.GOOD)

    def test_fair(self):
        self.assertEqual(get_health_score_label(62.0), HealthScoreLabel.FAIR)

    def test_poor(self):
        self.assertEqual(get_health_score_label(48.0), HealthScoreLabel.POOR)

    def test_critical(self):
        self.assertEqual(get_health_score_label(20.0), HealthScoreLabel.CRITICAL)

    def test_boundary_excellent(self):
        self.assertEqual(get_health_score_label(85.0), HealthScoreLabel.EXCELLENT)

    def test_boundary_critical(self):
        self.assertEqual(get_health_score_label(39.9), HealthScoreLabel.CRITICAL)


if __name__ == "__main__":
    unittest.main(verbosity=2)
