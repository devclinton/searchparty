"""Trail data API endpoints."""

import math
from typing import Annotated
from uuid import UUID

import asyncpg
from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status

from app.auth.dependencies import CurrentUser
from app.db.connection import get_pool
from app.db.trails import (
    bulk_insert_trails,
    create_junction,
    create_trail,
    list_junctions_by_incident,
    list_trails_by_bbox,
    list_trails_by_incident,
)
from app.importers.osm_trails import coords_to_wkt, fetch_osm_trails
from app.importers.shapefile import parse_shapefile_zip
from app.models.trail import (
    JunctionResponse,
    OverpassRequest,
    ShapefileImportResult,
    TrailCreate,
    TrailGeoJSON,
    TrailResponse,
)

router = APIRouter(prefix="/trails", tags=["trails"])


def _to_trail_response(row: asyncpg.Record) -> TrailResponse:
    return TrailResponse(
        id=row["id"],
        incident_id=row["incident_id"],
        name=row["name"],
        trail_type=row["trail_type"],
        source=row["source"],
        source_id=row["source_id"],
        surface=row["surface"],
        difficulty=row["difficulty"],
        length_meters=row["length_meters"],
        is_active=row["is_active"],
        created_at=row["created_at"],
    )


def _trails_to_geojson(rows: list[asyncpg.Record]) -> TrailGeoJSON:
    features = []
    for r in rows:
        geojson = r.get("geojson")
        if geojson is None:
            continue
        features.append(
            {
                "type": "Feature",
                "properties": {
                    "id": str(r["id"]),
                    "name": r["name"],
                    "trail_type": r["trail_type"],
                    "source": r["source"],
                    "surface": r["surface"],
                    "difficulty": r["difficulty"],
                    "length_meters": r["length_meters"],
                },
                "geometry": geojson,
            }
        )
    return TrailGeoJSON(features=features)


# --- Trail CRUD ---


@router.post(
    "/incidents/{incident_id}/custom",
    response_model=TrailResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_custom_trail(
    incident_id: UUID,
    body: TrailCreate,
    user: CurrentUser,
    pool: Annotated[asyncpg.Pool, Depends(get_pool)],
) -> TrailResponse:
    """Draw a custom trail on the map."""
    if len(body.coordinates) < 2:
        raise HTTPException(status_code=422, detail="Trail must have at least 2 points")

    wkt = coords_to_wkt(body.coordinates)
    row = await create_trail(
        pool,
        incident_id=incident_id,
        name=body.name,
        trail_type=body.trail_type,
        source="custom",
        geometry_wkt=wkt,
        surface=body.surface,
        difficulty=body.difficulty,
    )
    return _to_trail_response(row)


@router.get("/incidents/{incident_id}", response_model=TrailGeoJSON)
async def get_incident_trails_geojson(
    incident_id: UUID,
    user: CurrentUser,
    pool: Annotated[asyncpg.Pool, Depends(get_pool)],
) -> TrailGeoJSON:
    """Get all trails for an incident as GeoJSON."""
    rows = await list_trails_by_incident(pool, incident_id)
    return _trails_to_geojson(rows)


@router.get("/bbox", response_model=TrailGeoJSON)
async def get_trails_by_bbox(
    north: float = Query(...),
    south: float = Query(...),
    east: float = Query(...),
    west: float = Query(...),
    incident_id: UUID | None = Query(None),
    user: CurrentUser = None,
    pool: asyncpg.Pool = Depends(get_pool),
) -> TrailGeoJSON:
    """Get trails within a bounding box as GeoJSON."""
    rows = await list_trails_by_bbox(pool, north, south, east, west, incident_id)
    return _trails_to_geojson(rows)


# --- OSM Import ---


@router.post("/incidents/{incident_id}/fetch-osm")
async def fetch_osm_trail_data(
    incident_id: UUID,
    body: OverpassRequest,
    user: CurrentUser,
    pool: Annotated[asyncpg.Pool, Depends(get_pool)],
) -> dict:
    """Fetch trails from OpenStreetMap Overpass API and import them."""
    try:
        osm_trails = await fetch_osm_trails(body.north, body.south, body.east, body.west)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Overpass API error: {e}") from e

    if not osm_trails:
        return {"imported": 0, "message": "No trails found in the area"}

    trail_tuples = [
        (
            incident_id,
            t.name,
            t.trail_type,
            "osm",
            t.osm_id,
            coords_to_wkt(t.coordinates),
            t.surface,
            t.difficulty,
        )
        for t in osm_trails
        if len(t.coordinates) >= 2
    ]

    count = await bulk_insert_trails(pool, trail_tuples)
    return {"imported": count, "message": f"Imported {count} trails from OSM"}


# --- Shapefile Import ---


@router.post(
    "/incidents/{incident_id}/import-shapefile",
    response_model=ShapefileImportResult,
)
async def import_shapefile(
    incident_id: UUID,
    user: CurrentUser,
    pool: Annotated[asyncpg.Pool, Depends(get_pool)],
    file: UploadFile = File(...),
    source: str = Form("shapefile"),
) -> ShapefileImportResult:
    """Import trails from an ESRI Shapefile zip archive."""
    content = await file.read()
    errors: list[str] = []

    try:
        shp_trails = parse_shapefile_zip(content, source)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Shapefile parse error: {e}") from e

    if not shp_trails:
        return ShapefileImportResult(trails_imported=0, errors=["No trails found"])

    trail_tuples = []
    for t in shp_trails:
        if len(t.coordinates) < 2:
            continue
        wkt = coords_to_wkt(t.coordinates)
        trail_tuples.append((incident_id, t.name, t.trail_type, source, None, wkt, None, None))

    count = await bulk_insert_trails(pool, trail_tuples)
    return ShapefileImportResult(trails_imported=count, errors=errors)


# --- Junction Detection ---


@router.post("/incidents/{incident_id}/detect-junctions")
async def detect_junctions(
    incident_id: UUID,
    user: CurrentUser,
    pool: Annotated[asyncpg.Pool, Depends(get_pool)],
    tolerance_meters: float = Query(20.0),
) -> dict:
    """Detect trail intersections and create junction points.

    Junctions are high-priority areas for hasty searches because
    lost persons often make navigation errors at decision points.
    """
    rows = await list_trails_by_incident(pool, incident_id)

    # Extract all trail endpoints and midpoints to find intersections
    # Simple approach: collect all trail vertices, cluster nearby ones
    all_points: list[dict] = []
    for row in rows:
        geojson = row.get("geojson")
        if geojson is None:
            continue
        coords = geojson.get("coordinates", [])
        trail_name = row["name"] or "Unnamed"
        for c in coords:
            if len(c) >= 2:
                all_points.append({"lon": c[0], "lat": c[1], "trail_name": trail_name})

    # Simple clustering: group points within tolerance
    tolerance_deg = tolerance_meters / 111320.0
    junctions_found = 0
    visited = set()

    for i, p in enumerate(all_points):
        if i in visited:
            continue
        cluster = [p]
        trail_names = {p["trail_name"]}
        for j, q in enumerate(all_points):
            if j <= i or j in visited:
                continue
            dist = math.sqrt((p["lat"] - q["lat"]) ** 2 + (p["lon"] - q["lon"]) ** 2)
            if dist < tolerance_deg:
                cluster.append(q)
                trail_names.add(q["trail_name"])
                visited.add(j)

        # Only create junctions where 2+ different trails meet
        if len(trail_names) >= 2:
            avg_lat = sum(c["lat"] for c in cluster) / len(cluster)
            avg_lon = sum(c["lon"] for c in cluster) / len(cluster)
            priority = len(trail_names) * 10.0  # More trails = higher priority

            await create_junction(
                pool,
                incident_id=incident_id,
                lat=avg_lat,
                lon=avg_lon,
                trail_count=len(trail_names),
                trail_names=sorted(trail_names),
                priority_score=priority,
            )
            junctions_found += 1

    return {"junctions_detected": junctions_found}


@router.get(
    "/incidents/{incident_id}/junctions",
    response_model=list[JunctionResponse],
)
async def get_junctions(
    incident_id: UUID,
    user: CurrentUser,
    pool: Annotated[asyncpg.Pool, Depends(get_pool)],
) -> list[JunctionResponse]:
    rows = await list_junctions_by_incident(pool, incident_id)
    return [
        JunctionResponse(
            id=r["id"],
            incident_id=r["incident_id"],
            lat=r["lat"],
            lon=r["lon"],
            trail_count=r["trail_count"],
            trail_names=r["trail_names"] or [],
            priority_score=r["priority_score"],
        )
        for r in rows
    ]
