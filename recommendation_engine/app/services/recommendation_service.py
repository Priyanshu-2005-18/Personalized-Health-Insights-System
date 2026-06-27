"""
services/recommendation_service.py
====================================
Core recommendation engine.

Pipeline:
  1. Validate & normalise inputs
  2. Compute sub-scores for each metric
  3. Resolve health score (use supplied or compute composite)
  4. Run all rule registries against the metrics
  5. Score and rank recommendations by urgency
  6. Deduplicate and cap per category + total
  7. Compute score improvement potential
  8. Build and return RecommendationResponse
"""

from datetime import datetime, timezone
from typing import Dict, List, Optional

from app.models.health import (
    Category, HealthMetrics, HealthScoreLabel,
    Priority, Recommendation, RecommendationResponse,
)
from app.rules import ALL_RULE_SETS
from app.rules.thresholds import (
    MAX_PER_CATEGORY, MAX_RECOMMENDATIONS, PRIORITY_THRESHOLDS, VALID_RANGES
)
from app.services.scorer import (
    build_metric_statuses,
    build_overall_summary,
    compute_composite_score,
    compute_sub_scores,
    get_health_score_label,
)


# ─────────────────────────────────────────────────────────────────────────────
#  Priority ordering (for sorting)
# ─────────────────────────────────────────────────────────────────────────────

PRIORITY_ORDER = {
    Priority.CRITICAL: 0,
    Priority.HIGH:     1,
    Priority.MEDIUM:   2,
    Priority.LOW:      3,
}


# ─────────────────────────────────────────────────────────────────────────────
#  Input validation
# ─────────────────────────────────────────────────────────────────────────────

def _validate_metrics(m: HealthMetrics) -> List[str]:
    """Return list of validation error strings (empty = valid)."""
    errors = []
    checks = [
        ("sleep_hours",     m.sleep_hours),
        ("steps",           m.steps),
        ("calories",        m.calories),
        ("water_intake_ml", m.water_intake_ml),
        ("stress_level",    m.stress_level),
        ("heart_rate_bpm",  m.heart_rate_bpm),
        ("health_score",    m.health_score),
    ]
    for field, value in checks:
        if value is None:
            continue
        lo, hi = VALID_RANGES[field]
        if not (lo <= value <= hi):
            errors.append(
                f"{field}={value} is outside valid range [{lo}, {hi}]"
            )
    return errors


def _clamp(value: Optional[float], lo: float, hi: float) -> Optional[float]:
    if value is None:
        return None
    return max(lo, min(hi, value))


def _normalise(m: HealthMetrics) -> HealthMetrics:
    """Clamp all values to valid domain bounds (defensive guard)."""
    return HealthMetrics(
        sleep_hours     = _clamp(m.sleep_hours,     0.0, 24.0),
        steps           = int(_clamp(m.steps,       0,   100_000)) if m.steps is not None else None,
        calories        = int(_clamp(m.calories,    0,   10_000))  if m.calories is not None else None,
        water_intake_ml = int(_clamp(m.water_intake_ml, 0, 10_000)) if m.water_intake_ml is not None else None,
        stress_level    = int(_clamp(m.stress_level, 1,  10))      if m.stress_level is not None else None,
        heart_rate_bpm  = int(_clamp(m.heart_rate_bpm, 30, 250))   if m.heart_rate_bpm is not None else None,
        health_score    = _clamp(m.health_score,    0.0, 100.0),
    )


# ─────────────────────────────────────────────────────────────────────────────
#  Rule execution
# ─────────────────────────────────────────────────────────────────────────────

def _run_rules(m: HealthMetrics) -> List[Recommendation]:
    """
    Evaluate every rule registry against the metrics.
    Only the FIRST firing rule per category is kept (rules are ordered
    most-severe → least-severe within each registry).
    """
    fired: List[Recommendation] = []
    for category_name, rules in ALL_RULE_SETS.items():
        for rule_fn in rules:
            result = rule_fn(m)
            if result is not None:
                fired.append(result)
                break   # one recommendation per category (most severe)
    return fired


# ─────────────────────────────────────────────────────────────────────────────
#  Ranking and filtering
# ─────────────────────────────────────────────────────────────────────────────

def _rank_recommendations(recs: List[Recommendation]) -> List[Recommendation]:
    """
    Sort by:
      1. Priority (critical first)
      2. Score impact (higher = more important)
      3. Category weight (from CATEGORY_WEIGHTS)
    """
    from app.rules.thresholds import CATEGORY_WEIGHTS

    def sort_key(r: Recommendation):
        return (
            PRIORITY_ORDER[r.priority],
            -r.score_impact,
            -CATEGORY_WEIGHTS.get(r.category.value, 1.0),
        )

    return sorted(recs, key=sort_key)


def _deduplicate(recs: List[Recommendation]) -> List[Recommendation]:
    """Remove duplicate IDs (safety guard)."""
    seen = set()
    result = []
    for r in recs:
        if r.id not in seen:
            seen.add(r.id)
            result.append(r)
    return result


def _apply_caps(
    recs: List[Recommendation],
    max_total: int = MAX_RECOMMENDATIONS,
    max_per_cat: int = MAX_PER_CATEGORY,
) -> List[Recommendation]:
    """Cap recommendations to avoid overwhelming users."""
    cat_counts: Dict[Category, int] = {}
    result = []
    for r in recs:
        cat_count = cat_counts.get(r.category, 0)
        if cat_count >= max_per_cat:
            continue
        cat_counts[r.category] = cat_count + 1
        result.append(r)
        if len(result) >= max_total:
            break
    return result


# ─────────────────────────────────────────────────────────────────────────────
#  Main engine
# ─────────────────────────────────────────────────────────────────────────────

def generate_recommendations(raw: HealthMetrics) -> RecommendationResponse:
    """
    Full recommendation pipeline.

    Parameters
    ----------
    raw : HealthMetrics — user metrics (all fields optional)

    Returns
    -------
    RecommendationResponse — complete personalised recommendation package
    """
    # 1. Validate
    errors = _validate_metrics(raw)
    if errors:
        raise ValueError(f"Invalid health metrics: {'; '.join(errors)}")

    # 2. Normalise
    m = _normalise(raw)

    # 3. Sub-scores
    sub_scores = compute_sub_scores(m)

    # 4. Health score
    if m.health_score is not None:
        final_score = m.health_score
    else:
        final_score = compute_composite_score(sub_scores)
        m = HealthMetrics(
            sleep_hours=m.sleep_hours,
            steps=m.steps,
            calories=m.calories,
            water_intake_ml=m.water_intake_ml,
            stress_level=m.stress_level,
            heart_rate_bpm=m.heart_rate_bpm,
            health_score=final_score,
        )

    score_label = get_health_score_label(final_score)

    # 5. Run rules
    raw_recs = _run_rules(m)

    # 6. Rank, deduplicate, cap
    ranked  = _rank_recommendations(raw_recs)
    deduped = _deduplicate(ranked)
    capped  = _apply_caps(deduped)

    # 7. Score improvement potential
    score_potential = sum(r.score_impact for r in capped if r.priority in (
        Priority.CRITICAL, Priority.HIGH, Priority.MEDIUM
    ))
    max_possible = min(100.0, final_score + score_potential)
    improvement_potential = round(max_possible - final_score, 1)

    # 8. Counts
    critical_count = sum(1 for r in capped if r.priority == Priority.CRITICAL)
    high_count     = sum(1 for r in capped if r.priority == Priority.HIGH)

    # 9. Metric statuses
    metric_statuses = build_metric_statuses(m, sub_scores)

    # 10. Overall summary
    overall_summary = build_overall_summary(final_score, score_label, m)

    return RecommendationResponse(
        health_score               = final_score,
        health_score_label         = score_label,
        overall_summary            = overall_summary,
        metric_statuses            = metric_statuses,
        recommendations            = capped,
        total_count                = len(capped),
        critical_count             = critical_count,
        high_count                 = high_count,
        score_improvement_potential= improvement_potential,
        generated_at               = datetime.now(timezone.utc).isoformat(),
    )
