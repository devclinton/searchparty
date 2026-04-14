"""Data export endpoint for offline handoff."""

from typing import Annotated
from uuid import UUID

import asyncpg
from fastapi import APIRouter, Depends, HTTPException

from app.auth.dependencies import CurrentUser
from app.db.connection import get_pool
from app.db.incidents import get_incident_by_id
from app.db.safety import list_hazard_zones
from app.db.search import list_clues_by_incident, list_segments_by_incident
from app.db.teams import list_teams_by_incident

router = APIRouter(prefix="/export", tags=["export"])


@router.get("/incidents/{incident_id}")
async def export_incident(
    incident_id: UUID,
    user: CurrentUser,
    pool: Annotated[asyncpg.Pool, Depends(get_pool)],
) -> dict:
    """Export all incident data as a JSON bundle for offline handoff."""
    incident = await get_incident_by_id(pool, incident_id)
    if incident is None:
        raise HTTPException(status_code=404, detail="Incident not found")

    teams = await list_teams_by_incident(pool, incident_id)
    segments = await list_segments_by_incident(pool, incident_id)
    hazards = await list_hazard_zones(pool, incident_id)
    clues = await list_clues_by_incident(pool, incident_id)

    def serialize(record):
        result = {}
        for key in record:
            val = record[key]
            if hasattr(val, "isoformat"):
                result[key] = val.isoformat()
            elif isinstance(val, UUID):
                result[key] = str(val)
            else:
                result[key] = val
        return result

    return {
        "version": 1,
        "incident": serialize(incident),
        "teams": [serialize(t) for t in teams],
        "segments": [serialize(s) for s in segments],
        "hazards": [serialize(h) for h in hazards],
        "clues": [serialize(c) for c in clues],
    }
