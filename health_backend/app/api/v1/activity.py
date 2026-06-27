from datetime import date
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Query, status

from app.core.deps import CurrentUser, DBSession
from app.schemas.activity_log import ActivityLogCreate, ActivityLogRead
from app.schemas.common import MessageResponse
from app.services.activity_log_service import ActivityLogService

router = APIRouter()


@router.post(
    "",
    response_model=ActivityLogRead,
    status_code=status.HTTP_201_CREATED,
    summary="Log a physical activity",
)
async def create_activity_log(
    payload: ActivityLogCreate,
    current_user: CurrentUser,
    db: DBSession,
) -> ActivityLogRead:
    """
    Record a workout or physical activity session.
    Multiple activities can be logged per day (e.g. morning run + evening yoga).
    Intensity is on a 1–5 scale: 1 = very light, 5 = maximum effort.
    """
    return await ActivityLogService(db).create(current_user.id, payload)


@router.get(
    "",
    response_model=List[ActivityLogRead],
    summary="List activity logs",
)
async def list_activity_logs(
    current_user: CurrentUser,
    db: DBSession,
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    activity_type: Optional[str] = Query(None, description="Filter by type e.g. 'running'"),
    limit: int = Query(30, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> List[ActivityLogRead]:
    """Return paginated activity logs for the current user, newest first."""
    return await ActivityLogService(db).list_by_user(
        current_user.id, start_date, end_date, activity_type, limit, offset
    )


@router.get(
    "/{log_id}",
    response_model=ActivityLogRead,
    summary="Get a specific activity log",
)
async def get_activity_log(
    log_id: UUID,
    current_user: CurrentUser,
    db: DBSession,
) -> ActivityLogRead:
    return await ActivityLogService(db).get_or_404(current_user.id, log_id)


@router.delete(
    "/{log_id}",
    response_model=MessageResponse,
    summary="Delete an activity log",
)
async def delete_activity_log(
    log_id: UUID,
    current_user: CurrentUser,
    db: DBSession,
) -> MessageResponse:
    await ActivityLogService(db).delete(current_user.id, log_id)
    return MessageResponse(message="Activity log deleted")
