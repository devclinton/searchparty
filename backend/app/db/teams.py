from datetime import datetime
from uuid import UUID

import asyncpg


async def create_team(
    pool: asyncpg.Pool,
    *,
    incident_id: UUID,
    name: str,
    search_type: str | None = None,
    check_in_interval_minutes: int = 30,
) -> asyncpg.Record:
    return await pool.fetchrow(
        """
        INSERT INTO teams (incident_id, name, search_type, check_in_interval_minutes)
        VALUES ($1, $2, $3, $4)
        RETURNING *
        """,
        incident_id,
        name,
        search_type,
        check_in_interval_minutes,
    )


async def get_team_by_id(pool: asyncpg.Pool, team_id: UUID) -> asyncpg.Record | None:
    return await pool.fetchrow("SELECT * FROM teams WHERE id = $1", team_id)


async def list_teams_by_incident(pool: asyncpg.Pool, incident_id: UUID) -> list[asyncpg.Record]:
    return await pool.fetch(
        "SELECT * FROM teams WHERE incident_id = $1 ORDER BY created_at",
        incident_id,
    )


async def update_team_status(
    pool: asyncpg.Pool,
    team_id: UUID,
    status: str,
) -> asyncpg.Record | None:
    extra = ""
    if status == "deployed":
        extra = ", deployed_at = NOW()"
    return await pool.fetchrow(
        f"UPDATE teams SET status = $1, updated_at = NOW(){extra} "  # noqa: S608
        "WHERE id = $2 RETURNING *",
        status,
        team_id,
    )


async def update_team(
    pool: asyncpg.Pool,
    team_id: UUID,
    **fields: object,
) -> asyncpg.Record | None:
    updates = []
    params: list = [team_id]
    idx = 2

    for key, value in fields.items():
        if value is not None:
            updates.append(f"{key} = ${idx}")
            params.append(value)
            idx += 1

    if not updates:
        return await get_team_by_id(pool, team_id)

    updates.append("updated_at = NOW()")
    set_clause = ", ".join(updates)

    return await pool.fetchrow(
        f"UPDATE teams SET {set_clause} WHERE id = $1 RETURNING *",  # noqa: S608
        *params,
    )


async def dispatch_assignment(
    pool: asyncpg.Pool,
    team_id: UUID,
    *,
    search_type: str | None = None,
    turnaround_time: datetime | None = None,
) -> asyncpg.Record | None:
    updates = ["status = 'deployed'", "deployed_at = NOW()", "updated_at = NOW()"]
    params: list = [team_id]
    idx = 2

    if search_type is not None:
        updates.append(f"search_type = ${idx}")
        params.append(search_type)
        idx += 1
    if turnaround_time is not None:
        updates.append(f"turnaround_time = ${idx}")
        params.append(turnaround_time)
        idx += 1

    set_clause = ", ".join(updates)
    return await pool.fetchrow(
        f"UPDATE teams SET {set_clause} WHERE id = $1 RETURNING *",  # noqa: S608
        *params,
    )


# Team members


async def add_team_member(
    pool: asyncpg.Pool,
    *,
    team_id: UUID,
    user_id: UUID,
    role: str = "searcher",
) -> asyncpg.Record:
    return await pool.fetchrow(
        """
        INSERT INTO team_members (team_id, user_id, role)
        VALUES ($1, $2, $3)
        ON CONFLICT (team_id, user_id) DO UPDATE SET
            role = EXCLUDED.role,
            signed_in_at = NOW(),
            signed_out_at = NULL
        RETURNING *
        """,
        team_id,
        user_id,
        role,
    )


async def remove_team_member(
    pool: asyncpg.Pool,
    team_id: UUID,
    user_id: UUID,
) -> bool:
    result = await pool.execute(
        """
        UPDATE team_members SET signed_out_at = NOW()
        WHERE team_id = $1 AND user_id = $2 AND signed_out_at IS NULL
        """,
        team_id,
        user_id,
    )
    return result == "UPDATE 1"


async def list_team_members(pool: asyncpg.Pool, team_id: UUID) -> list[asyncpg.Record]:
    return await pool.fetch(
        """
        SELECT tm.*, u.display_name, u.email
        FROM team_members tm
        JOIN users u ON tm.user_id = u.id
        WHERE tm.team_id = $1 AND tm.signed_out_at IS NULL
        ORDER BY
            CASE tm.role
                WHEN 'incident_commander' THEN 0
                WHEN 'operations_chief' THEN 1
                WHEN 'safety_officer' THEN 2
                WHEN 'division_supervisor' THEN 3
                WHEN 'team_leader' THEN 4
                WHEN 'searcher' THEN 5
            END
        """,
        team_id,
    )


# Check-ins


async def record_check_in(pool: asyncpg.Pool, team_id: UUID) -> asyncpg.Record | None:
    return await pool.fetchrow(
        """
        UPDATE teams SET last_check_in_at = NOW(), updated_at = NOW()
        WHERE id = $1
        RETURNING *
        """,
        team_id,
    )


async def get_overdue_teams(pool: asyncpg.Pool, incident_id: UUID) -> list[asyncpg.Record]:
    return await pool.fetch(
        """
        SELECT * FROM teams
        WHERE incident_id = $1
        AND status = 'deployed'
        AND last_check_in_at IS NOT NULL
        AND last_check_in_at + (check_in_interval_minutes || ' minutes')::interval
            < NOW()
        """,
        incident_id,
    )


# Accountability board


async def get_accountability_board(pool: asyncpg.Pool, incident_id: UUID) -> list[asyncpg.Record]:
    return await pool.fetch(
        """
        SELECT
            tm.user_id,
            u.display_name,
            t.name as team_name,
            tm.role,
            tm.signed_in_at,
            tm.signed_out_at
        FROM team_members tm
        JOIN users u ON tm.user_id = u.id
        JOIN teams t ON tm.team_id = t.id
        WHERE t.incident_id = $1
        ORDER BY tm.signed_out_at NULLS FIRST, tm.signed_in_at DESC
        """,
        incident_id,
    )
