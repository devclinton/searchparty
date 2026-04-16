from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel


class DroneStatus(StrEnum):
    STANDBY = "standby"
    FLYING = "flying"
    RETURNING = "returning"
    CHARGING = "charging"
    MAINTENANCE = "maintenance"


class PatternType(StrEnum):
    PARALLEL_TRACK = "parallel_track"
    EXPANDING_SQUARE = "expanding_square"
    SECTOR_SEARCH = "sector_search"
    CREEPING_LINE = "creeping_line"
    CUSTOM = "custom"


class ObstacleAvoidance(StrEnum):
    STOP = "stop"
    BYPASS = "bypass"
    DISABLED = "disabled"


class ExportFormat(StrEnum):
    WPML = "wpml"
    MAVLINK = "mavlink"
    KML = "kml"
    LITCHI = "litchi"


class DroneCreate(BaseModel):
    model: str
    serial_number: str | None = None
    pilot_user_id: UUID | None = None
    nickname: str | None = None
    has_thermal: bool = False
    camera_preset: str | None = None
    obstacle_avoidance: ObstacleAvoidance = ObstacleAvoidance.STOP


class DroneResponse(BaseModel):
    id: UUID
    incident_id: UUID
    model: str
    serial_number: str | None
    pilot_user_id: UUID | None
    nickname: str | None
    status: DroneStatus
    battery_percent: int | None
    has_thermal: bool
    obstacle_avoidance: ObstacleAvoidance
    created_at: datetime


class MissionCreate(BaseModel):
    name: str
    pattern_type: PatternType
    drone_id: UUID | None = None
    segment_id: UUID | None = None
    altitude_meters: float = 50.0
    speed_ms: float = 5.0
    overlap_percent: float = 70.0
    gimbal_pitch: float = -90.0
    obstacle_avoidance: ObstacleAvoidance = ObstacleAvoidance.STOP
    camera_preset: str | None = None
    # Pattern-specific params
    bounds: dict | None = None  # north/south/east/west
    center_lat: float | None = None
    center_lon: float | None = None
    max_radius_m: float | None = None
    heading_deg: float = 0.0
    num_sectors: int = 6


class MissionResponse(BaseModel):
    id: UUID
    incident_id: UUID
    drone_id: UUID | None
    segment_id: UUID | None
    name: str
    pattern_type: PatternType
    status: str
    altitude_meters: float
    speed_ms: float
    overlap_percent: float
    gimbal_pitch: float
    obstacle_avoidance: str
    waypoint_count: int
    area_sq_meters: float | None
    estimated_flight_time_seconds: float | None
    created_at: datetime


class MissionExportRequest(BaseModel):
    format: ExportFormat


class SrtUploadResponse(BaseModel):
    video_id: UUID
    frame_count: int
    duration_seconds: float
    has_gps: bool
