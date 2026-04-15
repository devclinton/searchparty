from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel


class TrailType(StrEnum):
    PATH = "path"
    FOOTWAY = "footway"
    TRACK = "track"
    BRIDLEWAY = "bridleway"
    CYCLEWAY = "cycleway"
    ROAD = "road"
    CUSTOM = "custom"


class TrailSource(StrEnum):
    OSM = "osm"
    USFS = "usfs"
    NPS = "nps"
    BLM = "blm"
    STATE = "state"
    SHAPEFILE = "shapefile"
    CUSTOM = "custom"


class TrailCreate(BaseModel):
    name: str | None = None
    trail_type: TrailType = TrailType.CUSTOM
    coordinates: list[list[float]]  # [[lon, lat], ...]
    surface: str | None = None
    difficulty: str | None = None


class TrailResponse(BaseModel):
    id: UUID
    incident_id: UUID | None = None
    name: str | None = None
    trail_type: TrailType
    source: TrailSource
    source_id: str | None = None
    surface: str | None = None
    difficulty: str | None = None
    length_meters: float | None = None
    is_active: bool = True
    created_at: datetime


class TrailGeoJSON(BaseModel):
    type: str = "FeatureCollection"
    features: list[dict]


class JunctionResponse(BaseModel):
    id: UUID
    incident_id: UUID
    lat: float
    lon: float
    trail_count: int
    trail_names: list[str]
    priority_score: float


class OverpassRequest(BaseModel):
    north: float
    south: float
    east: float
    west: float


class ShapefileImportResult(BaseModel):
    trails_imported: int
    errors: list[str]
