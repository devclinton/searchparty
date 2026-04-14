from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class OperationSummary(BaseModel):
    incident_id: UUID
    incident_name: str
    status: str
    created_at: datetime
    closed_at: datetime | None
    duration_hours: float | None
    total_teams: int
    total_personnel: int
    total_segments: int
    segments_completed: int
    total_area_sq_meters: float
    average_pod: float
    total_clues: int
    total_gps_tracks: int


class TeamPerformance(BaseModel):
    team_id: UUID
    team_name: str
    status: str
    members_count: int
    segments_assigned: int
    total_check_ins: int
    deployed_duration_hours: float | None
    clues_found: int


class GpxExport(BaseModel):
    """GPX XML string for track export."""

    content: str
    filename: str


class IncidentActionPlan(BaseModel):
    """Printable Incident Action Plan (IAP)."""

    incident_name: str
    incident_commander: str
    status: str
    created_at: str
    subject_info: dict
    ipp: dict | None
    teams: list[dict]
    hazards: list[dict]
    segments: list[dict]
    communication_plan: str
    safety_message: str
