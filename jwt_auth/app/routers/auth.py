"""
routers/auth.py
===============
All authentication endpoints:

  POST /auth/signup          – create account, returns token pair
  POST /auth/login           – verify credentials, returns token pair
  POST /auth/refresh         – rotate refresh token, returns new pair
  POST /auth/logout          – revoke refresh token
  POST /auth/change-password – update password (protected)
  GET  /auth/me              – current user info (protected)
  GET  /auth/verify-token    – validate an access token (protected)
"""

from fastapi import APIRouter, Request, status

from app.core.dependencies import CurrentActiveUser, DBSession
from app.schemas.auth import (
    ChangePasswordRequest,
    LoginRequest,
    LogoutRequest,
    MessageResponse,
    RefreshRequest,
    SignupRequest,
    SignupResponse,
    TokenResponse,
    UserResponse,
)
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])


# ─────────────────────────────────────────────────────────────────────────────
#  Public endpoints (no token required)
# ─────────────────────────────────────────────────────────────────────────────

@router.post(
    "/signup",
    response_model=SignupResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new account",
    description="""
Create a new user account.

**Password requirements:**
- 8–128 characters
- At least one uppercase letter
- At least one lowercase letter
- At least one digit
- At least one special character (`@$!%*?&_-#^`)

On success, a token pair is returned immediately — no separate login step needed.
""",
)
async def signup(
    payload: SignupRequest,
    request: Request,
    db: DBSession,
) -> SignupResponse:
    return await AuthService(db).signup(payload, request)


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login with email and password",
    description="""
Authenticate with email and password.

Returns:
- **access_token** — short-lived (15 min), include in `Authorization: Bearer` header
- **refresh_token** — long-lived (7 days), use to obtain new access tokens
""",
)
async def login(
    payload: LoginRequest,
    request: Request,
    db: DBSession,
) -> TokenResponse:
    return await AuthService(db).login(payload, request)


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Rotate refresh token",
    description="""
Exchange a valid refresh token for a **new access + refresh token pair**.

The supplied refresh token is **immediately revoked** on use (rotation strategy).
If a previously-used refresh token is presented, it indicates possible theft and
should be treated as a security incident — all user tokens can be revoked.
""",
)
async def refresh_tokens(
    payload: RefreshRequest,
    db: DBSession,
) -> TokenResponse:
    return await AuthService(db).refresh(payload.refresh_token)


@router.post(
    "/logout",
    response_model=MessageResponse,
    summary="Logout and revoke refresh token",
    description="""
Revoke the supplied refresh token.

The client should also discard the access token locally (e.g. from memory / cookies).
Access tokens cannot be server-side revoked — they expire naturally after 15 minutes.
""",
)
async def logout(
    payload: LogoutRequest,
    db: DBSession,
) -> MessageResponse:
    return await AuthService(db).logout(payload.refresh_token)


# ─────────────────────────────────────────────────────────────────────────────
#  Protected endpoints (valid access token required)
# ─────────────────────────────────────────────────────────────────────────────

@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user",
    description="Return the profile of the currently authenticated user.",
)
async def get_me(current_user: CurrentActiveUser) -> UserResponse:
    return current_user  # type: ignore[return-value]


@router.get(
    "/verify-token",
    response_model=MessageResponse,
    summary="Verify access token",
    description="""
A lightweight endpoint that simply validates the Bearer token.
Useful for frontend guards and health checks.
Returns 200 if the token is valid, 401 otherwise.
""",
)
async def verify_token(current_user: CurrentActiveUser) -> MessageResponse:
    return MessageResponse(
        message=f"Token is valid. Authenticated as {current_user.email}"
    )


@router.post(
    "/change-password",
    response_model=MessageResponse,
    summary="Change password",
    description="""
Update the current user's password.

**Requires:**
- Valid access token
- Correct current password (re-authentication)
- New password that meets strength requirements
- All existing refresh tokens are revoked after a successful change
  so other sessions are terminated.
""",
)
async def change_password(
    payload: ChangePasswordRequest,
    current_user: CurrentActiveUser,
    db: DBSession,
) -> MessageResponse:
    return await AuthService(db).change_password(current_user, payload)
