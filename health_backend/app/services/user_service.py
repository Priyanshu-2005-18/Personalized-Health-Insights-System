from typing import Optional
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundException
from app.models.user import User
from app.schemas.user import UserUpdate


class UserService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_id(self, user_id: UUID) -> Optional[User]:
        return await self.db.get(User, user_id)

    async def get_by_email(self, email: str) -> Optional[User]:
        return await self.db.scalar(select(User).where(User.email == email.lower()))

    async def update(self, user_id: UUID, payload: UserUpdate) -> User:
        user = await self.get_by_id(user_id)
        if not user:
            raise NotFoundException("User not found")

        for field, value in payload.model_dump(exclude_none=True).items():
            setattr(user, field, value)

        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def delete(self, user_id: UUID) -> None:
        user = await self.get_by_id(user_id)
        if not user:
            raise NotFoundException("User not found")
        await self.db.delete(user)
        await self.db.commit()
