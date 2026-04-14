from typing import Annotated

import asyncpg
from fastapi import APIRouter, Depends, HTTPException, status

from app.auth.dependencies import CurrentUser
from app.db.connection import get_pool
from app.db.users import deactivate_user, update_user_profile
from app.models.user import UserProfileUpdate, UserResponse

router = APIRouter(prefix="/users", tags=["users"])


@router.patch("/me", response_model=UserResponse)
async def update_my_profile(
    body: UserProfileUpdate,
    user: CurrentUser,
    pool: Annotated[asyncpg.Pool, Depends(get_pool)],
) -> UserResponse:
    updated = await update_user_profile(
        pool,
        user["id"],
        display_name=body.display_name,
        contact_phone=body.contact_phone,
        sar_qualifications=body.sar_qualifications,
        preferred_locale=body.preferred_locale,
    )

    if updated is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return UserResponse(
        id=updated["id"],
        email=updated["email"],
        display_name=updated["display_name"],
        contact_phone=updated["contact_phone"],
        sar_qualifications=updated["sar_qualifications"] or [],
        preferred_locale=updated["preferred_locale"],
        is_active=updated["is_active"],
        created_at=updated["created_at"],
    )


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_my_account(
    user: CurrentUser,
    pool: Annotated[asyncpg.Pool, Depends(get_pool)],
) -> None:
    await deactivate_user(pool, user["id"])
