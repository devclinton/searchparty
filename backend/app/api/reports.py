"""Reporting and analytics API endpoints."""

from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID

import asyncpg
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import PlainTextResponse

from app.auth.dependencies import CurrentUser
from app.db.connection import get_pool
from app.db.gps import get_track_points, get_tracks_by_incident
from app.db.incidents import get_incident_by_id, list_incidents
from app.db.safety import list_hazard_zones
from app.db.search import get_coverage_stats, list_clues_by_incident, list_segments_by_incident
from app.db.teams import list_team_members, list_teams_by_incident
from app.db.users import get_user_by_id
from app.models.reports import (
    IncidentActionPlan,
    OperationSummary,
    TeamPerformance,
)

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/incidents/{incident_id}/summary", response_model=OperationSummary)
async def get_operation_summary(
    incident_id: UUID,
    user: CurrentUser,
    pool: Annotated[asyncpg.Pool, Depends(get_pool)],
) -> OperationSummary:
    incident = await get_incident_by_id(pool, incident_id)
    if incident is None:
        raise HTTPException(status_code=404, detail="Incident not found")

    teams = await list_teams_by_incident(pool, incident_id)
    coverage = await get_coverage_stats(pool, incident_id)
    clues = await list_clues_by_incident(pool, incident_id)
    tracks = await get_tracks_by_incident(pool, incident_id)

    # Count unique personnel across all teams
    all_members = []
    for t in teams:
        members = await list_team_members(pool, t["id"])
        all_members.extend(members)
    unique_users = {str(m["user_id"]) for m in all_members}

    duration = None
    if incident["closed_at"] and incident["created_at"]:
        delta = incident["closed_at"] - incident["created_at"]
        duration = delta.total_seconds() / 3600

    return OperationSummary(
        incident_id=incident["id"],
        incident_name=incident["name"],
        status=incident["status"],
        created_at=incident["created_at"],
        closed_at=incident["closed_at"],
        duration_hours=duration,
        total_teams=len(teams),
        total_personnel=len(unique_users),
        total_segments=coverage["total_segments"] if coverage else 0,
        segments_completed=coverage["segments_completed"] if coverage else 0,
        total_area_sq_meters=float(coverage["total_area_sq_meters"]) if coverage else 0,
        average_pod=float(coverage["average_pod"]) if coverage else 0,
        total_clues=len(clues),
        total_gps_tracks=len(tracks),
    )


@router.get(
    "/incidents/{incident_id}/team-performance",
    response_model=list[TeamPerformance],
)
async def get_team_performance(
    incident_id: UUID,
    user: CurrentUser,
    pool: Annotated[asyncpg.Pool, Depends(get_pool)],
) -> list[TeamPerformance]:
    incident = await get_incident_by_id(pool, incident_id)
    if incident is None:
        raise HTTPException(status_code=404, detail="Incident not found")

    teams = await list_teams_by_incident(pool, incident_id)
    segments = await list_segments_by_incident(pool, incident_id)
    clues = await list_clues_by_incident(pool, incident_id)

    results = []
    for t in teams:
        members = await list_team_members(pool, t["id"])
        team_segments = [s for s in segments if s.get("assigned_team_id") == t["id"]]
        team_clues = [c for c in clues if c.get("found_by_team_id") == t["id"]]

        deployed_hours = None
        if t["deployed_at"]:
            end = t.get("updated_at") or datetime.now(UTC)
            deployed_hours = (end - t["deployed_at"]).total_seconds() / 3600

        results.append(
            TeamPerformance(
                team_id=t["id"],
                team_name=t["name"],
                status=t["status"],
                members_count=len(members),
                segments_assigned=len(team_segments),
                total_check_ins=0,  # Would need check-in log table
                deployed_duration_hours=deployed_hours,
                clues_found=len(team_clues),
            )
        )
    return results


@router.get("/incidents/{incident_id}/gpx/{track_id}")
async def export_track_gpx(
    incident_id: UUID,
    track_id: str,
    user: CurrentUser,
    pool: Annotated[asyncpg.Pool, Depends(get_pool)],
) -> PlainTextResponse:
    """Export a GPS track as GPX XML."""
    points = await get_track_points(pool, track_id)
    if not points:
        raise HTTPException(status_code=404, detail="Track not found")

    gpx_points = []
    for p in points:
        ele = f"<ele>{p['altitude']}</ele>" if p.get("altitude") else ""
        time = p["recorded_at"].strftime("%Y-%m-%dT%H:%M:%SZ")
        gpx_points.append(
            f'      <trkpt lat="{p["lat"]}" lon="{p["lon"]}">{ele}<time>{time}</time></trkpt>'
        )

    gpx = f"""<?xml version="1.0" encoding="UTF-8"?>
<gpx version="1.1" creator="SearchParty">
  <trk>
    <name>{track_id}</name>
    <trkseg>
{chr(10).join(gpx_points)}
    </trkseg>
  </trk>
</gpx>"""

    return PlainTextResponse(
        content=gpx,
        media_type="application/gpx+xml",
        headers={"Content-Disposition": f'attachment; filename="{track_id}.gpx"'},
    )


@router.get("/incidents/{incident_id}/clues.csv")
async def export_clues_csv(
    incident_id: UUID,
    user: CurrentUser,
    pool: Annotated[asyncpg.Pool, Depends(get_pool)],
) -> PlainTextResponse:
    """Export clues as CSV."""
    clues = await list_clues_by_incident(pool, incident_id)

    lines = ["id,lat,lon,type,description,found_at"]
    for c in clues:
        desc = str(c["description"]).replace('"', '""')
        lines.append(f'{c["id"]},{c["lat"]},{c["lon"]},{c["clue_type"]},"{desc}",{c["found_at"]}')

    return PlainTextResponse(
        content="\n".join(lines),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="clues-{incident_id}.csv"'},
    )


@router.get("/incidents/{incident_id}/iap", response_model=IncidentActionPlan)
async def get_incident_action_plan(
    incident_id: UUID,
    user: CurrentUser,
    pool: Annotated[asyncpg.Pool, Depends(get_pool)],
) -> IncidentActionPlan:
    """Generate a printable Incident Action Plan."""
    incident = await get_incident_by_id(pool, incident_id)
    if incident is None:
        raise HTTPException(status_code=404, detail="Incident not found")

    teams = await list_teams_by_incident(pool, incident_id)
    hazards = await list_hazard_zones(pool, incident_id)
    segments = await list_segments_by_incident(pool, incident_id)

    ic_name = "Unknown"
    if incident["incident_commander_id"]:
        ic_user = await get_user_by_id(pool, incident["incident_commander_id"])
        if ic_user:
            ic_name = ic_user["display_name"]

    subject_info = {
        "name": incident["subject_name"],
        "age_category": incident["subject_age_category"],
        "activity": incident["subject_activity"],
        "condition": incident["subject_condition"],
        "clothing": incident["subject_clothing"],
        "medical_needs": incident["subject_medical_needs"],
    }

    ipp = None
    if incident["ipp_lat"] is not None:
        ipp = {"lat": incident["ipp_lat"], "lon": incident["ipp_lon"]}

    return IncidentActionPlan(
        incident_name=incident["name"],
        incident_commander=ic_name,
        status=incident["status"],
        created_at=incident["created_at"].isoformat(),
        subject_info=subject_info,
        ipp=ipp,
        teams=[
            {
                "name": t["name"],
                "status": t["status"],
                "search_type": t["search_type"],
                "check_in_interval": t["check_in_interval_minutes"],
            }
            for t in teams
        ],
        hazards=[
            {
                "name": h["name"],
                "type": h["hazard_type"],
                "severity": h["severity"],
            }
            for h in hazards
        ],
        segments=[
            {
                "name": s["name"],
                "status": s["status"],
                "pod": float(s["pod"]) if s.get("pod") else 0,
                "passes": s.get("passes", 0),
            }
            for s in segments
        ],
        communication_plan="Check-in every 30 minutes on assigned radio channel.",
        safety_message=(
            "All teams must complete safety briefing before deployment. "
            "Report all hazards immediately. Do not enter marked danger zones."
        ),
    )


@router.get("/incidents/archive", response_model=list[OperationSummary])
async def list_archived_operations(
    user: CurrentUser,
    pool: Annotated[asyncpg.Pool, Depends(get_pool)],
) -> list[OperationSummary]:
    """List closed incidents as archived operations."""
    incidents = await list_incidents(pool, status="closed", limit=100, offset=0)
    results = []
    for inc in incidents:
        duration = None
        if inc["closed_at"] and inc["created_at"]:
            delta = inc["closed_at"] - inc["created_at"]
            duration = delta.total_seconds() / 3600

        results.append(
            OperationSummary(
                incident_id=inc["id"],
                incident_name=inc["name"],
                status=inc["status"],
                created_at=inc["created_at"],
                closed_at=inc["closed_at"],
                duration_hours=duration,
                total_teams=0,
                total_personnel=0,
                total_segments=0,
                segments_completed=0,
                total_area_sq_meters=0,
                average_pod=0,
                total_clues=0,
                total_gps_tracks=0,
            )
        )
    return results
