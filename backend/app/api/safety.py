import json
from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID

import asyncpg
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.auth.dependencies import CurrentUser
from app.db.connection import get_pool
from app.db.incidents import get_incident_by_id
from app.db.safety import (
    check_geofence,
    create_emergency_alert,
    create_hazard_zone,
    get_unbriefed_teams,
    list_emergency_alerts,
    list_hazard_zones,
    update_emergency_alert_status,
    upsert_safety_briefing,
)
from app.db.teams import get_overdue_teams, list_teams_by_incident
from app.models.safety import (
    BriefingItem,
    EmergencyAlertCreate,
    EmergencyAlertResponse,
    EmergencyAlertUpdate,
    GeofenceCheckResult,
    HazardZoneCreate,
    HazardZoneResponse,
    SafetyBriefingCreate,
    SafetyBriefingResponse,
    SafetyDashboard,
    TurnaroundStatus,
)

router = APIRouter(tags=["safety"])


def _to_hazard_response(row: asyncpg.Record) -> HazardZoneResponse:
    return HazardZoneResponse(
        id=row["id"],
        incident_id=row["incident_id"],
        created_by_user_id=row["created_by_user_id"],
        name=row["name"],
        hazard_type=row["hazard_type"],
        severity=row["severity"],
        description=row["description"],
        center_lat=row["center_lat"],
        center_lon=row["center_lon"],
        radius_meters=row["radius_meters"],
        alert_buffer_meters=row["alert_buffer_meters"],
        is_active=row["is_active"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _to_alert_response(row: asyncpg.Record) -> EmergencyAlertResponse:
    return EmergencyAlertResponse(
        id=row["id"],
        incident_id=row["incident_id"],
        user_id=row["user_id"],
        team_id=row["team_id"],
        lat=row["lat"],
        lon=row["lon"],
        message=row["message"],
        status=row["status"],
        created_at=row["created_at"],
        acknowledged_at=row["acknowledged_at"],
        resolved_at=row["resolved_at"],
    )


# --- Hazard Zones ---


@router.post(
    "/incidents/{incident_id}/hazards",
    response_model=HazardZoneResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_hazard(
    incident_id: UUID,
    body: HazardZoneCreate,
    user: CurrentUser,
    pool: Annotated[asyncpg.Pool, Depends(get_pool)],
) -> HazardZoneResponse:
    incident = await get_incident_by_id(pool, incident_id)
    if incident is None:
        raise HTTPException(status_code=404, detail="Incident not found")

    row = await create_hazard_zone(
        pool,
        incident_id=incident_id,
        created_by_user_id=user["id"],
        name=body.name,
        hazard_type=body.hazard_type,
        severity=body.severity,
        description=body.description,
        center_lat=body.center_lat,
        center_lon=body.center_lon,
        radius_meters=body.radius_meters,
        alert_buffer_meters=body.alert_buffer_meters,
    )
    return _to_hazard_response(row)


@router.get(
    "/incidents/{incident_id}/hazards",
    response_model=list[HazardZoneResponse],
)
async def list_hazards(
    incident_id: UUID,
    user: CurrentUser,
    pool: Annotated[asyncpg.Pool, Depends(get_pool)],
) -> list[HazardZoneResponse]:
    rows = await list_hazard_zones(pool, incident_id)
    return [_to_hazard_response(r) for r in rows]


@router.get(
    "/incidents/{incident_id}/geofence-check",
    response_model=GeofenceCheckResult,
)
async def geofence_check(
    incident_id: UUID,
    lat: float = Query(...),
    lon: float = Query(...),
    user: CurrentUser = None,
    pool: asyncpg.Pool = Depends(get_pool),
) -> GeofenceCheckResult:
    rows = await check_geofence(pool, incident_id, lat, lon)
    return GeofenceCheckResult(
        in_hazard_zone=len(rows) > 0,
        nearby_hazards=[
            {
                "id": str(r["id"]),
                "name": r["name"],
                "hazard_type": r["hazard_type"],
                "severity": r["severity"],
            }
            for r in rows
        ],
    )


# --- Emergency Alerts ---


@router.post(
    "/incidents/{incident_id}/emergency",
    response_model=EmergencyAlertResponse,
    status_code=status.HTTP_201_CREATED,
)
async def send_emergency_alert(
    incident_id: UUID,
    body: EmergencyAlertCreate,
    user: CurrentUser,
    pool: Annotated[asyncpg.Pool, Depends(get_pool)],
) -> EmergencyAlertResponse:
    row = await create_emergency_alert(
        pool,
        incident_id=incident_id,
        user_id=user["id"],
        lat=body.lat,
        lon=body.lon,
        message=body.message,
        team_id=body.team_id,
    )
    return _to_alert_response(row)


@router.get(
    "/incidents/{incident_id}/emergency",
    response_model=list[EmergencyAlertResponse],
)
async def list_alerts(
    incident_id: UUID,
    user: CurrentUser,
    pool: Annotated[asyncpg.Pool, Depends(get_pool)],
    alert_status: str | None = Query(None, alias="status"),
) -> list[EmergencyAlertResponse]:
    rows = await list_emergency_alerts(pool, incident_id, status=alert_status)
    return [_to_alert_response(r) for r in rows]


@router.patch(
    "/emergency/{alert_id}",
    response_model=EmergencyAlertResponse,
)
async def update_alert(
    alert_id: UUID,
    body: EmergencyAlertUpdate,
    user: CurrentUser,
    pool: Annotated[asyncpg.Pool, Depends(get_pool)],
) -> EmergencyAlertResponse:
    row = await update_emergency_alert_status(pool, alert_id, body.status)
    if row is None:
        raise HTTPException(status_code=404, detail="Alert not found")
    return _to_alert_response(row)


# --- Safety Briefings ---


@router.post(
    "/incidents/{incident_id}/briefings",
    response_model=SafetyBriefingResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_briefing(
    incident_id: UUID,
    body: SafetyBriefingCreate,
    user: CurrentUser,
    pool: Annotated[asyncpg.Pool, Depends(get_pool)],
) -> SafetyBriefingResponse:
    all_checked = all(item.checked for item in body.items)
    items_json = json.dumps([item.model_dump() for item in body.items])

    row = await upsert_safety_briefing(
        pool,
        incident_id=incident_id,
        team_id=body.team_id,
        briefed_by_user_id=user["id"],
        items_json=items_json,
        all_checked=all_checked,
    )

    items_data = row["items"] if isinstance(row["items"], list) else json.loads(row["items"])

    return SafetyBriefingResponse(
        id=row["id"],
        incident_id=row["incident_id"],
        team_id=row["team_id"],
        briefed_by_user_id=row["briefed_by_user_id"],
        items=[BriefingItem(**i) for i in items_data],
        all_items_checked=row["all_items_checked"],
        briefed_at=row["briefed_at"],
    )


# --- Turnaround Status ---


@router.get(
    "/incidents/{incident_id}/turnaround",
    response_model=list[TurnaroundStatus],
)
async def get_turnaround_status(
    incident_id: UUID,
    user: CurrentUser,
    pool: Annotated[asyncpg.Pool, Depends(get_pool)],
) -> list[TurnaroundStatus]:
    teams = await list_teams_by_incident(pool, incident_id)
    now = datetime.now(UTC)
    results = []
    for t in teams:
        if t["status"] not in ("deployed", "returning"):
            continue
        ta = t["turnaround_time"]
        is_past = ta is not None and ta < now
        minutes_remaining = None
        if ta is not None and not is_past:
            minutes_remaining = (ta - now).total_seconds() / 60
        results.append(
            TurnaroundStatus(
                team_id=t["id"],
                team_name=t["name"],
                turnaround_time=ta,
                is_past_turnaround=is_past,
                minutes_remaining=minutes_remaining,
            )
        )
    return results


# --- Safety Officer Dashboard ---


@router.get(
    "/incidents/{incident_id}/safety-dashboard",
    response_model=SafetyDashboard,
)
async def safety_dashboard(
    incident_id: UUID,
    user: CurrentUser,
    pool: Annotated[asyncpg.Pool, Depends(get_pool)],
) -> SafetyDashboard:
    hazards = await list_hazard_zones(pool, incident_id)
    alerts = await list_emergency_alerts(pool, incident_id, status="active")
    overdue = await get_overdue_teams(pool, incident_id)
    unbriefed = await get_unbriefed_teams(pool, incident_id)

    # Check turnaround times
    teams = await list_teams_by_incident(pool, incident_id)
    now = datetime.now(UTC)
    past_turnaround = sum(
        1
        for t in teams
        if t["turnaround_time"] is not None
        and t["turnaround_time"] < now
        and t["status"] in ("deployed", "returning")
    )

    return SafetyDashboard(
        active_hazard_zones=len(hazards),
        active_emergency_alerts=len(alerts),
        teams_past_turnaround=past_turnaround,
        teams_overdue_checkin=len(overdue),
        teams_without_briefing=len(unbriefed),
        unbriefed_team_names=[r["name"] for r in unbriefed],
    )
