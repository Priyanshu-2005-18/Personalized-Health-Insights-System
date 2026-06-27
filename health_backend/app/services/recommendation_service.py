from typing import List, Optional
from uuid import UUID
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundException
from app.models.recommendation import Recommendation, RecCategory
from app.schemas.recommendation import RecommendationListResponse


class RecommendationService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def list_for_user(
        self,
        user_id: UUID,
        category: Optional[RecCategory] = None,
        unread_only: bool = False,
        limit: int = 20,
        offset: int = 0,
    ) -> RecommendationListResponse:
        base_query = (
            select(Recommendation)
            .options(selectinload(Recommendation.actions))
            .where(
                Recommendation.user_id == user_id,
                Recommendation.is_dismissed == False,  # noqa: E712
            )
        )
        if category:
            base_query = base_query.where(Recommendation.category == category)
        if unread_only:
            base_query = base_query.where(Recommendation.is_read == False)  # noqa: E712

        # Total count
        count_query = select(func.count()).select_from(base_query.subquery())
        total = await self.db.scalar(count_query) or 0

        # Unread count
        unread_query = select(func.count()).select_from(
            select(Recommendation)
            .where(
                Recommendation.user_id == user_id,
                Recommendation.is_read == False,  # noqa: E712
                Recommendation.is_dismissed == False,  # noqa: E712
            )
            .subquery()
        )
        unread_count = await self.db.scalar(unread_query) or 0

        # Paginated items
        items_query = (
            base_query
            .order_by(Recommendation.generated_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.db.scalars(items_query)
        items = list(result.all())

        return RecommendationListResponse(
            items=items, total=total, unread_count=unread_count
        )

    async def get_or_404(self, user_id: UUID, rec_id: UUID) -> Recommendation:
        rec = await self.db.scalar(
            select(Recommendation)
            .options(selectinload(Recommendation.actions))
            .where(Recommendation.id == rec_id, Recommendation.user_id == user_id)
        )
        if not rec:
            raise NotFoundException("Recommendation not found")
        return rec

    async def mark_read(self, user_id: UUID, rec_id: UUID) -> Recommendation:
        rec = await self.get_or_404(user_id, rec_id)
        rec.is_read = True
        await self.db.commit()
        await self.db.refresh(rec)
        return rec

    async def dismiss(self, user_id: UUID, rec_id: UUID) -> Recommendation:
        rec = await self.get_or_404(user_id, rec_id)
        rec.is_dismissed = True
        await self.db.commit()
        await self.db.refresh(rec)
        return rec

    async def mark_action_complete(
        self, user_id: UUID, rec_id: UUID, action_id: UUID
    ) -> Recommendation:
        from datetime import datetime, timezone
        from app.models.recommendation import RecommendationAction

        rec = await self.get_or_404(user_id, rec_id)
        action = next((a for a in rec.actions if a.id == action_id), None)
        if not action:
            raise NotFoundException("Action not found")

        action.is_completed = True
        action.completed_at = datetime.now(timezone.utc)
        await self.db.commit()
        await self.db.refresh(rec)
        return rec

    async def save_ml_recommendations(
        self, user_id: UUID, recommendations: List[Recommendation]
    ) -> List[Recommendation]:
        for rec in recommendations:
            rec.user_id = user_id
            self.db.add(rec)
        await self.db.commit()
        return recommendations
