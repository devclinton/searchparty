from uuid import UUID

import asyncpg


async def upsert_gps_track(
    pool: asyncpg.Pool,
    *,
    track_id: str,
    user_id: UUID,
    incident_id: UUID,
    team_id: UUID | None,
    started_at: object,
    ended_at: object | None,
    point_count: int,
) -> asyncpg.Record:
    return await pool.fetchrow(
        """
        INSERT INTO gps_tracks (id, user_id, incident_id, team_id,
            started_at, ended_at, point_count)
        VALUES ($1, $2, $3, $4, $5, $6, $7)
        ON CONFLICT (id) DO UPDATE SET
            ended_at = EXCLUDED.ended_at,
            point_count = EXCLUDED.point_count
        RETURNING *
        """,
        track_id,
        user_id,
        incident_id,
        team_id,
        started_at,
        ended_at,
        point_count,
    )


async def insert_gps_points(
    pool: asyncpg.Pool,
    track_id: str,
    points: list[tuple],
) -> int:
    """Bulk insert GPS points. Each tuple: (track_id, lat, lon, altitude, accuracy, recorded_at)."""
    await pool.executemany(
        """
        INSERT INTO gps_points (track_id, lat, lon, altitude, accuracy, recorded_at)
        VALUES ($1, $2, $3, $4, $5, $6)
        ON CONFLICT DO NOTHING
        """,
        points,
    )
    return len(points)


async def get_tracks_by_incident(pool: asyncpg.Pool, incident_id: UUID) -> list[asyncpg.Record]:
    return await pool.fetch(
        "SELECT * FROM gps_tracks WHERE incident_id = $1 ORDER BY started_at",
        incident_id,
    )


async def get_track_points(pool: asyncpg.Pool, track_id: str) -> list[asyncpg.Record]:
    return await pool.fetch(
        "SELECT lat, lon, altitude, accuracy, recorded_at FROM gps_points "
        "WHERE track_id = $1 ORDER BY recorded_at",
        track_id,
    )


async def get_latest_positions(pool: asyncpg.Pool, incident_id: UUID) -> list[asyncpg.Record]:
    """Get the most recent GPS point per user for an incident."""
    return await pool.fetch(
        """
        SELECT DISTINCT ON (gt.user_id)
            gt.user_id,
            u.display_name,
            t.name as team_name,
            tm.role,
            gp.lat,
            gp.lon,
            gp.accuracy,
            gp.recorded_at
        FROM gps_points gp
        JOIN gps_tracks gt ON gp.track_id = gt.id
        JOIN users u ON gt.user_id = u.id
        LEFT JOIN teams t ON gt.team_id = t.id
        LEFT JOIN team_members tm ON tm.user_id = gt.user_id
            AND tm.team_id = gt.team_id
            AND tm.signed_out_at IS NULL
        WHERE gt.incident_id = $1
        ORDER BY gt.user_id, gp.recorded_at DESC
        """,
        incident_id,
    )
