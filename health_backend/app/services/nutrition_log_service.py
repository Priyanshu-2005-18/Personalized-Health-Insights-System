from datetime import date
from typing import List, Optional
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundException
from app.models.nutrition_log import NutritionLog, NutritionItem
from app.schemas.nutrition_log import NutritionLogCreate


class NutritionLogService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create(self, user_id: UUID, payload: NutritionLogCreate) -> NutritionLog:
        items_data = payload.model_dump(exclude={"items"})
        log = NutritionLog(user_id=user_id, **items_data)

        # Compute aggregate macros from items
        total_cal = total_protein = total_carbs = total_fat = total_fiber = 0.0
        nutrition_items = []
        for item_payload in payload.items:
            item = NutritionItem(
                nutrition_log_id=None,  # set after flush
                **item_payload.model_dump()
            )
            nutrition_items.append(item)
            total_cal     += item_payload.calories    or 0
            total_protein += item_payload.protein_g   or 0
            total_carbs   += item_payload.carbs_g     or 0
            total_fat     += item_payload.fat_g       or 0
            total_fiber   += item_payload.fiber_g     or 0

        log.total_calories  = int(total_cal)
        log.total_protein_g = round(total_protein, 2)
        log.total_carbs_g   = round(total_carbs, 2)
        log.total_fat_g     = round(total_fat, 2)
        log.total_fiber_g   = round(total_fiber, 2)

        self.db.add(log)
        await self.db.flush()

        for item in nutrition_items:
            item.nutrition_log_id = log.id
            self.db.add(item)

        await self.db.commit()

        # Re-fetch with items eager-loaded
        return await self._get_with_items(log.id)

    async def list_by_user(
        self,
        user_id: UUID,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        limit: int = 30,
        offset: int = 0,
    ) -> List[NutritionLog]:
        query = (
            select(NutritionLog)
            .options(selectinload(NutritionLog.items))
            .where(NutritionLog.user_id == user_id)
        )
        if start_date:
            query = query.where(NutritionLog.log_date >= start_date)
        if end_date:
            query = query.where(NutritionLog.log_date <= end_date)
        query = query.order_by(NutritionLog.log_date.desc()).limit(limit).offset(offset)
        result = await self.db.scalars(query)
        return list(result.all())

    async def get_or_404(self, user_id: UUID, log_id: UUID) -> NutritionLog:
        log = await self._get_with_items(log_id)
        if not log or log.user_id != user_id:
            raise NotFoundException("Nutrition log not found")
        return log

    async def delete(self, user_id: UUID, log_id: UUID) -> None:
        log = await self.get_or_404(user_id, log_id)
        await self.db.delete(log)
        await self.db.commit()

    async def _get_with_items(self, log_id: UUID) -> Optional[NutritionLog]:
        return await self.db.scalar(
            select(NutritionLog)
            .options(selectinload(NutritionLog.items))
            .where(NutritionLog.id == log_id)
        )
