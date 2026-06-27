"""
routers/protected.py
====================
Example routes showing every level of access control:

  GET /protected/user-only      — any authenticated active user
  GET /protected/admin-only     — role == "admin"
  GET /protected/moderator-plus — role in ("admin", "moderator")
  GET /protected/profile        — returns full user object
  GET /protected/token-claims   — shows what's inside the decoded token
"""

from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.dependencies import (
    AdminUser,
    CurrentActiveUser,
    ModeratorUser,
    require_role,
)
from app.core.security import decode_token
from app.models.user import User
from app.schemas.auth import MessageResponse, UserResponse

router = APIRouter(prefix="/protected", tags=["Protected Routes"])

bearer = HTTPBearer(auto_error=False)


# ─────────────────────────────────────────────────────────────────────────────
#  Open to any authenticated active user
# ─────────────────────────────────────────────────────────────────────────────

@router.get(
    "/user-only",
    response_model=MessageResponse,
    summary="Authenticated users only",
)
async def user_only(current_user: CurrentActiveUser) -> MessageResponse:
    return MessageResponse(
        message=f"Hello {current_user.username}! "
                f"You are authenticated as role='{current_user.role}'."
    )


@router.get(
    "/profile",
    response_model=UserResponse,
    summary="Return full user profile",
)
async def get_profile(current_user: CurrentActiveUser) -> UserResponse:
    return current_user  # type: ignore[return-value]


@router.get(
    "/token-claims",
    summary="Inspect decoded token payload",
    description="Returns the claims inside your access token — useful for debugging.",
)
async def token_claims(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> dict:
    if credentials is None:
        return {"error": "No token provided"}
    payload = decode_token(credentials.credentials)
    if payload is None:
        return {"error": "Invalid or expired token"}
    # Remove exp/iat to keep response clean; in prod you'd keep them
    return {k: v for k, v in payload.items() if k not in ("exp", "iat")}


# ─────────────────────────────────────────────────────────────────────────────
#  Admin-only
# ─────────────────────────────────────────────────────────────────────────────

@router.get(
    "/admin-only",
    response_model=MessageResponse,
    summary="Admin role required",
    description="Only users with `role='admin'` can access this endpoint.",
)
async def admin_only(admin: AdminUser) -> MessageResponse:
    return MessageResponse(
        message=f"Welcome admin {admin.username}! You have full access."
    )


# ─────────────────────────────────────────────────────────────────────────────
#  Moderator or Admin
# ─────────────────────────────────────────────────────────────────────────────

@router.get(
    "/moderator-plus",
    response_model=MessageResponse,
    summary="Moderator or Admin role required",
)
async def moderator_plus(mod: ModeratorUser) -> MessageResponse:
    return MessageResponse(
        message=f"Hello {mod.username}! You have moderator-level access (role={mod.role})."
    )


# ─────────────────────────────────────────────────────────────────────────────
#  Dynamic role check example
# ─────────────────────────────────────────────────────────────────────────────

@router.get(
    "/clinician-only",
    response_model=MessageResponse,
    summary="Clinician role required (dynamic require_role example)",
)
async def clinician_only(
    user: Annotated[User, Depends(require_role("clinician", "admin"))],
) -> MessageResponse:
    return MessageResponse(
        message=f"Hello Dr. {user.username}! You have clinician-level access."
    )
