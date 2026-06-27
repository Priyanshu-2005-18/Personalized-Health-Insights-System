from datetime import date
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Query, status

from app.core.deps import CurrentUser, DBSession
from app.schemas.common import MessageResponse
from app.schemas.nutrition_log import NutritionLogCreate, NutritionLogRead
from app.services.nutrition_log_service import NutritionLogService

router = APIRouter()


@router.post(
    "",
    response_model=NutritionLogRead,
    status_code=status.HTTP_201_CREATED,
    summary="Log a meal with food items",
)
async def create_nutrition_log(
    payload: NutritionLogCreate,
    current_user: CurrentUser,
    db: DBSession,
) -> NutritionLogRead:
    """
    Record a meal (breakfast, lunch, dinner, snack, pre/post-workout).
    Supply a list of `items` with food name, serving size, and macros.
    Aggregate totals (calories, protein, carbs, fat, fiber) are computed
    automatically from the item list.
    """
    return await NutritionLogService(db).create(current_user.id, payload)


@router.get(
    "",
    response_model=List[NutritionLogRead],
    summary="List nutrition logs",
)
async def list_nutrition_logs(
    current_user: CurrentUser,
    db: DBSession,
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    limit: int = Query(30, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> List[NutritionLogRead]:
    """Return paginated nutrition logs with their food items, newest first."""
    return await NutritionLogService(db).list_by_user(
        current_user.id, start_date, end_date, limit, offset
    )


@router.get(
    "/{log_id}",
    response_model=NutritionLogRead,
    summary="Get a specific nutrition log",
)
async def get_nutrition_log(
    log_id: UUID,
    current_user: CurrentUser,
    db: DBSession,
) -> NutritionLogRead:
    """Retrieve a single meal log including all food items."""
    return await NutritionLogService(db).get_or_404(current_user.id, log_id)


@router.delete(
    "/{log_id}",
    response_model=MessageResponse,
    summary="Delete a nutrition log",
)
async def delete_nutrition_log(
    log_id: UUID,
    current_user: CurrentUser,
    db: DBSession,
) -> MessageResponse:
    """Delete a meal log and all its associated food items (cascade)."""
    await NutritionLogService(db).delete(current_user.id, log_id)
    return MessageResponse(message="Nutrition log deleted")
