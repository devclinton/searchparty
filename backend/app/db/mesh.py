from uuid import UUID

import asyncpg


async def upsert_mesh_node(
    pool: asyncpg.Pool,
    *,
    node_id: str,
    incident_id: UUID | None = None,
    user_id: UUID | None = None,
    long_name: str | None = None,
    short_name: str | None = None,
    hw_model: str | None = None,
    battery_level: int | None = None,
    last_lat: float | None = None,
    last_lon: float | None = None,
    last_altitude: float | None = None,
    snr: float | None = None,
) -> asyncpg.Record:
    return await pool.fetchrow(
        """
        INSERT INTO mesh_nodes (
            node_id, incident_id, user_id, long_name, short_name,
            hw_model, battery_level, last_lat, last_lon,
            last_altitude, snr, last_heard_at
        )
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, NOW())
        ON CONFLICT (node_id) DO UPDATE SET
            incident_id = COALESCE(EXCLUDED.incident_id, mesh_nodes.incident_id),
            user_id = COALESCE(EXCLUDED.user_id, mesh_nodes.user_id),
            long_name = COALESCE(EXCLUDED.long_name, mesh_nodes.long_name),
            short_name = COALESCE(EXCLUDED.short_name, mesh_nodes.short_name),
            hw_model = COALESCE(EXCLUDED.hw_model, mesh_nodes.hw_model),
            battery_level = COALESCE(EXCLUDED.battery_level, mesh_nodes.battery_level),
            last_lat = COALESCE(EXCLUDED.last_lat, mesh_nodes.last_lat),
            last_lon = COALESCE(EXCLUDED.last_lon, mesh_nodes.last_lon),
            last_altitude = COALESCE(EXCLUDED.last_altitude, mesh_nodes.last_altitude),
            snr = COALESCE(EXCLUDED.snr, mesh_nodes.snr),
            last_heard_at = NOW()
        RETURNING *
        """,
        node_id,
        incident_id,
        user_id,
        long_name,
        short_name,
        hw_model,
        battery_level,
        last_lat,
        last_lon,
        last_altitude,
        snr,
    )


async def list_mesh_nodes(pool: asyncpg.Pool, incident_id: UUID) -> list[asyncpg.Record]:
    return await pool.fetch(
        "SELECT * FROM mesh_nodes WHERE incident_id = $1 ORDER BY last_heard_at DESC",
        incident_id,
    )


async def insert_mesh_message(
    pool: asyncpg.Pool,
    *,
    incident_id: UUID | None,
    from_node: str,
    to_node: str | None,
    channel: int = 0,
    message_text: str,
    is_emergency: bool = False,
) -> asyncpg.Record:
    return await pool.fetchrow(
        """
        INSERT INTO mesh_messages (
            incident_id, from_node, to_node, channel,
            message_text, is_emergency
        )
        VALUES ($1, $2, $3, $4, $5, $6)
        RETURNING *
        """,
        incident_id,
        from_node,
        to_node,
        channel,
        message_text,
        is_emergency,
    )


async def list_mesh_messages(
    pool: asyncpg.Pool,
    incident_id: UUID,
    limit: int = 50,
) -> list[asyncpg.Record]:
    return await pool.fetch(
        """
        SELECT * FROM mesh_messages
        WHERE incident_id = $1
        ORDER BY received_at DESC
        LIMIT $2
        """,
        incident_id,
        limit,
    )
