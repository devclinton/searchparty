"""Shared models for all GPS import parsers."""

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel


class ImportPointType(StrEnum):
    TRACKPOINT = "trackpoint"
    WAYPOINT = "waypoint"


class ImportedPoint(BaseModel):
    lat: float
    lon: float
    altitude: float | None = None
    timestamp: datetime | None = None
    accuracy: float | None = None
    name: str | None = None
    point_type: ImportPointType = ImportPointType.TRACKPOINT


class ImportedTrack(BaseModel):
    name: str | None = None
    points: list[ImportedPoint]
    source_format: str
    source_device: str | None = None


class ImportResult(BaseModel):
    tracks: list[ImportedTrack]
    waypoints: list[ImportedPoint]
    total_points: int
    source_format: str
    errors: list[str]
