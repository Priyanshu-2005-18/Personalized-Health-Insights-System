from datetime import date, datetime
from typing import Optional
from uuid import UUID
from pydantic import Field
from app.schemas.common import BaseSchema


class HealthLogCreate(BaseSchema):
    log_date: date
    mood_score: Optional[int] = Field(default=None, ge=1, le=10)
    stress_level: Optional[int] = Field(default=None, ge=1, le=10)
    energy_level: Optional[int] = Field(default=None, ge=1, le=10)
    water_ml: Optional[int] = Field(default=None, ge=0)
    sleep_hours: Optional[float] = Field(default=None, ge=0.0, le=24.0)
    steps: Optional[int] = Field(default=None, ge=0, le=100000)
    calories: Optional[int] = Field(default=None, ge=0, le=10000)
    heart_rate_bpm: Optional[int] = Field(default=None, ge=30, le=250)
    notes: Optional[str] = None


class HealthLogUpdate(BaseSchema):
    mood_score: Optional[int] = Field(default=None, ge=1, le=10)
    stress_level: Optional[int] = Field(default=None, ge=1, le=10)
    energy_level: Optional[int] = Field(default=None, ge=1, le=10)
    water_ml: Optional[int] = Field(default=None, ge=0)
    sleep_hours: Optional[float] = Field(default=None, ge=0.0, le=24.0)
    steps: Optional[int] = Field(default=None, ge=0, le=100000)
    calories: Optional[int] = Field(default=None, ge=0, le=10000)
    heart_rate_bpm: Optional[int] = Field(default=None, ge=30, le=250)
    notes: Optional[str] = None


class HealthLogRead(BaseSchema):
    id: UUID
    user_id: UUID
    log_date: date
    mood_score: Optional[int]
    stress_level: Optional[int]
    energy_level: Optional[int]
    water_ml: Optional[int]
    sleep_hours: Optional[float]
    steps: Optional[int]
    calories: Optional[int]
    heart_rate_bpm: Optional[int]
    health_score: Optional[float]
    notes: Optional[str]
    created_at: datetime
