"""
services/auth_service.py
========================
All auth business logic lives here — routes stay thin, service stays testable.

Operations:
  signup          — validate uniqueness, hash password, create user + profile, issue tokens
  login           — verify credentials, update last_login_at, issue tokens
  refresh         — validate + rotate refresh token, issue new pair
  logout          — revoke refresh token
  change_password — re-authenticate, update hash, revoke all refresh tokens
  _issue_tokens   — internal: create access + refresh token pair, persist hash

Security practices applied:
  - Emails normalised to lowercase before DB write
  - Passwords hashed with bcrypt (rounds=12) before storage
  - Refresh tokens stored as SHA-256 hashes — never plaintext
  - Refresh tokens rotated on every use (old one revoked immediately)
  - last_login_at updated on every successful login for audit trail
  - All existing refresh tokens revoked after password change
  - Timing-safe password compare via passlib
  - Generic error messages on login failure (prevent user enumeration)
"""

from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

from fastapi import Request
from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import (
    CredentialsException,
    EmailAlreadyExistsException,
    InvalidCredentialsException,
    TokenRevokedException,
    UserNotFoundException,
)
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    hash_token,
    verify_password,
)
from app.models.user import RefreshToken, User
from app.schemas.auth import (
    ChangePasswordRequest,
    LoginRequest,
    MessageResponse,
    SignupRequest,
    SignupResponse,
    TokenResponse,
)


class AuthService:
    """
    Encapsulates all authentication operations.
    Instantiated per-request with the current DB session.
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ─────────────────────────────────────────────────────────────────────────
    #  Signup
    # ─────────────────────────────────────────────────────────────────────────

    async def signup(self, payload: SignupRequest, request: Request) -> SignupResponse:
        """
        Register a new user.

        Steps:
          1. Check email uniqueness
          2. Check username uniqueness
          3. Hash password
          4. Persist User row
          5. Issue token pair
          6. Return SignupResponse (user data + tokens)
        """
        # ── 1. Email uniqueness ───────────────────────────────────────────────
        existing_email = await self.db.scalar(
            select(User).where(User.email == payload.email)
        )
        if existing_email:
            raise EmailAlreadyExistsException()

        # ── 2. Username uniqueness ────────────────────────────────────────────
        existing_username = await self.db.scalar(
            select(User).where(User.username == payload.username.lower())
        )
        if existing_username:
            from app.core.exceptions import ForbiddenException
            from fastapi import HTTPException, status
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="This username is already taken",
            )

        # ── 3. Hash password ──────────────────────────────────────────────────
        pw_hash = hash_password(payload.password)

        # ── 4. Create user ────────────────────────────────────────────────────
        user = User(
            email=payload.email,                      # already lowercased by schema
            username=payload.username.lower(),
            password_hash=pw_hash,
            full_name=payload.full_name,
            role="user",
            is_active=True,
            is_verified=False,
        )
        self.db.add(user)
        await self.db.flush()        # populate user.id without committing

        # ── 5. Issue tokens ───────────────────────────────────────────────────
        access_token, refresh_token = await self._issue_tokens(user, request)
        await self.db.commit()
        await self.db.refresh(user)

        # ── 6. Build response ─────────────────────────────────────────────────
        return SignupResponse(
            id=user.id,
            email=user.email,
            username=user.username,
            full_name=user.full_name,
            role=user.role,
            is_active=user.is_active,
            is_verified=user.is_verified,
            created_at=user.created_at,
            access_token=access_token,
            refresh_token=refresh_token,
        )

    # ─────────────────────────────────────────────────────────────────────────
    #  Login
    # ─────────────────────────────────────────────────────────────────────────

    async def login(self, payload: LoginRequest, request: Request) -> TokenResponse:
        """
        Authenticate with email + password.

        Uses a generic error message for both "user not found" and "wrong password"
        to prevent user enumeration attacks.
        """
        # Fetch user — intentionally no early return on missing user
        # (we always call verify_password to keep timing consistent)
        user: Optional[User] = await self.db.scalar(
            select(User).where(User.email == payload.email)
        )

        # verify_password runs even when user is None (against a dummy hash)
        # to prevent timing-based user enumeration
        _dummy_hash = "$2b$12$KIXTYFoF1nBbTQE5m9ZcGuxiaBpH7piDkSTK1AHnB1JObJfUCqcXC"
        password_ok = verify_password(
            payload.password,
            user.password_hash if user else _dummy_hash,
        )

        if not user or not password_ok:
            raise InvalidCredentialsException()

        if not user.is_active:
            # Separate message only shown after password verified to avoid leaking info
            from fastapi import HTTPException, status
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is deactivated. Contact support.",
            )

        # Update last login timestamp
        await self.db.execute(
            update(User)
            .where(User.id == user.id)
            .values(last_login_at=datetime.now(timezone.utc))
        )

        access_token, refresh_token = await self._issue_tokens(user, request)
        await self.db.commit()

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
        )

    # ─────────────────────────────────────────────────────────────────────────
    #  Token refresh
    # ─────────────────────────────────────────────────────────────────────────

    async def refresh(self, raw_refresh_token: str) -> TokenResponse:
        """
        Rotate a refresh token.

        Steps:
          1. Decode JWT (expiry + signature)
          2. Verify token type is "refresh"
          3. Look up hashed token in DB
          4. Check not revoked
          5. Revoke old token
          6. Issue new pair
        """
        # ── 1 & 2. Decode + type check ────────────────────────────────────────
        payload = decode_token(raw_refresh_token)
        if payload is None or payload.get("type") != "refresh":
            raise CredentialsException("Invalid or expired refresh token")

        # ── 3. Lookup in DB ───────────────────────────────────────────────────
        token_hash = hash_token(raw_refresh_token)
        stored: Optional[RefreshToken] = await self.db.scalar(
            select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        )

        if stored is None:
            raise CredentialsException("Refresh token not found")

        # ── 4. Check not revoked ──────────────────────────────────────────────
        if stored.is_revoked:
            # Token reuse detected — this could mean theft.
            # Revoke ALL tokens for this user as a precaution.
            await self._revoke_all_user_tokens(stored.user_id)
            await self.db.commit()
            raise TokenRevokedException()

        if stored.expires_at < datetime.now(timezone.utc):
            raise CredentialsException("Refresh token has expired")

        # ── 5. Revoke old token ───────────────────────────────────────────────
        stored.is_revoked = True
        await self.db.flush()

        # ── 6. Issue new pair ─────────────────────────────────────────────────
        user: Optional[User] = await self.db.get(User, stored.user_id)
        if user is None or not user.is_active:
            raise CredentialsException("User not found or deactivated")

        access_token, refresh_token = await self._issue_tokens(user, request=None)
        await self.db.commit()

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
        )

    # ─────────────────────────────────────────────────────────────────────────
    #  Logout
    # ─────────────────────────────────────────────────────────────────────────

    async def logout(self, raw_refresh_token: str) -> MessageResponse:
        """
        Revoke a refresh token.
        Silently succeeds even if the token is already revoked or unknown
        (idempotent — clients may call logout multiple times).
        """
        token_hash = hash_token(raw_refresh_token)
        stored: Optional[RefreshToken] = await self.db.scalar(
            select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        )
        if stored and not stored.is_revoked:
            stored.is_revoked = True
            await self.db.commit()

        return MessageResponse(message="Successfully logged out")

    # ─────────────────────────────────────────────────────────────────────────
    #  Change password
    # ─────────────────────────────────────────────────────────────────────────

    async def change_password(
        self,
        user: User,
        payload: ChangePasswordRequest,
    ) -> MessageResponse:
        """
        Change the current user's password.

        Requires the current password for re-authentication.
        Revokes ALL existing refresh tokens on success so all other
        sessions are terminated — forces re-login everywhere.
        """
        # Re-authenticate
        if not verify_password(payload.current_password, user.password_hash):
            raise InvalidCredentialsException()

        if payload.current_password == payload.new_password:
            from fastapi import HTTPException, status
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="New password must differ from the current password",
            )

        # Update hash
        await self.db.execute(
            update(User)
            .where(User.id == user.id)
            .values(password_hash=hash_password(payload.new_password))
        )

        # Revoke all refresh tokens — force re-login on all devices
        await self._revoke_all_user_tokens(user.id)
        await self.db.commit()

        return MessageResponse(
            message="Password updated successfully. Please log in again on all devices."
        )

    # ─────────────────────────────────────────────────────────────────────────
    #  Internal helpers
    # ─────────────────────────────────────────────────────────────────────────

    async def _issue_tokens(
        self,
        user: User,
        request: Optional[Request],
    ) -> tuple[str, str]:
        """
        Create an access + refresh token pair and persist the refresh token hash.

        Returns:
            (raw_access_token, raw_refresh_token)
        """
        # Access token carries role for fast authorisation checks
        access_token = create_access_token(
            subject=str(user.id),
            extra_claims={"role": user.role, "email": user.email},
        )
        refresh_token = create_refresh_token(subject=str(user.id))

        # Persist hashed refresh token
        expires_at = datetime.now(timezone.utc) + timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )
        db_token = RefreshToken(
            user_id=user.id,
            token_hash=hash_token(refresh_token),
            expires_at=expires_at,
            ip_address=_get_client_ip(request),
            user_agent=_get_user_agent(request),
        )
        self.db.add(db_token)
        # Caller must flush/commit

        return access_token, refresh_token

    async def _revoke_all_user_tokens(self, user_id: UUID) -> None:
        """Mark every refresh token for *user_id* as revoked."""
        await self.db.execute(
            update(RefreshToken)
            .where(RefreshToken.user_id == user_id, RefreshToken.is_revoked == False)  # noqa: E712
            .values(is_revoked=True)
        )


# ─────────────────────────────────────────────────────────────────────────────
#  Request metadata helpers
# ─────────────────────────────────────────────────────────────────────────────

def _get_client_ip(request: Optional[Request]) -> Optional[str]:
    if request is None:
        return None
    # Respect X-Forwarded-For when behind a proxy / load balancer
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    if request.client:
        return request.client.host
    return None


def _get_user_agent(request: Optional[Request]) -> Optional[str]:
    if request is None:
        return None
    return request.headers.get("User-Agent")
