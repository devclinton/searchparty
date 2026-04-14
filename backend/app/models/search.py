import math
from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel


class SegmentStatus(StrEnum):
    UNASSIGNED = "unassigned"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class ClueType(StrEnum):
    PHYSICAL = "physical"
    TRACK = "track"
    SCENT = "scent"
    WITNESS = "witness"
    OTHER = "other"


# --- POD Math ---


def calculate_pod(coverage: float) -> float:
    """Calculate Probability of Detection from coverage.
    POD = 1 - e^(-coverage)
    Coverage = (ESW * distance_traveled) / area
    """
    return 1.0 - math.exp(-coverage)


def cumulative_pod(existing_pod: float, new_pass_pod: float) -> float:
    """Calculate cumulative POD after an additional search pass.
    P_cum = 1 - (1 - P_existing) * (1 - P_new)
    """
    return 1.0 - (1.0 - existing_pod) * (1.0 - new_pass_pod)


def coverage_from_esw(esw_meters: float, distance_meters: float, area_sq_meters: float) -> float:
    """Calculate coverage from Effective Sweep Width, distance traveled, and area."""
    if area_sq_meters <= 0:
        return 0.0
    return (esw_meters * distance_meters) / area_sq_meters


# --- Segment Models ---


class SegmentCreate(BaseModel):
    name: str
    search_type: str | None = None
    polygon: list[list[float]]  # [[lon, lat], [lon, lat], ...]
    grid_spacing_meters: float = 10.0
    esw_meters: float | None = None
    priority: int = 0
    notes: str | None = None


class SegmentUpdate(BaseModel):
    name: str | None = None
    search_type: str | None = None
    assigned_team_id: UUID | None = None
    grid_spacing_meters: float | None = None
    esw_meters: float | None = None
    priority: int | None = None
    notes: str | None = None
    status: SegmentStatus | None = None


class SegmentRecordPass(BaseModel):
    """Record a search pass over a segment."""

    esw_meters: float
    distance_traveled_meters: float


class SegmentResponse(BaseModel):
    id: UUID
    incident_id: UUID
    name: str
    search_type: str | None = None
    assigned_team_id: UUID | None = None
    area_sq_meters: float | None = None
    grid_spacing_meters: float = 10.0
    esw_meters: float | None = None
    coverage: float = 0.0
    pod: float = 0.0
    passes: int = 0
    status: SegmentStatus = SegmentStatus.UNASSIGNED
    priority: int = 0
    notes: str | None = None
    created_at: datetime
    updated_at: datetime


class CoverageStats(BaseModel):
    total_segments: int
    segments_completed: int
    segments_in_progress: int
    total_area_sq_meters: float
    searched_area_sq_meters: float
    average_pod: float
    overall_coverage_percent: float


# --- Clue Models ---


class ClueCreate(BaseModel):
    lat: float
    lon: float
    description: str
    clue_type: ClueType = ClueType.PHYSICAL
    segment_id: UUID | None = None
    team_id: UUID | None = None
    photo_url: str | None = None


class ClueResponse(BaseModel):
    id: UUID
    incident_id: UUID
    segment_id: UUID | None = None
    found_by_user_id: UUID
    found_by_team_id: UUID | None = None
    lat: float
    lon: float
    description: str
    clue_type: ClueType
    photo_url: str | None = None
    found_at: datetime
    created_at: datetime
