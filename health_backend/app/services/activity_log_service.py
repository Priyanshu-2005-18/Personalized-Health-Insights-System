from datetime import date
from typing import List, Optional
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundException
from app.models.activity_log import ActivityLog
from app.schemas.activity_log import ActivityLogCreate


class ActivityLogService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create(self, user_id: UUID, payload: ActivityLogCreate) -> ActivityLog:
        log = ActivityLog(user_id=user_id, **payload.model_dump())
        self.db.add(log)
        await self.db.commit()
        await self.db.refresh(log)
        return log

    async def list_by_user(
        self,
        user_id: UUID,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        activity_type: Optional[str] = None,
        limit: int = 30,
        offset: int = 0,
    ) -> List[ActivityLog]:
        query = select(ActivityLog).where(ActivityLog.user_id == user_id)
        if start_date:
            query = query.where(ActivityLog.activity_date >= start_date)
        if end_date:
            query = query.where(ActivityLog.activity_date <= end_date)
        if activity_type:
            query = query.where(ActivityLog.activity_type == activity_type)
        query = query.order_by(ActivityLog.activity_date.desc()).limit(limit).offset(offset)
        result = await self.db.scalars(query)
        return list(result.all())

    async def get_or_404(self, user_id: UUID, log_id: UUID) -> ActivityLog:
        log = await self.db.scalar(
            select(ActivityLog).where(
                ActivityLog.id == log_id, ActivityLog.user_id == user_id
            )
        )
        if not log:
            raise NotFoundException("Activity log not found")
        return log

    async def delete(self, user_id: UUID, log_id: UUID) -> None:
        log = await self.get_or_404(user_id, log_id)
        await self.db.delete(log)
        await self.db.commit()
