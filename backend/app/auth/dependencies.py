from collections.abc import Callable
from typing import Annotated

import asyncpg
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.auth.jwt import verify_access_token
from app.db.connection import get_pool
from app.db.users import get_user_by_id
from app.models.user import ICS_ROLE_HIERARCHY, ICSRole

_bearer_scheme = HTTPBearer()


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(_bearer_scheme)],
    pool: Annotated[asyncpg.Pool, Depends(get_pool)],
) -> asyncpg.Record:
    try:
        user_id = verify_access_token(credentials.credentials)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        ) from e

    user = await get_user_by_id(pool, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )
    return user


CurrentUser = Annotated[asyncpg.Record, Depends(get_current_user)]


def require_role(minimum_role: ICSRole) -> Callable:
    """Dependency factory that checks the user has at least the given ICS role
    in the context of a specific incident. For global endpoints (not incident-scoped),
    this checks the user exists and is active."""

    min_level = ICS_ROLE_HIERARCHY[minimum_role]

    async def _check_role(
        user: CurrentUser,
        pool: Annotated[asyncpg.Pool, Depends(get_pool)],
        incident_id: str | None = None,
    ) -> asyncpg.Record:
        if incident_id is None:
            # Non-incident-scoped endpoint — just require authenticated user
            return user

        # Check user's role in this incident via team_members
        row = await pool.fetchrow(
            """
            SELECT tm.role FROM team_members tm
            JOIN teams t ON tm.team_id = t.id
            WHERE tm.user_id = $1 AND t.incident_id = $2 AND tm.signed_out_at IS NULL
            ORDER BY
                CASE tm.role
                    WHEN 'incident_commander' THEN 4
                    WHEN 'operations_chief' THEN 3
                    WHEN 'division_supervisor' THEN 2
                    WHEN 'safety_officer' THEN 2
                    WHEN 'team_leader' THEN 1
                    WHEN 'searcher' THEN 0
                END DESC
            LIMIT 1
            """,
            user["id"],
            incident_id,
        )

        # Also check if user is the incident commander directly
        ic_row = await pool.fetchrow(
            "SELECT incident_commander_id FROM incidents WHERE id = $1",
            incident_id,
        )
        if ic_row and ic_row["incident_commander_id"] == user["id"]:
            return user

        if row is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not a member of this incident",
            )

        user_role = ICSRole(row["role"])
        user_level = ICS_ROLE_HIERARCHY[user_role]

        if user_level < min_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires {minimum_role.value} role or higher",
            )

        return user

    return _check_role
