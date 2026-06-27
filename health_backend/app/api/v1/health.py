from datetime import date
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Query, status

from app.core.deps import CurrentUser, DBSession
from app.schemas.common import MessageResponse
from app.schemas.health_log import HealthLogCreate, HealthLogRead, HealthLogUpdate
from app.services.health_log_service import HealthLogService

router = APIRouter()


@router.post(
    "/logs",
    response_model=HealthLogRead,
    status_code=status.HTTP_201_CREATED,
    summary="Submit a daily health log",
)
async def create_health_log(
    payload: HealthLogCreate,
    current_user: CurrentUser,
    db: DBSession,
) -> HealthLogRead:
    """
    Submit mood, stress, energy, hydration, and notes for a given date.
    Only one log per calendar day is allowed per user.
    """
    return await HealthLogService(db).create(current_user.id, payload)


@router.get(
    "/logs",
    response_model=List[HealthLogRead],
    summary="List health logs",
)
async def list_health_logs(
    current_user: CurrentUser,
    db: DBSession,
    start_date: Optional[date] = Query(None, description="Filter from this date (inclusive)"),
    end_date: Optional[date] = Query(None, description="Filter to this date (inclusive)"),
    limit: int = Query(30, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> List[HealthLogRead]:
    """Return paginated daily health logs for the current user, newest first."""
    return await HealthLogService(db).list_by_user(
        current_user.id, start_date, end_date, limit, offset
    )


@router.get(
    "/logs/today",
    response_model=Optional[HealthLogRead],
    summary="Get today's health log",
)
async def get_today_log(current_user: CurrentUser, db: DBSession) -> Optional[HealthLogRead]:
    """Return today's health log if it exists, otherwise null."""
    return await HealthLogService(db).get_by_date(current_user.id, date.today())


@router.get(
    "/logs/{log_id}",
    response_model=HealthLogRead,
    summary="Get a specific health log",
)
async def get_health_log(
    log_id: UUID,
    current_user: CurrentUser,
    db: DBSession,
) -> HealthLogRead:
    log = await HealthLogService(db).get_by_date(current_user.id, date.today())
    # Re-fetch by id via update path for consistency
    service = HealthLogService(db)
    from sqlalchemy import select
    from app.models.health_log import HealthLog
    from app.core.exceptions import NotFoundException
    result = await db.scalar(
        select(HealthLog).where(HealthLog.id == log_id, HealthLog.user_id == current_user.id)
    )
    if not result:
        raise NotFoundException("Health log not found")
    return result


@router.patch(
    "/logs/{log_id}",
    response_model=HealthLogRead,
    summary="Update a health log",
)
async def update_health_log(
    log_id: UUID,
    payload: HealthLogUpdate,
    current_user: CurrentUser,
    db: DBSession,
) -> HealthLogRead:
    """Partially update any field of an existing health log."""
    return await HealthLogService(db).update(current_user.id, log_id, payload)


@router.delete(
    "/logs/{log_id}",
    response_model=MessageResponse,
    summary="Delete a health log",
)
async def delete_health_log(
    log_id: UUID,
    current_user: CurrentUser,
    db: DBSession,
) -> MessageResponse:
    await HealthLogService(db).delete(current_user.id, log_id)
    return MessageResponse(message="Health log deleted")
