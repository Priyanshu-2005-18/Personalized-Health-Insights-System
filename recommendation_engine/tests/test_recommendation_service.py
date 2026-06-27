"""
tests/test_recommendation_service.py
=====================================
Integration tests for the full recommendation pipeline.
Tests end-to-end: HealthMetrics → generate_recommendations → RecommendationResponse
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import unittest
from app.models.health import (
    Category, HealthMetrics, HealthScoreLabel, Priority
)
from app.services.recommendation_service import generate_recommendations


def m(**kwargs) -> HealthMetrics:
    return HealthMetrics(**kwargs)


class TestFullPipelineCriticalUser(unittest.TestCase):
    """User with all metrics in critical/poor range."""

    def setUp(self):
        self.metrics = m(
            sleep_hours=4.0, steps=800, calories=900,
            water_intake_ml=400, stress_level=10, heart_rate_bpm=112
        )
        self.result = generate_recommendations(self.metrics)

    def test_score_is_critical(self):
        self.assertLess(self.result.health_score, 30.0)

    def test_label_is_critical(self):
        self.assertEqual(self.result.health_score_label, HealthScoreLabel.CRITICAL)

    def test_has_critical_recommendations(self):
        self.assertGreater(self.result.critical_count, 0)

    def test_critical_recs_come_first(self):
        priorities = [r.priority for r in self.result.recommendations]
        critical_idx = [i for i, p in enumerate(priorities) if p == Priority.CRITICAL]
        high_idx     = [i for i, p in enumerate(priorities) if p == Priority.HIGH]
        if critical_idx and high_idx:
            self.assertLess(max(critical_idx), min(high_idx))

    def test_total_count_within_max(self):
        self.assertLessEqual(self.result.total_count, 8)

    def test_score_improvement_potential_is_high(self):
        self.assertGreater(self.result.score_improvement_potential, 30.0)

    def test_each_rec_has_actions(self):
        for rec in self.result.recommendations:
            self.assertGreater(len(rec.actions), 0)

    def test_metric_statuses_present(self):
        self.assertEqual(len(self.result.metric_statuses), 6)

    def test_overall_summary_mentions_critical(self):
        self.assertIn("critical", self.result.overall_summary.lower())


class TestFullPipelineOptimalUser(unittest.TestCase):
    """User with all metrics in optimal range."""

    def setUp(self):
        self.metrics = m(
            sleep_hours=8.0, steps=11_000, calories=2_000,
            water_intake_ml=2_800, stress_level=2, heart_rate_bpm=62
        )
        self.result = generate_recommendations(self.metrics)

    def test_score_is_excellent(self):
        self.assertGreater(self.result.health_score, 90.0)

    def test_label_is_excellent(self):
        self.assertEqual(self.result.health_score_label, HealthScoreLabel.EXCELLENT)

    def test_no_critical_recs(self):
        self.assertEqual(self.result.critical_count, 0)

    def test_recommendations_are_low_priority(self):
        for rec in self.result.recommendations:
            self.assertIn(rec.priority, [Priority.LOW, Priority.MEDIUM])

    def test_positive_recommendations_exist(self):
        tags = [tag for r in self.result.recommendations for tag in r.tags]
        self.assertTrue(any(t in tags for t in ["positive", "maintain", "excellent"]))


class TestPartialInput(unittest.TestCase):
    """Engine handles partial metric input gracefully."""

    def test_sleep_only(self):
        result = generate_recommendations(m(sleep_hours=5.0))
        self.assertEqual(result.total_count, 1)
        self.assertEqual(result.recommendations[0].category, Category.SLEEP)

    def test_steps_only(self):
        result = generate_recommendations(m(steps=3000))
        self.assertEqual(result.total_count, 1)
        self.assertEqual(result.recommendations[0].category, Category.ACTIVITY)

    def test_stress_only(self):
        result = generate_recommendations(m(stress_level=9))
        self.assertEqual(result.total_count, 1)
        self.assertEqual(result.recommendations[0].category, Category.STRESS)

    def test_two_metrics(self):
        result = generate_recommendations(m(sleep_hours=4.0, stress_level=9))
        self.assertEqual(result.total_count, 2)

    def test_health_score_only_triggers_general_response(self):
        result = generate_recommendations(m(health_score=30.0))
        self.assertIsNotNone(result)
        self.assertAlmostEqual(result.health_score, 30.0)


class TestHealthScoreHandling(unittest.TestCase):
    """Health score: supplied vs computed."""

    def test_supplied_score_used_directly(self):
        result = generate_recommendations(m(steps=10_000, health_score=42.0))
        self.assertAlmostEqual(result.health_score, 42.0)

    def test_computed_when_not_supplied(self):
        result = generate_recommendations(m(steps=10_000))
        # Should compute from steps sub-score
        self.assertGreater(result.health_score, 50.0)

    def test_score_in_valid_range(self):
        for score in [0.0, 50.0, 100.0]:
            result = generate_recommendations(m(health_score=score, steps=5000))
            self.assertGreaterEqual(result.health_score, 0.0)
            self.assertLessEqual(result.health_score, 100.0)


class TestValidation(unittest.TestCase):
    """Input validation catches out-of-range values."""

    def test_sleep_too_high_raises(self):
        with self.assertRaises(ValueError):
            generate_recommendations(m(sleep_hours=30.0))

    def test_sleep_negative_raises(self):
        with self.assertRaises(ValueError):
            generate_recommendations(m(sleep_hours=-1.0))

    def test_stress_above_10_raises(self):
        with self.assertRaises(ValueError):
            generate_recommendations(m(stress_level=11))

    def test_stress_zero_raises(self):
        with self.assertRaises(ValueError):
            generate_recommendations(m(stress_level=0))

    def test_hr_below_30_raises(self):
        with self.assertRaises(ValueError):
            generate_recommendations(m(heart_rate_bpm=20))

    def test_hr_above_250_raises(self):
        with self.assertRaises(ValueError):
            generate_recommendations(m(heart_rate_bpm=300))

    def test_calories_negative_raises(self):
        with self.assertRaises(ValueError):
            generate_recommendations(m(calories=-100))


class TestDeduplicationAndCapping(unittest.TestCase):
    """No duplicate recommendation IDs; caps enforced."""

    def test_no_duplicate_ids(self):
        result = generate_recommendations(m(
            sleep_hours=4.0, steps=800, calories=900,
            water_intake_ml=400, stress_level=10, heart_rate_bpm=112
        ))
        ids = [r.id for r in result.recommendations]
        self.assertEqual(len(ids), len(set(ids)))

    def test_max_8_recommendations(self):
        result = generate_recommendations(m(
            sleep_hours=4.0, steps=800, calories=900,
            water_intake_ml=400, stress_level=10, heart_rate_bpm=112
        ))
        self.assertLessEqual(result.total_count, 8)

    def test_generated_at_present(self):
        result = generate_recommendations(m(steps=5000))
        self.assertIsNotNone(result.generated_at)
        self.assertIn("T", result.generated_at)  # ISO 8601 format


class TestCompoundRules(unittest.TestCase):
    """Rules that consider multiple metrics together."""

    def test_high_stress_plus_poor_sleep_compound_note(self):
        """High stress + poor sleep triggers a compound warning in the summary."""
        result = generate_recommendations(m(stress_level=8, sleep_hours=5.0))
        stress_rec = next(
            (r for r in result.recommendations if r.category == Category.STRESS), None
        )
        self.assertIsNotNone(stress_rec)
        self.assertIn("combined", stress_rec.summary.lower())

    def test_active_user_high_calories_gets_athlete_advice(self):
        """Very active user with high calories gets different nutrition advice (id contains 'high_active')."""
        result = generate_recommendations(m(steps=13_000, calories=3_000))
        nutrition_rec = next(
            (r for r in result.recommendations if r.category == Category.NUTRITION), None
        )
        if nutrition_rec:
            self.assertIn("high_active", nutrition_rec.id.lower())

    def test_elevated_hr_with_high_stress_mentions_stress(self):
        """Elevated HR + high stress gets stress mention in HR recommendation."""
        result = generate_recommendations(m(heart_rate_bpm=110, stress_level=9))
        hr_rec = next(
            (r for r in result.recommendations if r.category == Category.HEART_RATE), None
        )
        self.assertIsNotNone(hr_rec)
        self.assertIn("stress", hr_rec.summary.lower())

    def test_active_user_water_gets_extra_hydration_note(self):
        """Active user below water target gets activity-adjusted hydration advice."""
        result = generate_recommendations(m(water_intake_ml=1800, steps=12_000))
        hydration_rec = next(
            (r for r in result.recommendations if r.category == Category.HYDRATION), None
        )
        self.assertIsNotNone(hydration_rec)
        self.assertIn("activity", hydration_rec.summary.lower())


class TestMetricStatuses(unittest.TestCase):
    """MetricStatus cards are correctly computed."""

    def test_six_metric_statuses_always(self):
        result = generate_recommendations(m(
            sleep_hours=7.0, steps=8000, calories=2000,
            water_intake_ml=2500, stress_level=3, heart_rate_bpm=65
        ))
        self.assertEqual(len(result.metric_statuses), 6)

    def test_metric_names_correct(self):
        result = generate_recommendations(m(sleep_hours=8.0))
        names = [ms.name for ms in result.metric_statuses]
        self.assertIn("Sleep", names)
        self.assertIn("Steps", names)
        self.assertIn("Stress Level", names)

    def test_optimal_sleep_status_is_optimal(self):
        result = generate_recommendations(m(
            sleep_hours=8.0, steps=5000, stress_level=5
        ))
        sleep_status = next(
            (ms for ms in result.metric_statuses if ms.name == "Sleep"), None
        )
        self.assertIsNotNone(sleep_status)
        self.assertEqual(sleep_status.status, "optimal")

    def test_poor_sleep_status_reflects_score(self):
        result = generate_recommendations(m(sleep_hours=4.0))
        sleep_status = next(
            (ms for ms in result.metric_statuses if ms.name == "Sleep"), None
        )
        self.assertIsNotNone(sleep_status)
        self.assertIn(sleep_status.status, ["poor", "critical"])

    def test_null_metric_status_score_is_zero(self):
        result = generate_recommendations(m(sleep_hours=7.0))
        steps_status = next(
            (ms for ms in result.metric_statuses if ms.name == "Steps"), None
        )
        self.assertIsNotNone(steps_status)
        self.assertIsNone(steps_status.value)


if __name__ == "__main__":
    unittest.main(verbosity=2)
