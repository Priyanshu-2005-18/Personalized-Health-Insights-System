from datetime import date, datetime
from typing import List, Optional
from uuid import UUID
from pydantic import Field, field_validator
from app.models.profile import ActivityLevel, GenderType
from app.schemas.common import BaseSchema


class ProfileCreate(BaseSchema):
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    date_of_birth: Optional[date] = None
    gender: Optional[GenderType] = None
    height_cm: Optional[float] = Field(default=None, gt=0, lt=300)
    weight_kg: Optional[float] = Field(default=None, gt=0, lt=700)
    activity_level: Optional[ActivityLevel] = None
    health_goals: Optional[List[str]] = None
    medical_conditions: Optional[List[str]] = None
    timezone: str = "UTC"


class ProfileUpdate(BaseSchema):
    first_name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    date_of_birth: Optional[date] = None
    gender: Optional[GenderType] = None
    height_cm: Optional[float] = Field(default=None, gt=0, lt=300)
    weight_kg: Optional[float] = Field(default=None, gt=0, lt=700)
    activity_level: Optional[ActivityLevel] = None
    health_goals: Optional[List[str]] = None
    medical_conditions: Optional[List[str]] = None
    avatar_url: Optional[str] = None
    timezone: Optional[str] = None


class ProfileRead(BaseSchema):
    id: UUID
    user_id: UUID
    first_name: str
    last_name: str
    date_of_birth: Optional[date]
    gender: Optional[GenderType]
    height_cm: Optional[float]
    weight_kg: Optional[float]
    activity_level: Optional[ActivityLevel]
    health_goals: Optional[List[str]]
    medical_conditions: Optional[List[str]]
    avatar_url: Optional[str]
    timezone: str
    updated_at: datetime
