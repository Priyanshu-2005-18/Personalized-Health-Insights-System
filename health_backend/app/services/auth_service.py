import hashlib
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestException, ConflictException, UnauthorizedException
from app.core.security import (
    create_access_token, create_refresh_token,
    decode_token, hash_password, verify_password,
)
from app.models.user import RefreshToken, User
from app.models.profile import UserProfile
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse


class AuthService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ─── Register ──────────────────────────────────────────────────────────────

    async def register(self, payload: RegisterRequest) -> TokenResponse:
        existing = await self.db.scalar(
            select(User).where(User.email == payload.email.lower())
        )
        if existing:
            raise ConflictException("An account with this email already exists")

        user = User(
            email=payload.email.lower(),
            password_hash=hash_password(payload.password),
        )
        self.db.add(user)
        await self.db.flush()

        profile = UserProfile(
            user_id=user.id,
            first_name=payload.first_name,
            last_name=payload.last_name,
        )
        self.db.add(profile)
        await self.db.commit()
        await self.db.refresh(user)

        return await self._issue_tokens(user)

    # ─── Login ─────────────────────────────────────────────────────────────────

    async def login(self, payload: LoginRequest) -> TokenResponse:
        user = await self.db.scalar(
            select(User).where(User.email == payload.email.lower())
        )
        if not user or not verify_password(payload.password, user.password_hash):
            raise UnauthorizedException("Incorrect email or password")

        if not user.is_active:
            raise BadRequestException("Account is deactivated")

        await self.db.execute(
            update(User)
            .where(User.id == user.id)
            .values(last_login_at=datetime.now(timezone.utc))
        )
        await self.db.commit()

        return await self._issue_tokens(user)

    # ─── Refresh ───────────────────────────────────────────────────────────────

    async def refresh(self, token: str) -> TokenResponse:
        payload = decode_token(token)
        if payload is None or payload.get("type") != "refresh":
            raise UnauthorizedException("Invalid refresh token")

        token_hash = self._hash_token(token)
        stored = await self.db.scalar(
            select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        )
        if not stored or stored.is_revoked:
            raise UnauthorizedException("Refresh token is revoked or not found")

        if stored.expires_at < datetime.now(timezone.utc).replace(tzinfo=None):
            raise UnauthorizedException("Refresh token has expired")

        # Rotate — revoke old, issue new
        stored.is_revoked = True
        await self.db.flush()

        user = await self.db.get(User, stored.user_id)
        if not user or not user.is_active:
            raise UnauthorizedException("User not found or deactivated")

        tokens = await self._issue_tokens(user)
        await self.db.commit()
        return tokens

    # ─── Logout ────────────────────────────────────────────────────────────────

    async def logout(self, token: str) -> None:
        token_hash = self._hash_token(token)
        stored = await self.db.scalar(
            select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        )
        if stored:
            stored.is_revoked = True
            await self.db.commit()

    # ─── Helpers ───────────────────────────────────────────────────────────────

    async def _issue_tokens(self, user: User) -> TokenResponse:
        from datetime import timedelta
        from app.core.config import settings

        access_token = create_access_token(str(user.id), {"role": user.role.value})
        refresh_token = create_refresh_token(str(user.id))

        expires_at = datetime.now(timezone.utc) + timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )
        db_token = RefreshToken(
            user_id=user.id,
            token_hash=self._hash_token(refresh_token),
            expires_at=expires_at,
        )
        self.db.add(db_token)
        await self.db.flush()

        return TokenResponse(access_token=access_token, refresh_token=refresh_token)

    @staticmethod
    def _hash_token(token: str) -> str:
        return hashlib.sha256(token.encode()).hexdigest()
