from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel


class HazardType(StrEnum):
    CLIFF = "cliff"
    MINE_SHAFT = "mine_shaft"
    AVALANCHE = "avalanche"
    FLOOD = "flood"
    WATER = "water"
    WILDLIFE = "wildlife"
    UNSTABLE_GROUND = "unstable_ground"
    OTHER = "other"


class Severity(StrEnum):
    CAUTION = "caution"
    WARNING = "warning"
    DANGER = "danger"


class AlertStatus(StrEnum):
    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"


# --- Hazard Zones ---


class HazardZoneCreate(BaseModel):
    name: str
    hazard_type: HazardType
    severity: Severity = Severity.WARNING
    description: str | None = None
    center_lat: float
    center_lon: float
    radius_meters: float = 100.0
    alert_buffer_meters: float = 200.0


class HazardZoneResponse(BaseModel):
    id: UUID
    incident_id: UUID
    created_by_user_id: UUID
    name: str
    hazard_type: HazardType
    severity: Severity
    description: str | None = None
    center_lat: float | None = None
    center_lon: float | None = None
    radius_meters: float = 100.0
    alert_buffer_meters: float = 200.0
    is_active: bool = True
    created_at: datetime
    updated_at: datetime


# --- Emergency Alerts ---


class EmergencyAlertCreate(BaseModel):
    lat: float
    lon: float
    message: str | None = None
    team_id: UUID | None = None


class EmergencyAlertResponse(BaseModel):
    id: UUID
    incident_id: UUID
    user_id: UUID
    team_id: UUID | None = None
    lat: float
    lon: float
    message: str | None = None
    status: AlertStatus
    created_at: datetime
    acknowledged_at: datetime | None = None
    resolved_at: datetime | None = None


class EmergencyAlertUpdate(BaseModel):
    status: AlertStatus


# --- Safety Briefing ---


class BriefingItem(BaseModel):
    label: str
    checked: bool = False


class SafetyBriefingCreate(BaseModel):
    team_id: UUID
    items: list[BriefingItem]


class SafetyBriefingResponse(BaseModel):
    id: UUID
    incident_id: UUID
    team_id: UUID
    briefed_by_user_id: UUID
    items: list[BriefingItem]
    all_items_checked: bool
    briefed_at: datetime


# --- Geofence Check ---


class GeofenceCheckResult(BaseModel):
    in_hazard_zone: bool
    nearby_hazards: list[dict]


# --- Turnaround ---


class TurnaroundStatus(BaseModel):
    team_id: UUID
    team_name: str
    turnaround_time: datetime | None
    is_past_turnaround: bool
    minutes_remaining: float | None


# --- Safety Dashboard ---


class SafetyDashboard(BaseModel):
    active_hazard_zones: int
    active_emergency_alerts: int
    teams_past_turnaround: int
    teams_overdue_checkin: int
    teams_without_briefing: int
    unbriefed_team_names: list[str]
