from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class GpsPointInput(BaseModel):
    lat: float
    lon: float
    altitude: float | None = None
    accuracy: float
    timestamp: datetime


class GpsTrackUpload(BaseModel):
    track_id: str
    incident_id: UUID
    team_id: UUID | None = None
    started_at: datetime
    ended_at: datetime | None = None
    points: list[GpsPointInput]


class GpsTrackResponse(BaseModel):
    id: str
    user_id: UUID
    incident_id: UUID
    team_id: UUID | None = None
    started_at: datetime
    ended_at: datetime | None = None
    point_count: int
    created_at: datetime


class GpsPointResponse(BaseModel):
    lat: float
    lon: float
    altitude: float | None = None
    accuracy: float
    recorded_at: datetime
