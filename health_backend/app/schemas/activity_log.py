from datetime import date, datetime
from typing import Optional
from uuid import UUID
from pydantic import Field
from app.schemas.common import BaseSchema


class ActivityLogCreate(BaseSchema):
    activity_date: date
    activity_type: str = Field(min_length=1, max_length=50)
    duration_min: Optional[int] = Field(default=None, gt=0)
    distance_m: Optional[int] = Field(default=None, ge=0)
    calories_burned: Optional[int] = Field(default=None, ge=0)
    intensity: Optional[int] = Field(default=None, ge=1, le=5)
    steps: Optional[int] = Field(default=None, ge=0)
    avg_heart_rate: Optional[float] = Field(default=None, gt=0)
    max_heart_rate: Optional[float] = Field(default=None, gt=0)
    source: str = "manual"


class ActivityLogRead(BaseSchema):
    id: UUID
    user_id: UUID
    activity_date: date
    activity_type: str
    duration_min: Optional[int]
    distance_m: Optional[int]
    calories_burned: Optional[int]
    intensity: Optional[int]
    steps: Optional[int]
    avg_heart_rate: Optional[float]
    max_heart_rate: Optional[float]
    source: str
    created_at: datetime
