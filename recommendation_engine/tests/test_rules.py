"""
tests/test_rules.py
===================
Unit tests for every rule function across all 6 categories.
Verifies: rule fires when it should, does NOT fire when it shouldn't,
and returns correctly typed Recommendation objects.
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import unittest
from app.models.health import Category, HealthMetrics, Priority, Recommendation
from app.rules.sleep_rules import (
    rule_critical_sleep_deprivation, rule_poor_sleep,
    rule_suboptimal_sleep, rule_oversleeping, rule_optimal_sleep,
)
from app.rules.activity_rules import (
    rule_sedentary, rule_low_active, rule_somewhat_active,
    rule_active, rule_highly_active,
)
from app.rules.hydration_rules import (
    rule_severe_dehydration, rule_dehydrated,
    rule_below_target, rule_well_hydrated,
)
from app.rules.stress_rules import (
    rule_extreme_stress, rule_high_stress, rule_moderate_stress,
    rule_mild_stress, rule_low_stress,
)
from app.rules.nutrition_rules import (
    rule_critically_low_calories, rule_low_calories,
    rule_optimal_calories, rule_high_calories, rule_very_high_calories,
)
from app.rules.heart_rate_rules import (
    rule_elevated_hr, rule_above_normal_hr, rule_normal_hr,
    rule_good_hr, rule_athlete_hr,
)


def m(**kwargs) -> HealthMetrics:
    return HealthMetrics(**kwargs)


def assert_fires(rule_fn, metrics: HealthMetrics) -> Recommendation:
    """Assert rule fires and returns a valid Recommendation."""
    result = rule_fn(metrics)
    assert result is not None, f"{rule_fn.__name__} should fire but returned None"
    assert isinstance(result, Recommendation)
    assert result.id
    assert result.title
    assert result.summary
    assert len(result.actions) >= 1
    return result


def assert_no_fire(rule_fn, metrics: HealthMetrics):
    """Assert rule does NOT fire."""
    result = rule_fn(metrics)
    assert result is None, f"{rule_fn.__name__} should NOT fire but returned {result}"


class TestSleepRules(unittest.TestCase):

    def test_critical_fires_below_5h(self):
        r = assert_fires(rule_critical_sleep_deprivation, m(sleep_hours=4.0))
        self.assertEqual(r.priority, Priority.CRITICAL)
        self.assertEqual(r.category, Category.SLEEP)

    def test_critical_no_fire_above_5h(self):
        assert_no_fire(rule_critical_sleep_deprivation, m(sleep_hours=5.5))

    def test_poor_fires_5_to_6h(self):
        r = assert_fires(rule_poor_sleep, m(sleep_hours=5.5))
        self.assertEqual(r.priority, Priority.HIGH)

    def test_poor_no_fire_below_5h(self):
        assert_no_fire(rule_poor_sleep, m(sleep_hours=4.9))

    def test_poor_no_fire_above_6h(self):
        assert_no_fire(rule_poor_sleep, m(sleep_hours=6.5))

    def test_suboptimal_fires_6_to_7h(self):
        r = assert_fires(rule_suboptimal_sleep, m(sleep_hours=6.5))
        self.assertEqual(r.priority, Priority.MEDIUM)

    def test_optimal_fires_7_to_9h(self):
        for h in [7.0, 8.0, 9.0]:
            r = assert_fires(rule_optimal_sleep, m(sleep_hours=h))
            self.assertEqual(r.priority, Priority.LOW)

    def test_oversleeping_fires_above_9h(self):
        r = assert_fires(rule_oversleeping, m(sleep_hours=10.5))
        self.assertEqual(r.priority, Priority.LOW)

    def test_no_fire_when_none(self):
        assert_no_fire(rule_critical_sleep_deprivation, m(steps=5000))

    def test_score_impact_decreasing_severity(self):
        r_critical = rule_critical_sleep_deprivation(m(sleep_hours=4.0))
        r_poor     = rule_poor_sleep(m(sleep_hours=5.5))
        self.assertGreater(r_critical.score_impact, r_poor.score_impact)


class TestActivityRules(unittest.TestCase):

    def test_sedentary_fires_below_2500(self):
        r = assert_fires(rule_sedentary, m(steps=1000))
        self.assertEqual(r.priority, Priority.CRITICAL)

    def test_sedentary_no_fire_above_2500(self):
        assert_no_fire(rule_sedentary, m(steps=3000))

    def test_low_fires_2500_to_5000(self):
        r = assert_fires(rule_low_active, m(steps=4000))
        self.assertEqual(r.priority, Priority.HIGH)

    def test_moderate_fires_5000_to_7500(self):
        r = assert_fires(rule_somewhat_active, m(steps=6000))
        self.assertEqual(r.priority, Priority.MEDIUM)

    def test_active_fires_7500_to_10000(self):
        r = assert_fires(rule_active, m(steps=9000))
        self.assertEqual(r.priority, Priority.LOW)

    def test_highly_active_fires_above_10000(self):
        r = assert_fires(rule_highly_active, m(steps=12000))
        self.assertEqual(r.priority, Priority.LOW)

    def test_no_fire_when_none(self):
        assert_no_fire(rule_sedentary, m(sleep_hours=7.0))


class TestHydrationRules(unittest.TestCase):

    def test_severe_fires_below_1000(self):
        r = assert_fires(rule_severe_dehydration, m(water_intake_ml=500))
        self.assertEqual(r.priority, Priority.CRITICAL)

    def test_dehydrated_fires_1000_to_1500(self):
        r = assert_fires(rule_dehydrated, m(water_intake_ml=1200))
        self.assertEqual(r.priority, Priority.HIGH)

    def test_below_target_fires_1500_to_2000(self):
        r = assert_fires(rule_below_target, m(water_intake_ml=1800))
        self.assertEqual(r.priority, Priority.MEDIUM)

    def test_below_target_with_active_user(self):
        # Active user gets extra note about sweating
        r = assert_fires(rule_below_target, m(water_intake_ml=1800, steps=12000))
        self.assertIn("activity", r.summary.lower())

    def test_well_hydrated_fires_above_2000(self):
        r = assert_fires(rule_well_hydrated, m(water_intake_ml=2500))
        self.assertEqual(r.priority, Priority.LOW)

    def test_no_fire_when_none(self):
        assert_no_fire(rule_severe_dehydration, m(sleep_hours=7.0))


class TestStressRules(unittest.TestCase):

    def test_extreme_fires_at_10(self):
        r = assert_fires(rule_extreme_stress, m(stress_level=10))
        self.assertEqual(r.priority, Priority.CRITICAL)

    def test_high_fires_8_to_9(self):
        for lvl in [8, 9]:
            r = assert_fires(rule_high_stress, m(stress_level=lvl))
            self.assertEqual(r.priority, Priority.HIGH)

    def test_high_with_poor_sleep_compound(self):
        # Compound note should appear
        r = assert_fires(rule_high_stress, m(stress_level=8, sleep_hours=5.0))
        self.assertIn("combined", r.summary.lower())

    def test_moderate_fires_6_to_7(self):
        for lvl in [6, 7]:
            r = assert_fires(rule_moderate_stress, m(stress_level=lvl))
            self.assertEqual(r.priority, Priority.MEDIUM)

    def test_mild_fires_4_to_5(self):
        for lvl in [4, 5]:
            r = assert_fires(rule_mild_stress, m(stress_level=lvl))
            self.assertEqual(r.priority, Priority.LOW)

    def test_low_fires_1_to_3(self):
        for lvl in [1, 2, 3]:
            r = assert_fires(rule_low_stress, m(stress_level=lvl))
            self.assertEqual(r.priority, Priority.LOW)

    def test_no_fire_when_none(self):
        assert_no_fire(rule_extreme_stress, m(sleep_hours=7.0))


class TestNutritionRules(unittest.TestCase):

    def test_critically_low_fires_below_1200(self):
        r = assert_fires(rule_critically_low_calories, m(calories=900))
        self.assertEqual(r.priority, Priority.CRITICAL)

    def test_low_fires_1200_to_1500(self):
        r = assert_fires(rule_low_calories, m(calories=1350))
        self.assertEqual(r.priority, Priority.HIGH)

    def test_optimal_fires_1600_to_2400(self):
        for cal in [1600, 2000, 2400]:
            r = assert_fires(rule_optimal_calories, m(calories=cal))
            self.assertEqual(r.priority, Priority.LOW)

    def test_optimal_active_user_gets_protein_tip(self):
        r = assert_fires(rule_optimal_calories, m(calories=2000, steps=12000))
        self.assertIn("protein", r.detail.lower())

    def test_high_fires_2400_to_3500(self):
        r = assert_fires(rule_high_calories, m(calories=2800))
        self.assertEqual(r.priority, Priority.MEDIUM)

    def test_high_active_user_different_advice(self):
        # Very active user with high calories → different recommendation ID contains "high_active"
        r = assert_fires(rule_high_calories, m(calories=3000, steps=13000))
        self.assertIn("high_active", r.id.lower())

    def test_very_high_fires_above_3500(self):
        r = assert_fires(rule_very_high_calories, m(calories=4000))
        self.assertEqual(r.priority, Priority.HIGH)

    def test_no_fire_when_none(self):
        assert_no_fire(rule_critically_low_calories, m(sleep_hours=7.0))


class TestHeartRateRules(unittest.TestCase):

    def test_elevated_fires_above_100(self):
        r = assert_fires(rule_elevated_hr, m(heart_rate_bpm=105))
        self.assertEqual(r.priority, Priority.HIGH)

    def test_elevated_with_high_stress(self):
        r = assert_fires(rule_elevated_hr, m(heart_rate_bpm=110, stress_level=8))
        self.assertIn("stress", r.summary.lower())

    def test_above_normal_fires_86_to_100(self):
        r = assert_fires(rule_above_normal_hr, m(heart_rate_bpm=92))
        self.assertEqual(r.priority, Priority.MEDIUM)

    def test_normal_fires_76_to_85(self):
        r = assert_fires(rule_normal_hr, m(heart_rate_bpm=80))
        self.assertEqual(r.priority, Priority.LOW)

    def test_good_fires_56_to_75(self):
        for bpm in [60, 70, 75]:
            r = assert_fires(rule_good_hr, m(heart_rate_bpm=bpm))
            self.assertEqual(r.priority, Priority.LOW)

    def test_athlete_fires_below_55(self):
        r = assert_fires(rule_athlete_hr, m(heart_rate_bpm=48))
        self.assertEqual(r.priority, Priority.LOW)

    def test_no_fire_when_none(self):
        assert_no_fire(rule_elevated_hr, m(sleep_hours=7.0))


class TestRecommendationStructure(unittest.TestCase):
    """Verify all rules produce well-formed Recommendation objects."""

    ALL_RULES = [
        rule_critical_sleep_deprivation, rule_poor_sleep,
        rule_suboptimal_sleep, rule_oversleeping,
        rule_sedentary, rule_low_active, rule_somewhat_active,
        rule_severe_dehydration, rule_dehydrated,
        rule_extreme_stress, rule_high_stress, rule_moderate_stress,
        rule_critically_low_calories, rule_low_calories, rule_very_high_calories,
        rule_elevated_hr, rule_above_normal_hr,
    ]

    TRIGGER_METRICS = [
        m(sleep_hours=4.0), m(sleep_hours=5.5),
        m(sleep_hours=6.5), m(sleep_hours=10.5),
        m(steps=1000), m(steps=4000), m(steps=6000),
        m(water_intake_ml=500), m(water_intake_ml=1200),
        m(stress_level=10), m(stress_level=8), m(stress_level=6),
        m(calories=900), m(calories=1350), m(calories=4000),
        m(heart_rate_bpm=110), m(heart_rate_bpm=92),
    ]

    def test_all_recommendations_have_required_fields(self):
        for rule_fn, metrics in zip(self.ALL_RULES, self.TRIGGER_METRICS):
            with self.subTest(rule=rule_fn.__name__):
                result = rule_fn(metrics)
                if result is None:
                    continue
                self.assertIsInstance(result.id,       str)
                self.assertIsInstance(result.title,    str)
                self.assertIsInstance(result.summary,  str)
                self.assertIsInstance(result.detail,   str)
                self.assertIsInstance(result.actions,  list)
                self.assertGreater(len(result.actions), 0)
                self.assertIsInstance(result.score_impact, float)
                self.assertGreaterEqual(result.score_impact, 0.0)
                self.assertIsInstance(result.category, Category)
                self.assertIsInstance(result.priority, Priority)


if __name__ == "__main__":
    unittest.main(verbosity=2)
