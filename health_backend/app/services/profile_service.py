from typing import Optional
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictException, NotFoundException
from app.models.profile import UserProfile
from app.schemas.profile import ProfileCreate, ProfileUpdate


class ProfileService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_user_id(self, user_id: UUID) -> Optional[UserProfile]:
        return await self.db.scalar(
            select(UserProfile).where(UserProfile.user_id == user_id)
        )

    async def create(self, user_id: UUID, payload: ProfileCreate) -> UserProfile:
        existing = await self.get_by_user_id(user_id)
        if existing:
            raise ConflictException("Profile already exists for this user")

        profile = UserProfile(user_id=user_id, **payload.model_dump())
        self.db.add(profile)
        await self.db.commit()
        await self.db.refresh(profile)
        return profile

    async def update(self, user_id: UUID, payload: ProfileUpdate) -> UserProfile:
        profile = await self.get_by_user_id(user_id)
        if not profile:
            raise NotFoundException("Profile not found")

        for field, value in payload.model_dump(exclude_none=True).items():
            setattr(profile, field, value)

        await self.db.commit()
        await self.db.refresh(profile)
        return profile

    async def get_or_404(self, user_id: UUID) -> UserProfile:
        profile = await self.get_by_user_id(user_id)
        if not profile:
            raise NotFoundException("Profile not found")
        return profile
