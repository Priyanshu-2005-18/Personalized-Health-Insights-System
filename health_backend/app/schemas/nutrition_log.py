from datetime import date, datetime
from typing import List, Optional
from uuid import UUID
from pydantic import Field
from app.models.nutrition_log import MealType
from app.schemas.common import BaseSchema


class NutritionItemCreate(BaseSchema):
    food_name: str = Field(min_length=1, max_length=200)
    serving_qty: float = Field(gt=0)
    serving_unit: str = Field(min_length=1, max_length=30)
    calories: Optional[int] = Field(default=None, ge=0)
    protein_g: Optional[float] = Field(default=None, ge=0)
    carbs_g: Optional[float] = Field(default=None, ge=0)
    fat_g: Optional[float] = Field(default=None, ge=0)
    fiber_g: Optional[float] = Field(default=None, ge=0)
    sodium_mg: Optional[float] = Field(default=None, ge=0)
    sugar_g: Optional[float] = Field(default=None, ge=0)


class NutritionItemRead(BaseSchema):
    id: UUID
    nutrition_log_id: UUID
    food_name: str
    serving_qty: float
    serving_unit: str
    calories: Optional[int]
    protein_g: Optional[float]
    carbs_g: Optional[float]
    fat_g: Optional[float]
    fiber_g: Optional[float]
    sodium_mg: Optional[float]
    sugar_g: Optional[float]


class NutritionLogCreate(BaseSchema):
    log_date: date
    meal_type: MealType
    items: List[NutritionItemCreate] = Field(default_factory=list)


class NutritionLogRead(BaseSchema):
    id: UUID
    user_id: UUID
    log_date: date
    meal_type: MealType
    total_calories: Optional[int]
    total_protein_g: Optional[float]
    total_carbs_g: Optional[float]
    total_fat_g: Optional[float]
    total_fiber_g: Optional[float]
    items: List[NutritionItemRead]
    created_at: datetime
