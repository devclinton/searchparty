"""Drone integration API endpoints."""

import json
from typing import Annotated
from uuid import UUID

import asyncpg
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import PlainTextResponse

from app.auth.dependencies import CurrentUser
from app.db.connection import get_pool
from app.db.drones import (
    create_drone,
    create_mission,
    create_video_metadata,
    get_mission,
    list_drones,
    list_missions,
)
from app.drone.camera import CAMERA_PRESETS, calculate_fov, gsd, track_spacing
from app.drone.exporters import export_kml, export_litchi_csv, export_mavlink, export_wpml
from app.drone.patterns import (
    Waypoint,
    creeping_line,
    estimate_flight_time,
    expanding_square,
    parallel_track,
    sector_search,
)
from app.drone.srt_parser import parse_srt
from app.models.drone import (
    DroneCreate,
    DroneResponse,
    MissionCreate,
    MissionExportRequest,
    MissionResponse,
    SrtUploadResponse,
)

router = APIRouter(prefix="/drones", tags=["drones"])


# --- Camera Presets ---


@router.get("/camera-presets")
async def get_camera_presets() -> list[dict]:
    return [
        {
            "key": key,
            "name": cam.name,
            "drone_model": cam.drone_model,
            "has_thermal": cam.has_thermal,
            "fov_h": calculate_fov(cam)[0],
            "fov_v": calculate_fov(cam)[1],
        }
        for key, cam in CAMERA_PRESETS.items()
    ]


@router.get("/camera-presets/{key}/coverage")
async def calculate_coverage(
    key: str,
    altitude: float = 50.0,
    overlap: float = 70.0,
) -> dict:
    camera = CAMERA_PRESETS.get(key)
    if not camera:
        raise HTTPException(status_code=404, detail=f"Camera preset not found: {key}")
    fov_h, fov_v = calculate_fov(camera)
    from app.drone.camera import ground_coverage

    width, height = ground_coverage(altitude, fov_h, fov_v)
    spacing = track_spacing(altitude, camera, overlap)
    resolution = gsd(altitude, camera)

    return {
        "ground_width_m": round(width, 1),
        "ground_height_m": round(height, 1),
        "track_spacing_m": round(spacing, 1),
        "gsd_cm_per_px": round(resolution, 2),
        "fov_h_deg": round(fov_h, 1),
        "fov_v_deg": round(fov_v, 1),
    }


# --- Drone Fleet ---


@router.post("/incidents/{incident_id}/fleet", response_model=DroneResponse, status_code=201)
async def register_drone(
    incident_id: UUID,
    body: DroneCreate,
    user: CurrentUser,
    pool: Annotated[asyncpg.Pool, Depends(get_pool)],
) -> DroneResponse:
    row = await create_drone(
        pool,
        incident_id=incident_id,
        model=body.model,
        serial_number=body.serial_number,
        pilot_user_id=body.pilot_user_id,
        nickname=body.nickname,
        has_thermal=body.has_thermal,
        obstacle_avoidance=body.obstacle_avoidance,
    )
    return DroneResponse(
        id=row["id"],
        incident_id=row["incident_id"],
        model=row["model"],
        serial_number=row["serial_number"],
        pilot_user_id=row["pilot_user_id"],
        nickname=row["nickname"],
        status=row["status"],
        battery_percent=row["battery_percent"],
        has_thermal=row["has_thermal"],
        obstacle_avoidance=row["obstacle_avoidance"],
        created_at=row["created_at"],
    )


@router.get("/incidents/{incident_id}/fleet", response_model=list[DroneResponse])
async def list_fleet(
    incident_id: UUID,
    user: CurrentUser,
    pool: Annotated[asyncpg.Pool, Depends(get_pool)],
) -> list[DroneResponse]:
    rows = await list_drones(pool, incident_id)
    return [
        DroneResponse(
            id=r["id"],
            incident_id=r["incident_id"],
            model=r["model"],
            serial_number=r["serial_number"],
            pilot_user_id=r["pilot_user_id"],
            nickname=r["nickname"],
            status=r["status"],
            battery_percent=r["battery_percent"],
            has_thermal=r["has_thermal"],
            obstacle_avoidance=r["obstacle_avoidance"],
            created_at=r["created_at"],
        )
        for r in rows
    ]


# --- Missions ---


@router.post("/incidents/{incident_id}/missions", response_model=MissionResponse, status_code=201)
async def create_drone_mission(
    incident_id: UUID,
    body: MissionCreate,
    user: CurrentUser,
    pool: Annotated[asyncpg.Pool, Depends(get_pool)],
) -> MissionResponse:
    # Resolve camera preset for track spacing
    camera = CAMERA_PRESETS.get(body.camera_preset or "dji_m3e")
    spacing = track_spacing(body.altitude_meters, camera, body.overlap_percent) if camera else 20.0

    # Generate pattern
    waypoints: list[Waypoint] = []

    if body.pattern_type == "parallel_track":
        if not body.bounds:
            raise HTTPException(status_code=422, detail="bounds required for parallel_track")
        waypoints = parallel_track(
            body.bounds,
            body.altitude_meters,
            spacing,
            body.speed_ms,
            body.gimbal_pitch,
            body.heading_deg,
        )
    elif body.pattern_type == "expanding_square":
        if body.center_lat is None or body.center_lon is None:
            raise HTTPException(status_code=422, detail="center_lat/lon required")
        waypoints = expanding_square(
            body.center_lat,
            body.center_lon,
            body.altitude_meters,
            spacing,
            body.max_radius_m or 500.0,
            body.speed_ms,
            body.gimbal_pitch,
        )
    elif body.pattern_type == "sector_search":
        if body.center_lat is None or body.center_lon is None:
            raise HTTPException(status_code=422, detail="center_lat/lon required")
        waypoints = sector_search(
            body.center_lat,
            body.center_lon,
            body.max_radius_m or 300.0,
            body.altitude_meters,
            body.num_sectors,
            body.speed_ms,
            body.gimbal_pitch,
        )
    elif body.pattern_type == "creeping_line":
        if not body.bounds:
            raise HTTPException(status_code=422, detail="bounds required for creeping_line")
        waypoints = creeping_line(
            body.bounds,
            body.heading_deg,
            body.altitude_meters,
            spacing,
            body.speed_ms,
            body.gimbal_pitch,
        )

    flight_time = estimate_flight_time(waypoints)
    wp_json = json.dumps(
        [
            {
                "lat": w.lat,
                "lon": w.lon,
                "alt": w.altitude_m,
                "speed": w.speed_ms,
                "gimbal": w.gimbal_pitch,
                "action": w.action,
            }
            for w in waypoints
        ]
    )

    row = await create_mission(
        pool,
        incident_id=incident_id,
        drone_id=body.drone_id,
        segment_id=body.segment_id,
        name=body.name,
        pattern_type=body.pattern_type,
        altitude_meters=body.altitude_meters,
        speed_ms=body.speed_ms,
        overlap_percent=body.overlap_percent,
        gimbal_pitch=body.gimbal_pitch,
        obstacle_avoidance=body.obstacle_avoidance,
        waypoints_json=wp_json,
        area_sq_meters=None,
        estimated_flight_time=flight_time,
    )

    return MissionResponse(
        id=row["id"],
        incident_id=row["incident_id"],
        drone_id=row["drone_id"],
        segment_id=row["segment_id"],
        name=row["name"],
        pattern_type=row["pattern_type"],
        status=row["status"],
        altitude_meters=row["altitude_meters"],
        speed_ms=row["speed_ms"],
        overlap_percent=row["overlap_percent"],
        gimbal_pitch=row["gimbal_pitch"],
        obstacle_avoidance=row["obstacle_avoidance"],
        waypoint_count=len(waypoints),
        area_sq_meters=row["area_sq_meters"],
        estimated_flight_time_seconds=row["estimated_flight_time_seconds"],
        created_at=row["created_at"],
    )


@router.get("/incidents/{incident_id}/missions", response_model=list[MissionResponse])
async def list_drone_missions(
    incident_id: UUID,
    user: CurrentUser,
    pool: Annotated[asyncpg.Pool, Depends(get_pool)],
) -> list[MissionResponse]:
    rows = await list_missions(pool, incident_id)
    return [
        MissionResponse(
            id=r["id"],
            incident_id=r["incident_id"],
            drone_id=r["drone_id"],
            segment_id=r["segment_id"],
            name=r["name"],
            pattern_type=r["pattern_type"],
            status=r["status"],
            altitude_meters=r["altitude_meters"],
            speed_ms=r["speed_ms"],
            overlap_percent=r["overlap_percent"],
            gimbal_pitch=r["gimbal_pitch"],
            obstacle_avoidance=r["obstacle_avoidance"],
            waypoint_count=len(r["waypoints"]) if r["waypoints"] else 0,
            area_sq_meters=r["area_sq_meters"],
            estimated_flight_time_seconds=r["estimated_flight_time_seconds"],
            created_at=r["created_at"],
        )
        for r in rows
    ]


# --- Export ---


@router.post("/missions/{mission_id}/export")
async def export_mission(
    mission_id: UUID,
    body: MissionExportRequest,
    user: CurrentUser,
    pool: Annotated[asyncpg.Pool, Depends(get_pool)],
) -> PlainTextResponse:
    mission = await get_mission(pool, mission_id)
    if mission is None:
        raise HTTPException(status_code=404, detail="Mission not found")

    wp_data = mission["waypoints"] or []
    if isinstance(wp_data, str):
        wp_data = json.loads(wp_data)
    waypoints = [
        Waypoint(
            lat=w["lat"],
            lon=w["lon"],
            altitude_m=w["alt"],
            speed_ms=w.get("speed", 5.0),
            gimbal_pitch=w.get("gimbal", -90.0),
            action=w.get("action", "fly"),
        )
        for w in wp_data
    ]

    name = mission["name"]
    fmt = body.format

    if fmt == "wpml":
        content = export_wpml(waypoints, name, obstacle_avoidance=mission["obstacle_avoidance"])
        media = "application/xml"
        ext = "wpml"
    elif fmt == "mavlink":
        content = export_mavlink(waypoints)
        media = "application/json"
        ext = "plan"
    elif fmt == "kml":
        content = export_kml(waypoints, name)
        media = "application/vnd.google-earth.kml+xml"
        ext = "kml"
    elif fmt == "litchi":
        content = export_litchi_csv(waypoints)
        media = "text/csv"
        ext = "csv"
    else:
        raise HTTPException(status_code=422, detail=f"Unsupported format: {fmt}")

    filename = f"{name.replace(' ', '_')}.{ext}"
    return PlainTextResponse(
        content=content,
        media_type=media,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# --- Video Metadata ---


@router.post("/incidents/{incident_id}/video-srt", response_model=SrtUploadResponse)
async def upload_srt(
    incident_id: UUID,
    user: CurrentUser,
    pool: Annotated[asyncpg.Pool, Depends(get_pool)],
    file: UploadFile = File(...),
    drone_id: UUID | None = Form(None),
    mission_id: UUID | None = Form(None),
    external_url: str | None = Form(None),
) -> SrtUploadResponse:
    """Upload a DJI SRT file to index video telemetry."""
    content = await file.read()
    text = content.decode("utf-8", errors="ignore")
    frames = parse_srt(text)

    if not frames:
        raise HTTPException(status_code=422, detail="No frames found in SRT file")

    has_gps = any(f.lat is not None for f in frames)
    duration = frames[-1].timestamp_ms / 1000.0 if frames else 0.0

    telemetry = [
        {
            "ts_ms": f.timestamp_ms,
            "lat": f.lat,
            "lon": f.lon,
            "alt": f.altitude,
            "yaw": f.gimbal_yaw,
            "pitch": f.gimbal_pitch,
        }
        for f in frames
        if f.lat is not None
    ]

    row = await create_video_metadata(
        pool,
        incident_id=incident_id,
        drone_id=drone_id,
        mission_id=mission_id,
        filename=file.filename or "unknown.srt",
        external_url=external_url,
        duration_seconds=duration,
        frame_count=len(frames),
        telemetry_json=json.dumps(telemetry),
    )

    return SrtUploadResponse(
        video_id=row["id"],
        frame_count=len(frames),
        duration_seconds=duration,
        has_gps=has_gps,
    )
