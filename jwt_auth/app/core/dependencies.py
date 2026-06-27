"""
dependencies.py
===============
FastAPI dependency-injection functions used across route handlers.

Dependency graph:
  get_db              → yields AsyncSession
  get_current_user    → decodes Bearer token → fetches User from DB
  get_current_active  → get_current_user + is_active check
  require_role(...)   → get_current_active + role check
  AdminUser           → shorthand for require_role("admin")

Usage in a route:
    @router.get("/protected")
    async def endpoint(user: CurrentActiveUser):
        ...
"""

from typing import Annotated, AsyncGenerator
from uuid import UUID

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    CredentialsException,
    ForbiddenException,
    InactiveUserException,
)
from app.core.security import decode_token
from app.db.session import AsyncSessionLocal
from app.models.user import User

# HTTPBearer extracts the token from "Authorization: Bearer <token>"
# auto_error=False so we can return a custom 401 instead of FastAPI's default
bearer_scheme = HTTPBearer(auto_error=False)


# ─────────────────────────────────────────────────────────────────────────────
#  Database session
# ─────────────────────────────────────────────────────────────────────────────

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Yield an async SQLAlchemy session, guaranteed to be closed after the
    request even if an exception is raised.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


DBSession = Annotated[AsyncSession, Depends(get_db)]


# ─────────────────────────────────────────────────────────────────────────────
#  Token → User resolution
# ─────────────────────────────────────────────────────────────────────────────

async def get_current_user(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Depends(bearer_scheme),
    ],
    db: DBSession,
) -> User:
    """
    Resolve the Bearer token to a User row.

    Validation steps:
      1. Header present
      2. Token decodes without error (valid signature, not expired)
      3. Token type is "access" (prevents refresh token reuse)
      4. Subject (sub) is a valid UUID
      5. User row exists in DB
    """
    if credentials is None:
        raise CredentialsException("No authentication token provided")

    payload = decode_token(credentials.credentials)

    if payload is None:
        raise CredentialsException("Token is invalid or has expired")

    if payload.get("type") != "access":
        raise CredentialsException("Invalid token type — access token required")

    user_id: str | None = payload.get("sub")
    if user_id is None:
        raise CredentialsException("Token payload missing subject")

    try:
        uid = UUID(user_id)
    except ValueError:
        raise CredentialsException("Token subject is not a valid UUID")

    user: User | None = await db.get(User, uid)
    if user is None:
        raise CredentialsException("User belonging to this token no longer exists")

    return user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """Extend get_current_user with an is_active check."""
    if not current_user.is_active:
        raise InactiveUserException()
    return current_user


# ── Convenient type aliases for route signatures ───────────────────────────────
CurrentUser = Annotated[User, Depends(get_current_user)]
CurrentActiveUser = Annotated[User, Depends(get_current_active_user)]


# ─────────────────────────────────────────────────────────────────────────────
#  Role guards
# ─────────────────────────────────────────────────────────────────────────────

def require_role(*roles: str):
    """
    Factory that returns a dependency enforcing one of *roles*.

    Usage:
        @router.get("/admin-only")
        async def admin_endpoint(user: Annotated[User, Depends(require_role("admin"))]):
            ...
    """
    async def _guard(
        current_user: Annotated[User, Depends(get_current_active_user)],
    ) -> User:
        if current_user.role not in roles:
            raise ForbiddenException(
                f"This action requires one of the following roles: {', '.join(roles)}"
            )
        return current_user

    return _guard


# Ready-made role aliases
AdminUser = Annotated[User, Depends(require_role("admin"))]
ModeratorUser = Annotated[User, Depends(require_role("admin", "moderator"))]
