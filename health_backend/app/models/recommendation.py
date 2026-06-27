import uuid
import enum
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import Boolean, CheckConstraint, DateTime, Enum, ForeignKey, Numeric, SmallInteger, String, Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.user import User


class RecCategory(str, enum.Enum):
    sleep = "sleep"
    activity = "activity"
    nutrition = "nutrition"
    hydration = "hydration"
    stress = "stress"
    general = "general"


class RecPriority(str, enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"


class Recommendation(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "recommendations"
    __table_args__ = (
        CheckConstraint("confidence_score BETWEEN 0.0 AND 1.0", name="chk_confidence"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    category: Mapped[RecCategory] = mapped_column(Enum(RecCategory), nullable=False, index=True)
    priority: Mapped[RecPriority] = mapped_column(
        Enum(RecPriority), nullable=False, default=RecPriority.medium
    )
    title: Mapped[str] = mapped_column(Text, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    confidence_score: Mapped[Optional[float]] = mapped_column(Numeric(4, 3), nullable=True)
    model_version: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    is_read: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_dismissed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped["User"] = relationship("User", back_populates="recommendations")
    actions: Mapped[List["RecommendationAction"]] = relationship(
        "RecommendationAction", back_populates="recommendation", cascade="all, delete-orphan",
        order_by="RecommendationAction.sort_order"
    )


class RecommendationAction(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "recommendation_actions"

    recommendation_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("recommendations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    action_text: Mapped[str] = mapped_column(Text, nullable=False)
    sort_order: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    is_completed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    recommendation: Mapped["Recommendation"] = relationship(
        "Recommendation", back_populates="actions"
    )
