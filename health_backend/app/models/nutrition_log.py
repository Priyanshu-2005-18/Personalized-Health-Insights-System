import uuid
import enum
from datetime import date, datetime
from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import CheckConstraint, Date, DateTime, Enum, ForeignKey, Integer, Numeric, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.user import User


class MealType(str, enum.Enum):
    breakfast = "breakfast"
    lunch = "lunch"
    dinner = "dinner"
    snack = "snack"
    pre_workout = "pre_workout"
    post_workout = "post_workout"


class NutritionLog(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "nutrition_logs"
    __table_args__ = (
        CheckConstraint("total_calories >= 0", name="chk_total_calories"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    log_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    meal_type: Mapped[MealType] = mapped_column(Enum(MealType), nullable=False)
    total_calories: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    total_protein_g: Mapped[Optional[float]] = mapped_column(Numeric(6, 2), nullable=True)
    total_carbs_g: Mapped[Optional[float]] = mapped_column(Numeric(6, 2), nullable=True)
    total_fat_g: Mapped[Optional[float]] = mapped_column(Numeric(6, 2), nullable=True)
    total_fiber_g: Mapped[Optional[float]] = mapped_column(Numeric(6, 2), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    user: Mapped["User"] = relationship("User", back_populates="nutrition_logs")
    items: Mapped[List["NutritionItem"]] = relationship(
        "NutritionItem", back_populates="nutrition_log", cascade="all, delete-orphan"
    )


class NutritionItem(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "nutrition_items"
    __table_args__ = (
        CheckConstraint("serving_qty > 0", name="chk_serving_qty"),
        CheckConstraint("calories >= 0", name="chk_item_calories"),
    )

    nutrition_log_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("nutrition_logs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    food_name: Mapped[str] = mapped_column(String(200), nullable=False)
    serving_qty: Mapped[float] = mapped_column(Numeric(6, 2), nullable=False)
    serving_unit: Mapped[str] = mapped_column(String(30), nullable=False)
    calories: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    protein_g: Mapped[Optional[float]] = mapped_column(Numeric(6, 2), nullable=True)
    carbs_g: Mapped[Optional[float]] = mapped_column(Numeric(6, 2), nullable=True)
    fat_g: Mapped[Optional[float]] = mapped_column(Numeric(6, 2), nullable=True)
    fiber_g: Mapped[Optional[float]] = mapped_column(Numeric(6, 2), nullable=True)
    sodium_mg: Mapped[Optional[float]] = mapped_column(Numeric(7, 2), nullable=True)
    sugar_g: Mapped[Optional[float]] = mapped_column(Numeric(6, 2), nullable=True)

    nutrition_log: Mapped["NutritionLog"] = relationship("NutritionLog", back_populates="items")
