from fastapi import APIRouter, status

from app.core.deps import CurrentUser, DBSession
from app.schemas.common import MessageResponse
from app.schemas.profile import ProfileCreate, ProfileRead, ProfileUpdate
from app.schemas.user import UserRead, UserUpdate
from app.services.profile_service import ProfileService
from app.services.user_service import UserService

router = APIRouter()


# ─── Current user ──────────────────────────────────────────────────────────────

@router.get(
    "/me",
    response_model=UserRead,
    summary="Get current authenticated user",
)
async def get_me(current_user: CurrentUser) -> UserRead:
    """Return the currently authenticated user's account details."""
    return current_user


@router.patch(
    "/me",
    response_model=UserRead,
    summary="Update current user account",
)
async def update_me(
    payload: UserUpdate,
    current_user: CurrentUser,
    db: DBSession,
) -> UserRead:
    """Update email or active status for the current user."""
    return await UserService(db).update(current_user.id, payload)


@router.delete(
    "/me",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Delete current user account",
)
async def delete_me(current_user: CurrentUser, db: DBSession) -> MessageResponse:
    """Permanently delete the authenticated user's account and all associated data."""
    await UserService(db).delete(current_user.id)
    return MessageResponse(message="Account deleted successfully")


# ─── Profile ───────────────────────────────────────────────────────────────────

@router.get(
    "/me/profile",
    response_model=ProfileRead,
    summary="Get current user profile",
)
async def get_profile(current_user: CurrentUser, db: DBSession) -> ProfileRead:
    """Retrieve the health profile for the current user."""
    return await ProfileService(db).get_or_404(current_user.id)


@router.post(
    "/me/profile",
    response_model=ProfileRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create user profile",
)
async def create_profile(
    payload: ProfileCreate,
    current_user: CurrentUser,
    db: DBSession,
) -> ProfileRead:
    """
    Create a health profile for the current user.
    Only one profile per user is allowed.
    """
    return await ProfileService(db).create(current_user.id, payload)


@router.patch(
    "/me/profile",
    response_model=ProfileRead,
    summary="Update user profile",
)
async def update_profile(
    payload: ProfileUpdate,
    current_user: CurrentUser,
    db: DBSession,
) -> ProfileRead:
    """Partially update the current user's health profile."""
    return await ProfileService(db).update(current_user.id, payload)
