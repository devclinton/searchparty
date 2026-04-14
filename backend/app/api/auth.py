from typing import Annotated

import asyncpg
from fastapi import APIRouter, Depends, HTTPException, status

from app.auth.dependencies import CurrentUser
from app.auth.jwt import (
    create_access_token,
    create_refresh_token,
    verify_refresh_token,
)
from app.auth.password import hash_password, verify_password
from app.auth.rate_limit import auth_rate_limiter, rate_limit, register_rate_limiter
from app.db.connection import get_pool
from app.db.users import create_user, get_user_by_email, get_user_by_id
from app.models.user import (
    TokenPair,
    TokenRefresh,
    UserCreate,
    UserLogin,
    UserResponse,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(rate_limit(register_rate_limiter))],
)
async def register(
    body: UserCreate,
    pool: Annotated[asyncpg.Pool, Depends(get_pool)],
) -> UserResponse:
    existing = await get_user_by_email(pool, body.email)
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    if len(body.password) < 8:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Password must be at least 8 characters",
        )

    hashed = hash_password(body.password)
    user = await create_user(
        pool,
        email=body.email,
        display_name=body.display_name,
        password_hash=hashed,
        preferred_locale=body.preferred_locale,
    )

    return UserResponse(
        id=user["id"],
        email=user["email"],
        display_name=user["display_name"],
        contact_phone=user["contact_phone"],
        sar_qualifications=user["sar_qualifications"] or [],
        preferred_locale=user["preferred_locale"],
        is_active=user["is_active"],
        created_at=user["created_at"],
    )


@router.post(
    "/login",
    response_model=TokenPair,
    dependencies=[Depends(rate_limit(auth_rate_limiter))],
)
async def login(
    body: UserLogin,
    pool: Annotated[asyncpg.Pool, Depends(get_pool)],
) -> TokenPair:
    user = await get_user_by_email(pool, body.email)
    if user is None or user["password_hash"] is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    if not verify_password(body.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    return TokenPair(
        access_token=create_access_token(user["id"]),
        refresh_token=create_refresh_token(user["id"]),
    )


@router.post(
    "/refresh",
    response_model=TokenPair,
    dependencies=[Depends(rate_limit(auth_rate_limiter))],
)
async def refresh_token(
    body: TokenRefresh,
    pool: Annotated[asyncpg.Pool, Depends(get_pool)],
) -> TokenPair:
    try:
        user_id = verify_refresh_token(body.refresh_token)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        ) from e

    user = await get_user_by_id(pool, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    return TokenPair(
        access_token=create_access_token(user["id"]),
        refresh_token=create_refresh_token(user["id"]),
    )


@router.get("/me", response_model=UserResponse)
async def get_me(user: CurrentUser) -> UserResponse:
    return UserResponse(
        id=user["id"],
        email=user["email"],
        display_name=user["display_name"],
        contact_phone=user["contact_phone"],
        sar_qualifications=user["sar_qualifications"] or [],
        preferred_locale=user["preferred_locale"],
        is_active=user["is_active"],
        created_at=user["created_at"],
    )
