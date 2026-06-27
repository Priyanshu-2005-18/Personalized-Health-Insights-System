"""
routers/auth.py
===============
Minimal auth endpoints so the health tracker is self-contained:
  POST /auth/signup  — create account
  POST /auth/login   — get access token
"""

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.core.dependencies import DBSession
from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User
from app.schemas.health_entry import MessageResponse, TokenResponse, UserLogin, UserSignup

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/signup",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new account",
)
async def signup(payload: UserSignup, db: DBSession) -> MessageResponse:
    # Check email uniqueness
    existing = await db.scalar(select(User).where(User.email == payload.email.lower()))
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered")

    # Check username uniqueness
    existing_u = await db.scalar(select(User).where(User.username == payload.username.lower()))
    if existing_u:
        raise HTTPException(status_code=409, detail="Username already taken")

    user = User(
        email=payload.email.lower(),
        username=payload.username.lower(),
        password_hash=hash_password(payload.password),
        full_name=payload.full_name,
    )
    db.add(user)
    await db.commit()
    return MessageResponse(message=f"Account created for {payload.email}")


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login and get access token",
)
async def login(payload: UserLogin, db: DBSession) -> TokenResponse:
    user = await db.scalar(select(User).where(User.email == payload.email.lower()))

    _dummy = "$2b$12$KIXTYFoF1nBbTQE5m9ZcGuxiaBpH7piDkSTK1AHnB1JObJfUCqcXC"
    ok = verify_password(payload.password, user.password_hash if user else _dummy)

    if not user or not ok:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is deactivated")

    token = create_access_token(str(user.id), {"email": user.email})
    return TokenResponse(access_token=token)
