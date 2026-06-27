from datetime import date, datetime
from typing import Optional
from uuid import UUID
from pydantic import Field, model_validator
from app.schemas.common import BaseSchema


class SleepStages(BaseSchema):
    deep_min: Optional[int] = Field(default=None, ge=0)
    light_min: Optional[int] = Field(default=None, ge=0)
    rem_min: Optional[int] = Field(default=None, ge=0)
    awake_min: Optional[int] = Field(default=None, ge=0)


class SleepLogCreate(BaseSchema):
    sleep_date: date
    bedtime: datetime
    wake_time: datetime
    quality_score: Optional[int] = Field(default=None, ge=1, le=10)
    sleep_stages: Optional[SleepStages] = None
    interruptions: int = Field(default=0, ge=0)
    source: str = "manual"

    @model_validator(mode="after")
    def wake_after_bed(self) -> "SleepLogCreate":
        if self.wake_time <= self.bedtime:
            raise ValueError("wake_time must be after bedtime")
        return self


class SleepLogRead(BaseSchema):
    id: UUID
    user_id: UUID
    sleep_date: date
    bedtime: datetime
    wake_time: datetime
    duration_min: Optional[int]
    quality_score: Optional[int]
    sleep_stages: Optional[dict]
    interruptions: int
    source: str
    created_at: datetime
