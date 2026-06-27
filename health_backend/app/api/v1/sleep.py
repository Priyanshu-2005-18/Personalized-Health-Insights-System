from datetime import date
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Query, status

from app.core.deps import CurrentUser, DBSession
from app.schemas.common import MessageResponse
from app.schemas.sleep_log import SleepLogCreate, SleepLogRead
from app.services.sleep_log_service import SleepLogService

router = APIRouter()


@router.post(
    "",
    response_model=SleepLogRead,
    status_code=status.HTTP_201_CREATED,
    summary="Log a sleep session",
)
async def create_sleep_log(
    payload: SleepLogCreate,
    current_user: CurrentUser,
    db: DBSession,
) -> SleepLogRead:
    """
    Record a sleep session including bedtime, wake time, quality score,
    optional sleep-stage breakdown (JSONB), and interruption count.
    Duration is automatically computed from bedtime and wake_time.
    """
    return await SleepLogService(db).create(current_user.id, payload)


@router.get(
    "",
    response_model=List[SleepLogRead],
    summary="List sleep logs",
)
async def list_sleep_logs(
    current_user: CurrentUser,
    db: DBSession,
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    limit: int = Query(30, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> List[SleepLogRead]:
    """Return paginated sleep logs for the current user, newest first."""
    return await SleepLogService(db).list_by_user(
        current_user.id, start_date, end_date, limit, offset
    )


@router.get(
    "/{log_id}",
    response_model=SleepLogRead,
    summary="Get a specific sleep log",
)
async def get_sleep_log(
    log_id: UUID,
    current_user: CurrentUser,
    db: DBSession,
) -> SleepLogRead:
    return await SleepLogService(db).get_or_404(current_user.id, log_id)


@router.delete(
    "/{log_id}",
    response_model=MessageResponse,
    summary="Delete a sleep log",
)
async def delete_sleep_log(
    log_id: UUID,
    current_user: CurrentUser,
    db: DBSession,
) -> MessageResponse:
    await SleepLogService(db).delete(current_user.id, log_id)
    return MessageResponse(message="Sleep log deleted")
