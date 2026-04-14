from uuid import UUID

import asyncpg

# --- Segments ---


async def create_segment(
    pool: asyncpg.Pool,
    *,
    incident_id: UUID,
    name: str,
    search_type: str | None = None,
    polygon_wkt: str,
    grid_spacing_meters: float = 10.0,
    esw_meters: float | None = None,
    priority: int = 0,
    notes: str | None = None,
) -> asyncpg.Record:
    return await pool.fetchrow(
        """
        INSERT INTO search_segments (
            incident_id, name, search_type, polygon,
            area_sq_meters, grid_spacing_meters, esw_meters,
            priority, notes
        )
        VALUES (
            $1, $2, $3, ST_GeomFromText($4, 4326),
            ST_Area(ST_Transform(ST_GeomFromText($4, 4326), 3857)),
            $5, $6, $7, $8
        )
        RETURNING id, incident_id, name, search_type,
            assigned_team_id, area_sq_meters, grid_spacing_meters,
            esw_meters, coverage, pod, passes, status, priority,
            notes, created_at, updated_at
        """,
        incident_id,
        name,
        search_type,
        polygon_wkt,
        grid_spacing_meters,
        esw_meters,
        priority,
        notes,
    )


async def get_segment_by_id(pool: asyncpg.Pool, segment_id: UUID) -> asyncpg.Record | None:
    return await pool.fetchrow(
        """
        SELECT id, incident_id, name, search_type,
            assigned_team_id, area_sq_meters, grid_spacing_meters,
            esw_meters, coverage, pod, passes, status, priority,
            notes, created_at, updated_at
        FROM search_segments WHERE id = $1
        """,
        segment_id,
    )


async def list_segments_by_incident(pool: asyncpg.Pool, incident_id: UUID) -> list[asyncpg.Record]:
    return await pool.fetch(
        """
        SELECT id, incident_id, name, search_type,
            assigned_team_id, area_sq_meters, grid_spacing_meters,
            esw_meters, coverage, pod, passes, status, priority,
            notes, created_at, updated_at
        FROM search_segments
        WHERE incident_id = $1
        ORDER BY priority DESC, created_at
        """,
        incident_id,
    )


async def update_segment(
    pool: asyncpg.Pool,
    segment_id: UUID,
    **fields: object,
) -> asyncpg.Record | None:
    updates = []
    params: list = [segment_id]
    idx = 2

    for key, value in fields.items():
        if value is not None:
            updates.append(f"{key} = ${idx}")
            params.append(value)
            idx += 1

    if not updates:
        return await get_segment_by_id(pool, segment_id)

    updates.append("updated_at = NOW()")
    set_clause = ", ".join(updates)

    return await pool.fetchrow(
        f"""
        UPDATE search_segments SET {set_clause}
        WHERE id = $1
        RETURNING id, incident_id, name, search_type,
            assigned_team_id, area_sq_meters, grid_spacing_meters,
            esw_meters, coverage, pod, passes, status, priority,
            notes, created_at, updated_at
        """,  # noqa: S608
        *params,
    )


async def record_search_pass(
    pool: asyncpg.Pool,
    segment_id: UUID,
    *,
    new_coverage: float,
    new_pod: float,
) -> asyncpg.Record | None:
    return await pool.fetchrow(
        """
        UPDATE search_segments SET
            coverage = coverage + $2,
            pod = 1.0 - (1.0 - pod) * (1.0 - $3),
            passes = passes + 1,
            updated_at = NOW()
        WHERE id = $1
        RETURNING id, incident_id, name, search_type,
            assigned_team_id, area_sq_meters, grid_spacing_meters,
            esw_meters, coverage, pod, passes, status, priority,
            notes, created_at, updated_at
        """,
        segment_id,
        new_coverage,
        new_pod,
    )


async def get_coverage_stats(pool: asyncpg.Pool, incident_id: UUID) -> asyncpg.Record | None:
    return await pool.fetchrow(
        """
        SELECT
            COUNT(*) as total_segments,
            COUNT(*) FILTER (WHERE status = 'completed') as segments_completed,
            COUNT(*) FILTER (WHERE status = 'in_progress') as segments_in_progress,
            COALESCE(SUM(area_sq_meters), 0) as total_area_sq_meters,
            COALESCE(SUM(area_sq_meters * coverage), 0) as searched_area_sq_meters,
            COALESCE(AVG(pod), 0) as average_pod,
            CASE
                WHEN SUM(area_sq_meters) > 0
                THEN SUM(area_sq_meters * coverage) / SUM(area_sq_meters) * 100
                ELSE 0
            END as overall_coverage_percent
        FROM search_segments
        WHERE incident_id = $1
        """,
        incident_id,
    )


# --- Clues ---


async def create_clue(
    pool: asyncpg.Pool,
    *,
    incident_id: UUID,
    found_by_user_id: UUID,
    lat: float,
    lon: float,
    description: str,
    clue_type: str = "physical",
    segment_id: UUID | None = None,
    found_by_team_id: UUID | None = None,
    photo_url: str | None = None,
) -> asyncpg.Record:
    return await pool.fetchrow(
        """
        INSERT INTO clues (
            incident_id, segment_id, found_by_user_id,
            found_by_team_id, lat, lon, point,
            description, clue_type, photo_url
        )
        VALUES ($1, $2, $3, $4, $5, $6, ST_SetSRID(ST_MakePoint($6, $5), 4326),
                $7, $8, $9)
        RETURNING id, incident_id, segment_id, found_by_user_id,
            found_by_team_id, lat, lon, description, clue_type,
            photo_url, found_at, created_at
        """,
        incident_id,
        segment_id,
        found_by_user_id,
        found_by_team_id,
        lat,
        lon,
        description,
        clue_type,
        photo_url,
    )


async def list_clues_by_incident(pool: asyncpg.Pool, incident_id: UUID) -> list[asyncpg.Record]:
    return await pool.fetch(
        """
        SELECT id, incident_id, segment_id, found_by_user_id,
            found_by_team_id, lat, lon, description, clue_type,
            photo_url, found_at, created_at
        FROM clues
        WHERE incident_id = $1
        ORDER BY found_at DESC
        """,
        incident_id,
    )
