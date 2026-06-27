from typing import Annotated, AsyncGenerator
from uuid import UUID
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.security import decode_token
from app.db.session import AsyncSessionLocal

bearer = HTTPBearer(auto_error=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


DBSession = Annotated[AsyncSession, Depends(get_db)]


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
    db: DBSession,
):
    from fastapi import HTTPException, status
    from sqlalchemy import select
    from app.models.user import User

    exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if credentials is None:
        raise exc

    payload = decode_token(credentials.credentials)
    if not payload or payload.get("type") != "access":
        raise exc

    uid = payload.get("sub")
    if not uid:
        raise exc

    user = await db.get(User, UUID(uid))
    if not user or not user.is_active:
        raise exc
    return user


CurrentUser = Annotated[object, Depends(get_current_user)]
