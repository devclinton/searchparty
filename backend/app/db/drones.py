from uuid import UUID

import asyncpg


async def create_drone(
    pool: asyncpg.Pool,
    *,
    incident_id: UUID,
    model: str,
    serial_number: str | None = None,
    pilot_user_id: UUID | None = None,
    nickname: str | None = None,
    has_thermal: bool = False,
    obstacle_avoidance: str = "stop",
) -> asyncpg.Record:
    return await pool.fetchrow(
        """
        INSERT INTO drones (incident_id, model, serial_number,
            pilot_user_id, nickname, has_thermal, obstacle_avoidance)
        VALUES ($1, $2, $3, $4, $5, $6, $7)
        RETURNING *
        """,
        incident_id,
        model,
        serial_number,
        pilot_user_id,
        nickname,
        has_thermal,
        obstacle_avoidance,
    )


async def list_drones(pool: asyncpg.Pool, incident_id: UUID) -> list[asyncpg.Record]:
    return await pool.fetch(
        "SELECT * FROM drones WHERE incident_id = $1 ORDER BY created_at",
        incident_id,
    )


async def create_mission(
    pool: asyncpg.Pool,
    *,
    incident_id: UUID,
    drone_id: UUID | None,
    segment_id: UUID | None,
    name: str,
    pattern_type: str,
    altitude_meters: float,
    speed_ms: float,
    overlap_percent: float,
    gimbal_pitch: float,
    obstacle_avoidance: str,
    waypoints_json: str,
    area_sq_meters: float | None,
    estimated_flight_time: float | None,
) -> asyncpg.Record:
    return await pool.fetchrow(
        """
        INSERT INTO drone_missions (
            incident_id, drone_id, segment_id, name, pattern_type,
            altitude_meters, speed_ms, overlap_percent, gimbal_pitch,
            obstacle_avoidance, waypoints, area_sq_meters,
            estimated_flight_time_seconds
        )
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11::jsonb, $12, $13)
        RETURNING *
        """,
        incident_id,
        drone_id,
        segment_id,
        name,
        pattern_type,
        altitude_meters,
        speed_ms,
        overlap_percent,
        gimbal_pitch,
        obstacle_avoidance,
        waypoints_json,
        area_sq_meters,
        estimated_flight_time,
    )


async def get_mission(pool: asyncpg.Pool, mission_id: UUID) -> asyncpg.Record | None:
    return await pool.fetchrow("SELECT * FROM drone_missions WHERE id = $1", mission_id)


async def list_missions(pool: asyncpg.Pool, incident_id: UUID) -> list[asyncpg.Record]:
    return await pool.fetch(
        "SELECT * FROM drone_missions WHERE incident_id = $1 ORDER BY created_at",
        incident_id,
    )


async def create_video_metadata(
    pool: asyncpg.Pool,
    *,
    incident_id: UUID,
    drone_id: UUID | None,
    mission_id: UUID | None,
    filename: str,
    external_url: str | None,
    duration_seconds: float,
    frame_count: int,
    telemetry_json: str,
) -> asyncpg.Record:
    return await pool.fetchrow(
        """
        INSERT INTO video_metadata (
            incident_id, drone_id, mission_id, filename,
            external_url, duration_seconds, frame_count, telemetry
        )
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8::jsonb)
        RETURNING *
        """,
        incident_id,
        drone_id,
        mission_id,
        filename,
        external_url,
        duration_seconds,
        frame_count,
        telemetry_json,
    )
