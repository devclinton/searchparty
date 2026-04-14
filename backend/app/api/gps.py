from typing import Annotated
from uuid import UUID

import asyncpg
from fastapi import APIRouter, Depends, status

from app.auth.dependencies import CurrentUser
from app.db.connection import get_pool
from app.db.gps import (
    get_latest_positions,
    get_track_points,
    get_tracks_by_incident,
    insert_gps_points,
    upsert_gps_track,
)
from app.models.gps import (
    GpsPointResponse,
    GpsTrackResponse,
    GpsTrackUpload,
)

router = APIRouter(prefix="/gps", tags=["gps"])


@router.post("/tracks", response_model=GpsTrackResponse, status_code=status.HTTP_201_CREATED)
async def upload_track(
    body: GpsTrackUpload,
    user: CurrentUser,
    pool: Annotated[asyncpg.Pool, Depends(get_pool)],
) -> GpsTrackResponse:
    track = await upsert_gps_track(
        pool,
        track_id=body.track_id,
        user_id=user["id"],
        incident_id=body.incident_id,
        team_id=body.team_id,
        started_at=body.started_at,
        ended_at=body.ended_at,
        point_count=len(body.points),
    )

    if body.points:
        point_tuples = [
            (
                body.track_id,
                p.lat,
                p.lon,
                p.altitude,
                p.accuracy,
                p.timestamp,
            )
            for p in body.points
        ]
        await insert_gps_points(pool, body.track_id, point_tuples)

    return GpsTrackResponse(
        id=track["id"],
        user_id=track["user_id"],
        incident_id=track["incident_id"],
        team_id=track["team_id"],
        started_at=track["started_at"],
        ended_at=track["ended_at"],
        point_count=track["point_count"],
        created_at=track["created_at"],
    )


@router.get(
    "/incidents/{incident_id}/tracks",
    response_model=list[GpsTrackResponse],
)
async def list_incident_tracks(
    incident_id: UUID,
    user: CurrentUser,
    pool: Annotated[asyncpg.Pool, Depends(get_pool)],
) -> list[GpsTrackResponse]:
    rows = await get_tracks_by_incident(pool, incident_id)
    return [
        GpsTrackResponse(
            id=r["id"],
            user_id=r["user_id"],
            incident_id=r["incident_id"],
            team_id=r["team_id"],
            started_at=r["started_at"],
            ended_at=r["ended_at"],
            point_count=r["point_count"],
            created_at=r["created_at"],
        )
        for r in rows
    ]


@router.get("/tracks/{track_id}/points", response_model=list[GpsPointResponse])
async def get_points(
    track_id: str,
    user: CurrentUser,
    pool: Annotated[asyncpg.Pool, Depends(get_pool)],
) -> list[GpsPointResponse]:
    rows = await get_track_points(pool, track_id)
    return [
        GpsPointResponse(
            lat=r["lat"],
            lon=r["lon"],
            altitude=r["altitude"],
            accuracy=r["accuracy"],
            recorded_at=r["recorded_at"],
        )
        for r in rows
    ]


@router.get("/incidents/{incident_id}/positions")
async def get_team_positions(
    incident_id: UUID,
    user: CurrentUser,
    pool: Annotated[asyncpg.Pool, Depends(get_pool)],
) -> list[dict]:
    rows = await get_latest_positions(pool, incident_id)
    return [
        {
            "user_id": str(r["user_id"]),
            "display_name": r["display_name"],
            "team_name": r["team_name"] or "Unassigned",
            "role": r["role"] or "searcher",
            "lat": r["lat"],
            "lon": r["lon"],
            "accuracy": r["accuracy"],
            "timestamp": r["recorded_at"].isoformat(),
        }
        for r in rows
    ]
