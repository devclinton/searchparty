from typing import Annotated
from uuid import UUID

import asyncpg
from fastapi import APIRouter, Depends, HTTPException, status

from app.auth.dependencies import CurrentUser
from app.db.connection import get_pool
from app.db.incidents import get_incident_by_id
from app.db.teams import (
    add_team_member,
    create_team,
    dispatch_assignment,
    get_accountability_board,
    get_overdue_teams,
    get_team_by_id,
    list_team_members,
    list_teams_by_incident,
    record_check_in,
    remove_team_member,
    update_team_status,
)
from app.models.team import (
    AccountabilityEntry,
    AssignmentDispatch,
    TeamCreate,
    TeamMemberAdd,
    TeamMemberResponse,
    TeamResponse,
    TeamStatus,
    TeamStatusUpdate,
)
from app.models.user import ICSRole

router = APIRouter(prefix="/incidents/{incident_id}/teams", tags=["teams"])


def _to_team_response(row: asyncpg.Record) -> TeamResponse:
    return TeamResponse(
        id=row["id"],
        incident_id=row["incident_id"],
        name=row["name"],
        status=TeamStatus(row["status"]),
        leader_id=row["leader_id"],
        search_type=row["search_type"],
        check_in_interval_minutes=row["check_in_interval_minutes"],
        last_check_in_at=row["last_check_in_at"],
        deployed_at=row["deployed_at"],
        turnaround_time=row["turnaround_time"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _to_member_response(row: asyncpg.Record) -> TeamMemberResponse:
    return TeamMemberResponse(
        id=row["id"],
        team_id=row["team_id"],
        user_id=row["user_id"],
        role=ICSRole(row["role"]),
        signed_in_at=row["signed_in_at"],
        signed_out_at=row["signed_out_at"],
    )


async def _verify_incident(pool: asyncpg.Pool, incident_id: UUID) -> asyncpg.Record:
    incident = await get_incident_by_id(pool, incident_id)
    if incident is None:
        raise HTTPException(status_code=404, detail="Incident not found")
    return incident


async def _verify_team(pool: asyncpg.Pool, team_id: UUID, incident_id: UUID) -> asyncpg.Record:
    team = await get_team_by_id(pool, team_id)
    if team is None or team["incident_id"] != incident_id:
        raise HTTPException(status_code=404, detail="Team not found")
    return team


# --- Team CRUD ---


@router.post("", response_model=TeamResponse, status_code=status.HTTP_201_CREATED)
async def create_new_team(
    incident_id: UUID,
    body: TeamCreate,
    user: CurrentUser,
    pool: Annotated[asyncpg.Pool, Depends(get_pool)],
) -> TeamResponse:
    await _verify_incident(pool, incident_id)
    row = await create_team(
        pool,
        incident_id=incident_id,
        name=body.name,
        search_type=body.search_type,
        check_in_interval_minutes=body.check_in_interval_minutes,
    )
    return _to_team_response(row)


@router.get("", response_model=list[TeamResponse])
async def list_incident_teams(
    incident_id: UUID,
    user: CurrentUser,
    pool: Annotated[asyncpg.Pool, Depends(get_pool)],
) -> list[TeamResponse]:
    await _verify_incident(pool, incident_id)
    rows = await list_teams_by_incident(pool, incident_id)
    return [_to_team_response(r) for r in rows]


@router.get("/{team_id}", response_model=TeamResponse)
async def get_team(
    incident_id: UUID,
    team_id: UUID,
    user: CurrentUser,
    pool: Annotated[asyncpg.Pool, Depends(get_pool)],
) -> TeamResponse:
    team = await _verify_team(pool, team_id, incident_id)
    return _to_team_response(team)


# --- Team Status ---


@router.post("/{team_id}/status", response_model=TeamResponse)
async def change_team_status(
    incident_id: UUID,
    team_id: UUID,
    body: TeamStatusUpdate,
    user: CurrentUser,
    pool: Annotated[asyncpg.Pool, Depends(get_pool)],
) -> TeamResponse:
    await _verify_team(pool, team_id, incident_id)
    row = await update_team_status(pool, team_id, body.status)
    if row is None:
        raise HTTPException(status_code=404, detail="Team not found")
    return _to_team_response(row)


# --- Assignment Dispatch ---


@router.post("/{team_id}/dispatch", response_model=TeamResponse)
async def dispatch_team(
    incident_id: UUID,
    team_id: UUID,
    body: AssignmentDispatch,
    user: CurrentUser,
    pool: Annotated[asyncpg.Pool, Depends(get_pool)],
) -> TeamResponse:
    await _verify_team(pool, team_id, incident_id)
    row = await dispatch_assignment(
        pool,
        team_id,
        search_type=body.search_type,
        turnaround_time=body.turnaround_time,
    )
    if row is None:
        raise HTTPException(status_code=404, detail="Team not found")
    return _to_team_response(row)


# --- Team Members ---


@router.post(
    "/{team_id}/members",
    response_model=TeamMemberResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_member(
    incident_id: UUID,
    team_id: UUID,
    body: TeamMemberAdd,
    user: CurrentUser,
    pool: Annotated[asyncpg.Pool, Depends(get_pool)],
) -> TeamMemberResponse:
    await _verify_team(pool, team_id, incident_id)
    row = await add_team_member(
        pool,
        team_id=team_id,
        user_id=body.user_id,
        role=body.role,
    )
    return _to_member_response(row)


@router.get("/{team_id}/members", response_model=list[TeamMemberResponse])
async def list_members(
    incident_id: UUID,
    team_id: UUID,
    user: CurrentUser,
    pool: Annotated[asyncpg.Pool, Depends(get_pool)],
) -> list[TeamMemberResponse]:
    await _verify_team(pool, team_id, incident_id)
    rows = await list_team_members(pool, team_id)
    return [_to_member_response(r) for r in rows]


@router.delete("/{team_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_member(
    incident_id: UUID,
    team_id: UUID,
    user_id: UUID,
    user: CurrentUser,
    pool: Annotated[asyncpg.Pool, Depends(get_pool)],
) -> None:
    await _verify_team(pool, team_id, incident_id)
    removed = await remove_team_member(pool, team_id, user_id)
    if not removed:
        raise HTTPException(status_code=404, detail="Team member not found")


# --- Check-ins ---


@router.post("/{team_id}/check-in", response_model=TeamResponse)
async def team_check_in(
    incident_id: UUID,
    team_id: UUID,
    user: CurrentUser,
    pool: Annotated[asyncpg.Pool, Depends(get_pool)],
) -> TeamResponse:
    await _verify_team(pool, team_id, incident_id)
    row = await record_check_in(pool, team_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Team not found")
    return _to_team_response(row)


@router.get("/overdue", response_model=list[TeamResponse])
async def get_overdue(
    incident_id: UUID,
    user: CurrentUser,
    pool: Annotated[asyncpg.Pool, Depends(get_pool)],
) -> list[TeamResponse]:
    await _verify_incident(pool, incident_id)
    rows = await get_overdue_teams(pool, incident_id)
    return [_to_team_response(r) for r in rows]


# --- Accountability Board ---


@router.get(
    "/accountability",
    response_model=list[AccountabilityEntry],
)
async def accountability_board(
    incident_id: UUID,
    user: CurrentUser,
    pool: Annotated[asyncpg.Pool, Depends(get_pool)],
) -> list[AccountabilityEntry]:
    await _verify_incident(pool, incident_id)
    rows = await get_accountability_board(pool, incident_id)
    return [
        AccountabilityEntry(
            user_id=r["user_id"],
            display_name=r["display_name"],
            team_name=r["team_name"],
            role=ICSRole(r["role"]),
            signed_in_at=r["signed_in_at"],
            signed_out_at=r["signed_out_at"],
        )
        for r in rows
    ]
