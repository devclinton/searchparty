from typing import Annotated
from uuid import UUID

import asyncpg
from fastapi import APIRouter, Depends, HTTPException, status

from app.auth.dependencies import CurrentUser
from app.db.connection import get_pool
from app.db.incidents import get_incident_by_id
from app.db.search import (
    create_clue,
    create_segment,
    get_coverage_stats,
    get_segment_by_id,
    list_clues_by_incident,
    list_segments_by_incident,
    record_search_pass,
    update_segment,
)
from app.models.search import (
    ClueCreate,
    ClueResponse,
    CoverageStats,
    SegmentCreate,
    SegmentRecordPass,
    SegmentResponse,
    SegmentUpdate,
    calculate_pod,
    coverage_from_esw,
)

router = APIRouter(tags=["search"])


def _polygon_to_wkt(coords: list[list[float]]) -> str:
    """Convert [[lon, lat], ...] to WKT POLYGON string."""
    # Close the ring if not already closed
    if coords[0] != coords[-1]:
        coords = [*coords, coords[0]]
    points = ", ".join(f"{c[0]} {c[1]}" for c in coords)
    return f"POLYGON(({points}))"


def _to_segment_response(row: asyncpg.Record) -> SegmentResponse:
    return SegmentResponse(
        id=row["id"],
        incident_id=row["incident_id"],
        name=row["name"],
        search_type=row["search_type"],
        assigned_team_id=row["assigned_team_id"],
        area_sq_meters=row["area_sq_meters"],
        grid_spacing_meters=row["grid_spacing_meters"],
        esw_meters=row["esw_meters"],
        coverage=row["coverage"],
        pod=row["pod"],
        passes=row["passes"],
        status=row["status"],
        priority=row["priority"],
        notes=row["notes"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


# --- Segments ---


@router.post(
    "/incidents/{incident_id}/segments",
    response_model=SegmentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_search_segment(
    incident_id: UUID,
    body: SegmentCreate,
    user: CurrentUser,
    pool: Annotated[asyncpg.Pool, Depends(get_pool)],
) -> SegmentResponse:
    incident = await get_incident_by_id(pool, incident_id)
    if incident is None:
        raise HTTPException(status_code=404, detail="Incident not found")

    if len(body.polygon) < 3:
        raise HTTPException(status_code=422, detail="Polygon must have at least 3 points")

    wkt = _polygon_to_wkt(body.polygon)
    row = await create_segment(
        pool,
        incident_id=incident_id,
        name=body.name,
        search_type=body.search_type,
        polygon_wkt=wkt,
        grid_spacing_meters=body.grid_spacing_meters,
        esw_meters=body.esw_meters,
        priority=body.priority,
        notes=body.notes,
    )
    return _to_segment_response(row)


@router.get(
    "/incidents/{incident_id}/segments",
    response_model=list[SegmentResponse],
)
async def list_search_segments(
    incident_id: UUID,
    user: CurrentUser,
    pool: Annotated[asyncpg.Pool, Depends(get_pool)],
) -> list[SegmentResponse]:
    rows = await list_segments_by_incident(pool, incident_id)
    return [_to_segment_response(r) for r in rows]


@router.get(
    "/segments/{segment_id}",
    response_model=SegmentResponse,
)
async def get_search_segment(
    segment_id: UUID,
    user: CurrentUser,
    pool: Annotated[asyncpg.Pool, Depends(get_pool)],
) -> SegmentResponse:
    row = await get_segment_by_id(pool, segment_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Segment not found")
    return _to_segment_response(row)


@router.patch(
    "/segments/{segment_id}",
    response_model=SegmentResponse,
)
async def update_search_segment(
    segment_id: UUID,
    body: SegmentUpdate,
    user: CurrentUser,
    pool: Annotated[asyncpg.Pool, Depends(get_pool)],
) -> SegmentResponse:
    existing = await get_segment_by_id(pool, segment_id)
    if existing is None:
        raise HTTPException(status_code=404, detail="Segment not found")

    fields = body.model_dump(exclude_none=True)
    row = await update_segment(pool, segment_id, **fields)
    if row is None:
        raise HTTPException(status_code=404, detail="Segment not found")
    return _to_segment_response(row)


@router.post(
    "/segments/{segment_id}/pass",
    response_model=SegmentResponse,
)
async def record_segment_pass(
    segment_id: UUID,
    body: SegmentRecordPass,
    user: CurrentUser,
    pool: Annotated[asyncpg.Pool, Depends(get_pool)],
) -> SegmentResponse:
    """Record a search pass and update POD for the segment."""
    existing = await get_segment_by_id(pool, segment_id)
    if existing is None:
        raise HTTPException(status_code=404, detail="Segment not found")

    area = existing["area_sq_meters"] or 0.0
    if area <= 0:
        raise HTTPException(status_code=422, detail="Segment has no area computed")

    new_coverage = coverage_from_esw(body.esw_meters, body.distance_traveled_meters, area)
    new_pod = calculate_pod(new_coverage)

    row = await record_search_pass(
        pool,
        segment_id,
        new_coverage=new_coverage,
        new_pod=new_pod,
    )
    if row is None:
        raise HTTPException(status_code=404, detail="Segment not found")
    return _to_segment_response(row)


# --- Coverage Stats ---


@router.get(
    "/incidents/{incident_id}/coverage",
    response_model=CoverageStats,
)
async def get_incident_coverage(
    incident_id: UUID,
    user: CurrentUser,
    pool: Annotated[asyncpg.Pool, Depends(get_pool)],
) -> CoverageStats:
    row = await get_coverage_stats(pool, incident_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Incident not found")
    return CoverageStats(
        total_segments=row["total_segments"],
        segments_completed=row["segments_completed"],
        segments_in_progress=row["segments_in_progress"],
        total_area_sq_meters=float(row["total_area_sq_meters"]),
        searched_area_sq_meters=float(row["searched_area_sq_meters"]),
        average_pod=float(row["average_pod"]),
        overall_coverage_percent=float(row["overall_coverage_percent"]),
    )


# --- Clues ---


@router.post(
    "/incidents/{incident_id}/clues",
    response_model=ClueResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_new_clue(
    incident_id: UUID,
    body: ClueCreate,
    user: CurrentUser,
    pool: Annotated[asyncpg.Pool, Depends(get_pool)],
) -> ClueResponse:
    incident = await get_incident_by_id(pool, incident_id)
    if incident is None:
        raise HTTPException(status_code=404, detail="Incident not found")

    row = await create_clue(
        pool,
        incident_id=incident_id,
        found_by_user_id=user["id"],
        lat=body.lat,
        lon=body.lon,
        description=body.description,
        clue_type=body.clue_type,
        segment_id=body.segment_id,
        found_by_team_id=body.team_id,
        photo_url=body.photo_url,
    )
    return ClueResponse(
        id=row["id"],
        incident_id=row["incident_id"],
        segment_id=row["segment_id"],
        found_by_user_id=row["found_by_user_id"],
        found_by_team_id=row["found_by_team_id"],
        lat=row["lat"],
        lon=row["lon"],
        description=row["description"],
        clue_type=row["clue_type"],
        photo_url=row["photo_url"],
        found_at=row["found_at"],
        created_at=row["created_at"],
    )


@router.get(
    "/incidents/{incident_id}/clues",
    response_model=list[ClueResponse],
)
async def list_incident_clues(
    incident_id: UUID,
    user: CurrentUser,
    pool: Annotated[asyncpg.Pool, Depends(get_pool)],
) -> list[ClueResponse]:
    rows = await list_clues_by_incident(pool, incident_id)
    return [
        ClueResponse(
            id=r["id"],
            incident_id=r["incident_id"],
            segment_id=r["segment_id"],
            found_by_user_id=r["found_by_user_id"],
            found_by_team_id=r["found_by_team_id"],
            lat=r["lat"],
            lon=r["lon"],
            description=r["description"],
            clue_type=r["clue_type"],
            photo_url=r["photo_url"],
            found_at=r["found_at"],
            created_at=r["created_at"],
        )
        for r in rows
    ]
