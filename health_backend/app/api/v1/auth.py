from fastapi import APIRouter, Request, status

from app.core.deps import DBSession
from app.schemas.auth import (
    LoginRequest,
    LogoutRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
)
from app.schemas.common import MessageResponse
from app.services.auth_service import AuthService

router = APIRouter()


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user account",
)
async def register(payload: RegisterRequest, db: DBSession) -> TokenResponse:
    """
    Create a new user account and return access + refresh tokens.
    A minimal profile (first_name, last_name) is created automatically.
    """
    return await AuthService(db).register(payload)


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login with email and password",
)
async def login(payload: LoginRequest, db: DBSession) -> TokenResponse:
    """
    Authenticate with email/password. Returns a short-lived access token
    (15 min) and a long-lived refresh token (7 days).
    """
    return await AuthService(db).login(payload)


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Rotate refresh token and get new access token",
)
async def refresh(payload: RefreshRequest, db: DBSession) -> TokenResponse:
    """
    Exchange a valid refresh token for a new access token + refresh token pair.
    The old refresh token is immediately revoked (rotation strategy).
    """
    return await AuthService(db).refresh(payload.refresh_token)


@router.post(
    "/logout",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Logout and revoke refresh token",
)
async def logout(payload: LogoutRequest, db: DBSession) -> MessageResponse:
    """
    Revoke the supplied refresh token so it can no longer be used.
    The client should also discard the access token locally.
    """
    await AuthService(db).logout(payload.refresh_token)
    return MessageResponse(message="Logged out successfully")
