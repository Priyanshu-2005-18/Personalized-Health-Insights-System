from datetime import datetime
from typing import List, Optional
from uuid import UUID
from app.models.recommendation import RecCategory, RecPriority
from app.schemas.common import BaseSchema


class RecommendationActionRead(BaseSchema):
    id: UUID
    action_text: str
    sort_order: int
    is_completed: bool
    completed_at: Optional[datetime]


class RecommendationRead(BaseSchema):
    id: UUID
    user_id: UUID
    category: RecCategory
    priority: RecPriority
    title: str
    content: str
    confidence_score: Optional[float]
    model_version: Optional[str]
    is_read: bool
    is_dismissed: bool
    generated_at: datetime
    expires_at: Optional[datetime]
    actions: List[RecommendationActionRead]


class RecommendationListResponse(BaseSchema):
    items: List[RecommendationRead]
    total: int
    unread_count: int


class RecommendationMarkRead(BaseSchema):
    is_read: bool = True


class RecommendationDismiss(BaseSchema):
    is_dismissed: bool = True
