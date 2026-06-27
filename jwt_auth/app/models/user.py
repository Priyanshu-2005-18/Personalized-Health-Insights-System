"""
models/user.py
==============
Two tables:

  users
  ─────
  Central identity table. Only authentication columns live here.
  Profile data (name, avatar, etc.) belongs in a separate table (2NF).

  refresh_tokens
  ──────────────
  Stores HASHED refresh tokens so that even a DB breach cannot be
  used to forge tokens. One user can have multiple active tokens
  (multiple devices) but each is revoked independently.

Relationships:
  User 1 ──< RefreshToken  (one-to-many, cascade delete)
"""

import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin


class User(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "users"

    # ── Identity ──────────────────────────────────────────────────────────────
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
        comment="Normalised to lowercase before storage",
    )
    username: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
    )

    # ── Credentials ───────────────────────────────────────────────────────────
    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="bcrypt hash — NEVER store plain text",
    )

    # ── Profile ───────────────────────────────────────────────────────────────
    full_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)

    # ── Authorisation ─────────────────────────────────────────────────────────
    role: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="user",
        comment="user | admin | moderator",
    )

    # ── Status ────────────────────────────────────────────────────────────────
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        comment="Soft-delete / account suspension flag",
    )
    is_verified: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="Email verification flag",
    )
    last_login_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # ── Relationships ─────────────────────────────────────────────────────────
    refresh_tokens: Mapped[List["RefreshToken"]] = relationship(
        "RefreshToken",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="select",
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email} role={self.role}>"


class RefreshToken(Base, UUIDMixin):
    __tablename__ = "refresh_tokens"

    # ── Owner ─────────────────────────────────────────────────────────────────
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # ── Token data ────────────────────────────────────────────────────────────
    token_hash: Mapped[str] = mapped_column(
        String(64),           # SHA-256 hex digest is always 64 chars
        unique=True,
        nullable=False,
        index=True,
        comment="SHA-256 hash of the raw JWT refresh token",
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )

    # ── State ─────────────────────────────────────────────────────────────────
    is_revoked: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="Set to True on logout or rotation",
    )

    # ── Audit ─────────────────────────────────────────────────────────────────
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # ── Relationships ─────────────────────────────────────────────────────────
    user: Mapped["User"] = relationship("User", back_populates="refresh_tokens")

    def __repr__(self) -> str:
        return (
            f"<RefreshToken id={self.id} "
            f"user_id={self.user_id} "
            f"revoked={self.is_revoked}>"
        )
