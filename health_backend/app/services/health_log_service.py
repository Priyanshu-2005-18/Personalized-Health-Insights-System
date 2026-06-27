import logging
from datetime import date
from typing import List, Optional
from uuid import UUID
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictException, NotFoundException
from app.models.health_log import HealthLog
from app.schemas.health_log import HealthLogCreate, HealthLogUpdate

logger = logging.getLogger(__name__)


class HealthLogService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create(self, user_id: UUID, payload: HealthLogCreate) -> HealthLog:
        existing = await self.db.scalar(
            select(HealthLog).where(
                HealthLog.user_id == user_id,
                HealthLog.log_date == payload.log_date,
            )
        )
        if existing:
            raise ConflictException(f"Health log for {payload.log_date} already exists")

        log = HealthLog(user_id=user_id, **payload.model_dump())
        await self._calculate_score_and_recommendations(user_id, log)
        self.db.add(log)
        await self.db.commit()
        await self.db.refresh(log)
        return log

    async def get_by_date(self, user_id: UUID, log_date: date) -> Optional[HealthLog]:
        return await self.db.scalar(
            select(HealthLog).where(
                HealthLog.user_id == user_id,
                HealthLog.log_date == log_date,
            )
        )

    async def list_by_user(
        self,
        user_id: UUID,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        limit: int = 30,
        offset: int = 0,
    ) -> List[HealthLog]:
        query = select(HealthLog).where(HealthLog.user_id == user_id)
        if start_date:
            query = query.where(HealthLog.log_date >= start_date)
        if end_date:
            query = query.where(HealthLog.log_date <= end_date)
        query = query.order_by(HealthLog.log_date.desc()).limit(limit).offset(offset)
        result = await self.db.scalars(query)
        return list(result.all())

    async def update(self, user_id: UUID, log_id: UUID, payload: HealthLogUpdate) -> HealthLog:
        log = await self.db.scalar(
            select(HealthLog).where(HealthLog.id == log_id, HealthLog.user_id == user_id)
        )
        if not log:
            raise NotFoundException("Health log not found")

        for field, value in payload.model_dump(exclude_none=True).items():
            setattr(log, field, value)

        await self._calculate_score_and_recommendations(user_id, log)
        await self.db.commit()
        await self.db.refresh(log)
        return log

    async def delete(self, user_id: UUID, log_id: UUID) -> None:
        log = await self.db.scalar(
            select(HealthLog).where(HealthLog.id == log_id, HealthLog.user_id == user_id)
        )
        if not log:
            raise NotFoundException("Health log not found")
        await self.db.delete(log)
        await self.db.commit()

    async def _calculate_score_and_recommendations(self, user_id: UUID, log: HealthLog) -> None:
        from app.ml.predictor import HealthScorePredictor
        from app.recommendation_engine.models.health import HealthMetrics as RecHealthMetrics
        from app.recommendation_engine.services.recommendation_service import generate_recommendations
        from app.models.recommendation import Recommendation as DBRecommendation, RecommendationAction as DBRecommendationAction, RecCategory as DBRecCategory, RecPriority as DBRecPriority

        # 1. Predict health score using ML predictor
        predictor = HealthScorePredictor.get_instance()
        metrics = {
            "sleep_hours": float(log.sleep_hours) if log.sleep_hours is not None else None,
            "steps": log.steps,
            "calories": log.calories,
            "water_intake_ml": log.water_ml,
            "stress_level": log.stress_level,
            "heart_rate_bpm": log.heart_rate_bpm,
        }
        # Filter out None values
        metrics_filtered = {k: v for k, v in metrics.items() if v is not None}

        pred_score = None
        if metrics_filtered:
            try:
                pred_result = predictor.predict_single(**metrics_filtered)
                pred_score = pred_result.get("health_score")
                log.health_score = pred_score
            except Exception as e:
                logger.error(f"Error predicting health score: {e}")

        # 2. Generate recommendations using recommendation engine
        rec_metrics = RecHealthMetrics(
            sleep_hours=float(log.sleep_hours) if log.sleep_hours is not None else None,
            steps=log.steps,
            calories=log.calories,
            water_intake_ml=log.water_ml,
            stress_level=log.stress_level,
            heart_rate_bpm=log.heart_rate_bpm,
            health_score=float(pred_score) if pred_score is not None else None,
        )
        try:
            rec_response = generate_recommendations(rec_metrics)

            # Delete old recommendations for this user to keep it clean
            await self.db.execute(
                delete(DBRecommendation).where(DBRecommendation.user_id == user_id)
            )

            # Save new recommendations to database
            for r in rec_response.recommendations:
                cat_val = r.category.value if r.category.value != "heart_rate" else "general"
                pri_val = r.priority.value
                if pri_val == "critical":
                    pri_val = "high"

                db_rec = DBRecommendation(
                    user_id=user_id,
                    category=DBRecCategory(cat_val),
                    priority=DBRecPriority(pri_val),
                    title=r.title,
                    content=r.detail,
                    confidence_score=0.9,
                    model_version="1.0.0",
                )
                self.db.add(db_rec)

                for idx, act in enumerate(r.actions):
                    db_act = DBRecommendationAction(
                        recommendation=db_rec,
                        action_text=act.description,
                        sort_order=idx + 1,
                    )
                    self.db.add(db_act)
        except Exception as e:
            logger.error(f"Error generating or saving recommendations in health log: {e}")

