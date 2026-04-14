from typing import Annotated

import asyncpg
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.auth.jwt import create_access_token, create_refresh_token
from app.auth.oauth import OAuthError, verify_oauth_token
from app.db.connection import get_pool
from app.db.users import create_user, get_user_by_oauth
from app.models.user import TokenPair

router = APIRouter(prefix="/auth/oauth", tags=["auth"])


class OAuthRequest(BaseModel):
    provider: str
    token: str


@router.post("/login", response_model=TokenPair)
async def oauth_login(
    body: OAuthRequest,
    pool: Annotated[asyncpg.Pool, Depends(get_pool)],
) -> TokenPair:
    try:
        user_info = await verify_oauth_token(body.provider, body.token)
    except OAuthError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        ) from e

    # Check if user already exists with this OAuth identity
    user = await get_user_by_oauth(pool, user_info["provider"], user_info["oauth_id"])

    if user is None:
        # Auto-register new OAuth user
        user = await create_user(
            pool,
            email=user_info["email"],
            display_name=user_info["display_name"],
            oauth_provider=user_info["provider"],
            oauth_id=user_info["oauth_id"],
        )

    return TokenPair(
        access_token=create_access_token(user["id"]),
        refresh_token=create_refresh_token(user["id"]),
    )
