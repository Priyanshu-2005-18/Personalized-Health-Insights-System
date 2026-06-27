from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Query, status
from sqlalchemy import select

from app.core.deps import CurrentUser, DBSession
from app.core.exceptions import BadRequestException
from app.models.recommendation import RecCategory, Recommendation, RecommendationAction
from app.schemas.common import MessageResponse
from app.schemas.recommendation import RecommendationListResponse, RecommendationRead
from app.services.recommendation_service import RecommendationService

router = APIRouter()


@router.get(
    "",
    response_model=RecommendationListResponse,
    summary="List personalised recommendations",
)
async def list_recommendations(
    current_user: CurrentUser,
    db: DBSession,
    category: Optional[RecCategory] = Query(None, description="Filter by category"),
    unread_only: bool = Query(False, description="Return only unread recommendations"),
    limit: int = Query(20, ge=1, le=50),
    offset: int = Query(0, ge=0),
) -> RecommendationListResponse:
    """
    Return AI-generated recommendations for the current user.
    Dismissed recommendations are excluded. Ordered newest first.
    """
    return await RecommendationService(db).list_for_user(
        current_user.id, category, unread_only, limit, offset
    )


@router.get(
    "/{rec_id}",
    response_model=RecommendationRead,
    summary="Get a single recommendation",
)
async def get_recommendation(
    rec_id: UUID,
    current_user: CurrentUser,
    db: DBSession,
) -> RecommendationRead:
    return await RecommendationService(db).get_or_404(current_user.id, rec_id)


@router.patch(
    "/{rec_id}/read",
    response_model=RecommendationRead,
    summary="Mark a recommendation as read",
)
async def mark_read(
    rec_id: UUID,
    current_user: CurrentUser,
    db: DBSession,
) -> RecommendationRead:
    return await RecommendationService(db).mark_read(current_user.id, rec_id)


@router.patch(
    "/{rec_id}/dismiss",
    response_model=RecommendationRead,
    summary="Dismiss a recommendation",
)
async def dismiss(
    rec_id: UUID,
    current_user: CurrentUser,
    db: DBSession,
) -> RecommendationRead:
    """Dismissed recommendations no longer appear in the default listing."""
    return await RecommendationService(db).dismiss(current_user.id, rec_id)


@router.patch(
    "/{rec_id}/actions/{action_id}/complete",
    response_model=RecommendationRead,
    summary="Mark an action step as completed",
)
async def complete_action(
    rec_id: UUID,
    action_id: UUID,
    current_user: CurrentUser,
    db: DBSession,
) -> RecommendationRead:
    return await RecommendationService(db).mark_action_complete(
        current_user.id, rec_id, action_id
    )


@router.post(
    "/generate",
    response_model=RecommendationListResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Trigger ML recommendation generation",
)
async def generate_recommendations(
    current_user: CurrentUser,
    db: DBSession,
) -> RecommendationListResponse:
    """
    Run the ML pipeline against the current user's last 30 days of data
    and persist the resulting recommendations.

    - Uses trained Scikit-learn models when available.
    - Falls back to the rule-based engine otherwise.
    - Returns the full updated recommendation list immediately.
    """
    from datetime import date, timedelta
    from sqlalchemy import select

    from app.ml.features import build_feature_vector
    from app.ml.pipeline import generate_recommendations as ml_generate
    from app.models.health_log import HealthLog
    from app.models.sleep_log import SleepLog
    from app.models.activity_log import ActivityLog
    from app.models.nutrition_log import NutritionLog
    from app.services.profile_service import ProfileService

    since = date.today() - timedelta(days=30)

    # Load last 30 days of each data type
    profile = await ProfileService(db).get_by_user_id(current_user.id)

    health_logs = list(
        (await db.scalars(
            select(HealthLog)
            .where(HealthLog.user_id == current_user.id, HealthLog.log_date >= since)
        )).all()
    )
    sleep_logs = list(
        (await db.scalars(
            select(SleepLog)
            .where(SleepLog.user_id == current_user.id, SleepLog.sleep_date >= since)
        )).all()
    )
    activity_logs = list(
        (await db.scalars(
            select(ActivityLog)
            .where(ActivityLog.user_id == current_user.id, ActivityLog.activity_date >= since)
        )).all()
    )
    nutrition_logs = list(
        (await db.scalars(
            select(NutritionLog)
            .where(NutritionLog.user_id == current_user.id, NutritionLog.log_date >= since)
        )).all()
    )

    if not any([health_logs, sleep_logs, activity_logs, nutrition_logs]):
        raise BadRequestException(
            "Not enough data to generate recommendations. "
            "Please log at least a few days of health data first."
        )

    # Build feature vector and run pipeline
    features = build_feature_vector(
        profile, health_logs, sleep_logs, activity_logs, nutrition_logs
    )
    raw_recs = ml_generate(features)

    # Persist to DB
    rec_service = RecommendationService(db)
    orm_recs = []
    for r in raw_recs:
        actions_data = r.pop("actions", [])
        rec = Recommendation(user_id=current_user.id, **r)
        db.add(rec)
        await db.flush()

        for idx, action_text in enumerate(actions_data):
            db.add(RecommendationAction(
                recommendation_id=rec.id,
                action_text=action_text,
                sort_order=idx,
            ))
        orm_recs.append(rec)

    await db.commit()

    # Return the refreshed full list
    return await rec_service.list_for_user(current_user.id)
