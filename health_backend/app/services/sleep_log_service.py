from datetime import date
from typing import List, Optional
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundException
from app.models.sleep_log import SleepLog
from app.schemas.sleep_log import SleepLogCreate


class SleepLogService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create(self, user_id: UUID, payload: SleepLogCreate) -> SleepLog:
        # payload.model_dump() converts SleepStages → dict automatically
        data = payload.model_dump()
        stages = data.pop("sleep_stages", None)  # already a dict or None

        log = SleepLog(
            user_id=user_id,
            **data,
            sleep_stages=stages if stages else None,  # pass dict directly
        )
        log.duration_min = log.compute_duration()
        self.db.add(log)
        await self.db.commit()
        await self.db.refresh(log)
        return log

    async def list_by_user(
        self,
        user_id: UUID,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        limit: int = 30,
        offset: int = 0,
    ) -> List[SleepLog]:
        query = select(SleepLog).where(SleepLog.user_id == user_id)
        if start_date:
            query = query.where(SleepLog.sleep_date >= start_date)
        if end_date:
            query = query.where(SleepLog.sleep_date <= end_date)
        query = query.order_by(SleepLog.sleep_date.desc()).limit(limit).offset(offset)
        result = await self.db.scalars(query)
        return list(result.all())

    async def get_or_404(self, user_id: UUID, log_id: UUID) -> SleepLog:
        log = await self.db.scalar(
            select(SleepLog).where(SleepLog.id == log_id, SleepLog.user_id == user_id)
        )
        if not log:
            raise NotFoundException("Sleep log not found")
        return log

    async def delete(self, user_id: UUID, log_id: UUID) -> None:
        log = await self.get_or_404(user_id, log_id)
        await self.db.delete(log)
        await self.db.commit()
