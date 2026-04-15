"""GPS data import API endpoints."""

from typing import Annotated
from uuid import UUID

import asyncpg
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel

from app.auth.dependencies import CurrentUser
from app.db.connection import get_pool
from app.db.gps import insert_gps_points, upsert_gps_track
from app.db.incidents import get_incident_by_id
from app.importers.csv_import import parse_csv
from app.importers.fit import parse_fit
from app.importers.geojson import parse_geojson
from app.importers.google_takeout import parse_google_takeout
from app.importers.gpx import parse_gpx
from app.importers.inreach import fetch_inreach_feed
from app.importers.kml import parse_kml, parse_kmz
from app.importers.models import ImportResult

router = APIRouter(prefix="/import", tags=["import"])

PARSERS = {
    "gpx": lambda c: parse_gpx(c),
    "kml": lambda c: parse_kml(c),
    "kmz": lambda c: parse_kmz(c),
    "geojson": lambda c: parse_geojson(c),
    "json": lambda c: parse_geojson(c),
    "fit": lambda c: parse_fit(c),
    "google_takeout": lambda c: parse_google_takeout(c),
    "csv": lambda c: parse_csv(c),
}

EXTENSION_MAP = {
    ".gpx": "gpx",
    ".kml": "kml",
    ".kmz": "kmz",
    ".geojson": "geojson",
    ".json": "geojson",
    ".fit": "fit",
    ".csv": "csv",
}


def _detect_format(filename: str, content: bytes) -> str:
    """Detect file format from extension or content."""
    for ext, fmt in EXTENSION_MAP.items():
        if filename.lower().endswith(ext):
            return fmt

    # Try content-based detection
    text = content[:200].decode("utf-8", errors="ignore").strip()
    if text.startswith("<?xml") or text.startswith("<gpx"):
        return "gpx"
    if "<kml" in text:
        return "kml"
    if text.startswith("{"):
        if '"locations"' in text or '"latitudeE7"' in text or '"timelineObjects"' in text:
            return "google_takeout"
        return "geojson"
    if "," in text.split("\n")[0]:
        return "csv"

    return "unknown"


class ImportPreview(BaseModel):
    format_detected: str
    total_tracks: int
    total_waypoints: int
    total_points: int
    track_names: list[str | None]
    errors: list[str]


class ImportCommit(BaseModel):
    incident_id: UUID
    tag: str | None = None
    source_label: str | None = None


class ImportCommitResponse(BaseModel):
    tracks_imported: int
    points_imported: int
    errors: list[str]


@router.post("/preview", response_model=ImportPreview)
async def preview_import(
    user: CurrentUser,
    file: UploadFile = File(...),
) -> ImportPreview:
    """Upload a GPS file and preview its contents before committing."""
    content = await file.read()
    filename = file.filename or "unknown"

    fmt = _detect_format(filename, content)
    if fmt == "unknown":
        raise HTTPException(
            status_code=422,
            detail=f"Could not detect format for file: {filename}",
        )

    parser = PARSERS.get(fmt)
    if parser is None:
        raise HTTPException(status_code=422, detail=f"Unsupported format: {fmt}")

    result: ImportResult = parser(content)

    return ImportPreview(
        format_detected=result.source_format,
        total_tracks=len(result.tracks),
        total_waypoints=len(result.waypoints),
        total_points=result.total_points,
        track_names=[t.name for t in result.tracks],
        errors=result.errors,
    )


@router.post("/commit", response_model=ImportCommitResponse)
async def commit_import(
    user: CurrentUser,
    pool: Annotated[asyncpg.Pool, Depends(get_pool)],
    file: UploadFile = File(...),
    incident_id: UUID = Form(...),
    tag: str | None = Form(None),
    source_label: str | None = Form(None),
) -> ImportCommitResponse:
    """Parse a GPS file and import tracks into an incident."""
    incident = await get_incident_by_id(pool, incident_id)
    if incident is None:
        raise HTTPException(status_code=404, detail="Incident not found")

    content = await file.read()
    filename = file.filename or "unknown"
    fmt = _detect_format(filename, content)

    parser = PARSERS.get(fmt)
    if parser is None:
        raise HTTPException(status_code=422, detail=f"Unsupported format: {fmt}")

    result: ImportResult = parser(content)
    errors = list(result.errors)
    tracks_imported = 0
    points_imported = 0

    for track in result.tracks:
        if not track.points:
            continue

        track_id = f"import-{incident_id}-{tracks_imported}-{filename}"
        start = track.points[0].timestamp
        end = track.points[-1].timestamp if len(track.points) > 1 else None

        await upsert_gps_track(
            pool,
            track_id=track_id,
            user_id=user["id"],
            incident_id=incident_id,
            team_id=None,
            started_at=start,
            ended_at=end,
            point_count=len(track.points),
        )

        point_tuples = [
            (track_id, p.lat, p.lon, p.altitude, p.accuracy or 0.0, p.timestamp)
            for p in track.points
            if p.timestamp is not None
        ]
        if point_tuples:
            await insert_gps_points(pool, track_id, point_tuples)
            points_imported += len(point_tuples)

        tracks_imported += 1

    return ImportCommitResponse(
        tracks_imported=tracks_imported,
        points_imported=points_imported,
        errors=errors,
    )


class InReachFeedRequest(BaseModel):
    mapshare_url: str
    incident_id: UUID


@router.post("/inreach", response_model=ImportPreview)
async def fetch_inreach(
    body: InReachFeedRequest,
    user: CurrentUser,
    pool: Annotated[asyncpg.Pool, Depends(get_pool)],
) -> ImportPreview:
    """Fetch positions from a Garmin inReach MapShare feed."""
    try:
        result = await fetch_inreach_feed(body.mapshare_url)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Failed to fetch inReach feed: {e}") from e

    return ImportPreview(
        format_detected="inreach",
        total_tracks=len(result.tracks),
        total_waypoints=len(result.waypoints),
        total_points=result.total_points,
        track_names=[t.name for t in result.tracks],
        errors=result.errors,
    )
