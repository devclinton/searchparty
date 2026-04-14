from typing import Annotated
from uuid import UUID

import asyncpg
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.auth.dependencies import CurrentUser, require_role
from app.db.connection import get_pool
from app.db.incidents import (
    create_incident,
    get_incident_by_id,
    list_incidents,
    purge_expired_incidents,
    update_incident,
    update_incident_status,
)
from app.models.incident import (
    VALID_STATUS_TRANSITIONS,
    IncidentCreate,
    IncidentResponse,
    IncidentStatus,
    IncidentStatusUpdate,
    IncidentUpdate,
)
from app.models.user import ICSRole

router = APIRouter(prefix="/incidents", tags=["incidents"])


def _to_response(row: asyncpg.Record) -> IncidentResponse:
    return IncidentResponse(
        id=row["id"],
        name=row["name"],
        status=IncidentStatus(row["status"]),
        description=row["description"],
        subject_name=row["subject_name"],
        subject_age_category=row["subject_age_category"],
        subject_activity=row["subject_activity"],
        subject_condition=row["subject_condition"],
        subject_clothing=row["subject_clothing"],
        subject_medical_needs=row["subject_medical_needs"],
        ipp_lat=row["ipp_lat"],
        ipp_lon=row["ipp_lon"],
        terrain_type=row["terrain_type"],
        incident_commander_id=row["incident_commander_id"],
        data_retention_days=row["data_retention_days"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        closed_at=row["closed_at"],
    )


@router.post("", response_model=IncidentResponse, status_code=status.HTTP_201_CREATED)
async def create_new_incident(
    body: IncidentCreate,
    user: CurrentUser,
    pool: Annotated[asyncpg.Pool, Depends(get_pool)],
) -> IncidentResponse:
    row = await create_incident(
        pool,
        name=body.name,
        incident_commander_id=user["id"],
        description=body.description,
        subject_name=body.subject_name,
        subject_age_category=body.subject_age_category,
        subject_activity=body.subject_activity,
        subject_condition=body.subject_condition,
        subject_clothing=body.subject_clothing,
        subject_medical_needs=body.subject_medical_needs,
        ipp_lat=body.ipp_lat,
        ipp_lon=body.ipp_lon,
        terrain_type=body.terrain_type,
        data_retention_days=body.data_retention_days,
    )
    return _to_response(row)


@router.get("", response_model=list[IncidentResponse])
async def list_all_incidents(
    user: CurrentUser,
    pool: Annotated[asyncpg.Pool, Depends(get_pool)],
    incident_status: IncidentStatus | None = Query(None, alias="status"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> list[IncidentResponse]:
    rows = await list_incidents(pool, status=incident_status, limit=limit, offset=offset)
    return [_to_response(r) for r in rows]


@router.get("/{incident_id}", response_model=IncidentResponse)
async def get_incident(
    incident_id: UUID,
    user: CurrentUser,
    pool: Annotated[asyncpg.Pool, Depends(get_pool)],
) -> IncidentResponse:
    row = await get_incident_by_id(pool, incident_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Incident not found")
    return _to_response(row)


@router.patch("/{incident_id}", response_model=IncidentResponse)
async def update_existing_incident(
    incident_id: UUID,
    body: IncidentUpdate,
    user: CurrentUser,
    pool: Annotated[asyncpg.Pool, Depends(get_pool)],
    _role: Annotated[None, Depends(require_role(ICSRole.OPERATIONS_CHIEF))],
) -> IncidentResponse:
    existing = await get_incident_by_id(pool, incident_id)
    if existing is None:
        raise HTTPException(status_code=404, detail="Incident not found")

    fields = body.model_dump(exclude_none=True)
    row = await update_incident(pool, incident_id, **fields)
    if row is None:
        raise HTTPException(status_code=404, detail="Incident not found")
    return _to_response(row)


@router.post("/{incident_id}/status", response_model=IncidentResponse)
async def transition_incident_status(
    incident_id: UUID,
    body: IncidentStatusUpdate,
    user: CurrentUser,
    pool: Annotated[asyncpg.Pool, Depends(get_pool)],
) -> IncidentResponse:
    existing = await get_incident_by_id(pool, incident_id)
    if existing is None:
        raise HTTPException(status_code=404, detail="Incident not found")

    # Only IC can change status
    if existing["incident_commander_id"] != user["id"]:
        raise HTTPException(
            status_code=403,
            detail="Only the Incident Commander can change status",
        )

    current = IncidentStatus(existing["status"])
    allowed = VALID_STATUS_TRANSITIONS.get(current, [])
    if body.status not in allowed:
        raise HTTPException(
            status_code=422,
            detail=f"Cannot transition from {current} to {body.status}",
        )

    row = await update_incident_status(pool, incident_id, body.status)
    if row is None:
        raise HTTPException(status_code=404, detail="Incident not found")
    return _to_response(row)


@router.post("/purge", status_code=status.HTTP_200_OK)
async def purge_expired(
    user: CurrentUser,
    pool: Annotated[asyncpg.Pool, Depends(get_pool)],
) -> dict[str, int]:
    count = await purge_expired_incidents(pool)
    return {"purged": count}
