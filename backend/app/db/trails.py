from uuid import UUID

import asyncpg


async def create_trail(
    pool: asyncpg.Pool,
    *,
    incident_id: UUID | None,
    name: str | None,
    trail_type: str = "custom",
    source: str = "custom",
    source_id: str | None = None,
    geometry_wkt: str,
    surface: str | None = None,
    difficulty: str | None = None,
) -> asyncpg.Record:
    return await pool.fetchrow(
        """
        INSERT INTO trails (
            incident_id, name, trail_type, source, source_id,
            geometry, length_meters, surface, difficulty
        )
        VALUES (
            $1, $2, $3, $4, $5,
            ST_GeomFromText($6, 4326),
            ST_Length(ST_Transform(ST_GeomFromText($6, 4326), 3857)),
            $7, $8
        )
        RETURNING id, incident_id, name, trail_type, source, source_id,
            surface, difficulty, length_meters, is_active, created_at, updated_at
        """,
        incident_id,
        name,
        trail_type,
        source,
        source_id,
        geometry_wkt,
        surface,
        difficulty,
    )


async def list_trails_by_bbox(
    pool: asyncpg.Pool,
    north: float,
    south: float,
    east: float,
    west: float,
    incident_id: UUID | None = None,
) -> list[asyncpg.Record]:
    bbox_wkt = (
        f"POLYGON(({west} {south}, {east} {south}, {east} {north}, {west} {north}, {west} {south}))"
    )
    if incident_id:
        return await pool.fetch(
            """
            SELECT id, incident_id, name, trail_type, source,
                source_id, surface, difficulty, length_meters,
                is_active, created_at, updated_at,
                ST_AsGeoJSON(geometry)::json as geojson
            FROM trails
            WHERE is_active = TRUE
            AND (incident_id IS NULL OR incident_id = $2)
            AND ST_Intersects(geometry, ST_GeomFromText($1, 4326))
            ORDER BY name
            """,
            bbox_wkt,
            incident_id,
        )
    return await pool.fetch(
        """
        SELECT id, incident_id, name, trail_type, source,
            source_id, surface, difficulty, length_meters,
            is_active, created_at, updated_at,
            ST_AsGeoJSON(geometry)::json as geojson
        FROM trails
        WHERE is_active = TRUE
        AND ST_Intersects(geometry, ST_GeomFromText($1, 4326))
        ORDER BY name
        """,
        bbox_wkt,
    )


async def list_trails_by_incident(pool: asyncpg.Pool, incident_id: UUID) -> list[asyncpg.Record]:
    return await pool.fetch(
        """
        SELECT id, incident_id, name, trail_type, source,
            source_id, surface, difficulty, length_meters,
            is_active, created_at, updated_at,
            ST_AsGeoJSON(geometry)::json as geojson
        FROM trails
        WHERE (incident_id = $1 OR incident_id IS NULL)
        AND is_active = TRUE
        ORDER BY name
        """,
        incident_id,
    )


async def bulk_insert_trails(
    pool: asyncpg.Pool,
    trails: list[tuple],
) -> int:
    """Bulk insert trails. Each tuple:
    (incident_id, name, trail_type, source, source_id, geometry_wkt, surface, difficulty)
    """
    await pool.executemany(
        """
        INSERT INTO trails (
            incident_id, name, trail_type, source, source_id,
            geometry, length_meters, surface, difficulty
        )
        VALUES (
            $1, $2, $3, $4, $5,
            ST_GeomFromText($6, 4326),
            ST_Length(ST_Transform(ST_GeomFromText($6, 4326), 3857)),
            $7, $8
        )
        ON CONFLICT DO NOTHING
        """,
        trails,
    )
    return len(trails)


# --- Junctions ---


async def create_junction(
    pool: asyncpg.Pool,
    *,
    incident_id: UUID,
    lat: float,
    lon: float,
    trail_count: int,
    trail_names: list[str],
    priority_score: float = 0.0,
) -> asyncpg.Record:
    return await pool.fetchrow(
        """
        INSERT INTO trail_junctions (
            incident_id, lat, lon, point,
            trail_count, trail_names, priority_score
        )
        VALUES ($1, $2, $3, ST_SetSRID(ST_MakePoint($3, $2), 4326),
                $4, $5, $6)
        RETURNING *
        """,
        incident_id,
        lat,
        lon,
        trail_count,
        trail_names,
        priority_score,
    )


async def list_junctions_by_incident(pool: asyncpg.Pool, incident_id: UUID) -> list[asyncpg.Record]:
    return await pool.fetch(
        """
        SELECT id, incident_id, lat, lon, trail_count,
            trail_names, priority_score, created_at
        FROM trail_junctions
        WHERE incident_id = $1
        ORDER BY priority_score DESC
        """,
        incident_id,
    )
