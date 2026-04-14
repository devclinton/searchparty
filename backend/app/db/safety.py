from uuid import UUID

import asyncpg

# --- Hazard Zones ---


async def create_hazard_zone(
    pool: asyncpg.Pool,
    *,
    incident_id: UUID,
    created_by_user_id: UUID,
    name: str,
    hazard_type: str,
    severity: str = "warning",
    description: str | None = None,
    center_lat: float,
    center_lon: float,
    radius_meters: float = 100.0,
    alert_buffer_meters: float = 200.0,
) -> asyncpg.Record:
    return await pool.fetchrow(
        """
        INSERT INTO hazard_zones (
            incident_id, created_by_user_id, name, hazard_type,
            severity, description, center_lat, center_lon,
            radius_meters, alert_buffer_meters,
            polygon
        )
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10,
            ST_Buffer(
                ST_Transform(ST_SetSRID(ST_MakePoint($8, $7), 4326), 3857),
                $9
            )::geometry(Polygon, 3857)
        )
        RETURNING id, incident_id, created_by_user_id, name,
            hazard_type, severity, description, center_lat,
            center_lon, radius_meters, alert_buffer_meters,
            is_active, created_at, updated_at
        """,
        incident_id,
        created_by_user_id,
        name,
        hazard_type,
        severity,
        description,
        center_lat,
        center_lon,
        radius_meters,
        alert_buffer_meters,
    )


async def list_hazard_zones(pool: asyncpg.Pool, incident_id: UUID) -> list[asyncpg.Record]:
    return await pool.fetch(
        """
        SELECT id, incident_id, created_by_user_id, name,
            hazard_type, severity, description, center_lat,
            center_lon, radius_meters, alert_buffer_meters,
            is_active, created_at, updated_at
        FROM hazard_zones
        WHERE incident_id = $1 AND is_active = TRUE
        ORDER BY severity DESC, created_at
        """,
        incident_id,
    )


async def check_geofence(
    pool: asyncpg.Pool, incident_id: UUID, lat: float, lon: float
) -> list[asyncpg.Record]:
    """Check if a point is within any hazard zone's alert buffer."""
    return await pool.fetch(
        """
        SELECT id, name, hazard_type, severity,
            center_lat, center_lon, radius_meters,
            alert_buffer_meters
        FROM hazard_zones
        WHERE incident_id = $1 AND is_active = TRUE
        AND ST_DWithin(
            ST_Transform(ST_SetSRID(ST_MakePoint($3, $2), 4326), 3857),
            ST_Transform(polygon, 3857),
            alert_buffer_meters
        )
        """,
        incident_id,
        lat,
        lon,
    )


# --- Emergency Alerts ---


async def create_emergency_alert(
    pool: asyncpg.Pool,
    *,
    incident_id: UUID,
    user_id: UUID,
    lat: float,
    lon: float,
    message: str | None = None,
    team_id: UUID | None = None,
) -> asyncpg.Record:
    return await pool.fetchrow(
        """
        INSERT INTO emergency_alerts (
            incident_id, user_id, team_id, lat, lon,
            point, message
        )
        VALUES ($1, $2, $3, $4, $5,
            ST_SetSRID(ST_MakePoint($5, $4), 4326), $6)
        RETURNING *
        """,
        incident_id,
        user_id,
        team_id,
        lat,
        lon,
        message,
    )


async def list_emergency_alerts(
    pool: asyncpg.Pool,
    incident_id: UUID,
    status: str | None = None,
) -> list[asyncpg.Record]:
    if status:
        return await pool.fetch(
            """
            SELECT id, incident_id, user_id, team_id, lat, lon,
                message, status, created_at, acknowledged_at, resolved_at
            FROM emergency_alerts
            WHERE incident_id = $1 AND status = $2
            ORDER BY created_at DESC
            """,
            incident_id,
            status,
        )
    return await pool.fetch(
        """
        SELECT id, incident_id, user_id, team_id, lat, lon,
            message, status, created_at, acknowledged_at, resolved_at
        FROM emergency_alerts
        WHERE incident_id = $1
        ORDER BY created_at DESC
        """,
        incident_id,
    )


async def update_emergency_alert_status(
    pool: asyncpg.Pool,
    alert_id: UUID,
    status: str,
) -> asyncpg.Record | None:
    time_col = ""
    if status == "acknowledged":
        time_col = ", acknowledged_at = NOW()"
    elif status == "resolved":
        time_col = ", resolved_at = NOW()"
    return await pool.fetchrow(
        f"""
        UPDATE emergency_alerts SET status = $1{time_col}
        WHERE id = $2
        RETURNING id, incident_id, user_id, team_id, lat, lon,
            message, status, created_at, acknowledged_at, resolved_at
        """,  # noqa: S608
        status,
        alert_id,
    )


# --- Safety Briefings ---


async def upsert_safety_briefing(
    pool: asyncpg.Pool,
    *,
    incident_id: UUID,
    team_id: UUID,
    briefed_by_user_id: UUID,
    items_json: str,
    all_checked: bool,
) -> asyncpg.Record:
    return await pool.fetchrow(
        """
        INSERT INTO safety_briefings (
            incident_id, team_id, briefed_by_user_id, items, all_items_checked
        )
        VALUES ($1, $2, $3, $4::jsonb, $5)
        ON CONFLICT (team_id) DO UPDATE SET
            briefed_by_user_id = EXCLUDED.briefed_by_user_id,
            items = EXCLUDED.items,
            all_items_checked = EXCLUDED.all_items_checked,
            briefed_at = NOW()
        RETURNING *
        """,
        incident_id,
        team_id,
        briefed_by_user_id,
        items_json,
        all_checked,
    )


async def get_briefing_for_team(pool: asyncpg.Pool, team_id: UUID) -> asyncpg.Record | None:
    return await pool.fetchrow(
        "SELECT * FROM safety_briefings WHERE team_id = $1",
        team_id,
    )


async def get_unbriefed_teams(pool: asyncpg.Pool, incident_id: UUID) -> list[asyncpg.Record]:
    return await pool.fetch(
        """
        SELECT t.id, t.name FROM teams t
        LEFT JOIN safety_briefings sb ON t.id = sb.team_id
        WHERE t.incident_id = $1
        AND (sb.id IS NULL OR sb.all_items_checked = FALSE)
        AND t.status != 'stood_down'
        """,
        incident_id,
    )
