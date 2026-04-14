from uuid import UUID

import asyncpg


async def create_incident(
    pool: asyncpg.Pool,
    *,
    name: str,
    incident_commander_id: UUID,
    description: str | None = None,
    subject_name: str | None = None,
    subject_age_category: str | None = None,
    subject_activity: str | None = None,
    subject_condition: str | None = None,
    subject_clothing: str | None = None,
    subject_medical_needs: str | None = None,
    ipp_lat: float | None = None,
    ipp_lon: float | None = None,
    terrain_type: str | None = None,
    data_retention_days: int = 90,
) -> asyncpg.Record:
    return await pool.fetchrow(
        """
        INSERT INTO incidents (
            name, description, incident_commander_id,
            subject_name, subject_age_category, subject_activity,
            subject_condition, subject_clothing, subject_medical_needs,
            ipp_lat, ipp_lon, terrain_type, data_retention_days
        )
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
        RETURNING *
        """,
        name,
        description,
        incident_commander_id,
        subject_name,
        subject_age_category,
        subject_activity,
        subject_condition,
        subject_clothing,
        subject_medical_needs,
        ipp_lat,
        ipp_lon,
        terrain_type,
        data_retention_days,
    )


async def get_incident_by_id(pool: asyncpg.Pool, incident_id: UUID) -> asyncpg.Record | None:
    return await pool.fetchrow(
        "SELECT * FROM incidents WHERE id = $1",
        incident_id,
    )


async def list_incidents(
    pool: asyncpg.Pool,
    *,
    status: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[asyncpg.Record]:
    if status:
        return await pool.fetch(
            """
            SELECT * FROM incidents WHERE status = $1
            ORDER BY created_at DESC LIMIT $2 OFFSET $3
            """,
            status,
            limit,
            offset,
        )
    return await pool.fetch(
        "SELECT * FROM incidents ORDER BY created_at DESC LIMIT $1 OFFSET $2",
        limit,
        offset,
    )


async def update_incident_status(
    pool: asyncpg.Pool,
    incident_id: UUID,
    status: str,
) -> asyncpg.Record | None:
    closed_at_clause = ", closed_at = NOW()" if status == "closed" else ""
    return await pool.fetchrow(
        f"UPDATE incidents SET status = $1, updated_at = NOW(){closed_at_clause} "  # noqa: S608
        "WHERE id = $2 RETURNING *",
        status,
        incident_id,
    )


async def update_incident(
    pool: asyncpg.Pool,
    incident_id: UUID,
    **fields: object,
) -> asyncpg.Record | None:
    updates = []
    params: list = [incident_id]
    idx = 2

    for key, value in fields.items():
        if value is not None:
            updates.append(f"{key} = ${idx}")
            params.append(value)
            idx += 1

    if not updates:
        return await get_incident_by_id(pool, incident_id)

    updates.append("updated_at = NOW()")
    set_clause = ", ".join(updates)

    return await pool.fetchrow(
        f"UPDATE incidents SET {set_clause} WHERE id = $1 RETURNING *",  # noqa: S608
        *params,
    )


async def purge_expired_incidents(pool: asyncpg.Pool) -> int:
    """Delete closed incidents past their retention period."""
    result = await pool.execute(
        """
        DELETE FROM incidents
        WHERE status = 'closed'
        AND closed_at IS NOT NULL
        AND closed_at + (data_retention_days || ' days')::interval < NOW()
        """
    )
    # result is like "DELETE N"
    return int(result.split()[-1])
