"""Mesh network API endpoints.

Provides server-side ingestion of mesh data (from MQTT bridge or
direct API calls) and queries for mesh node status and messages.
"""

from typing import Annotated
from uuid import UUID

import asyncpg
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.auth.dependencies import CurrentUser
from app.db.connection import get_pool
from app.db.mesh import (
    insert_mesh_message,
    list_mesh_messages,
    list_mesh_nodes,
    upsert_mesh_node,
)

router = APIRouter(prefix="/mesh", tags=["mesh"])


class MeshNodeUpdate(BaseModel):
    node_id: str
    incident_id: UUID | None = None
    user_id: UUID | None = None
    long_name: str | None = None
    short_name: str | None = None
    hw_model: str | None = None
    battery_level: int | None = None
    last_lat: float | None = None
    last_lon: float | None = None
    last_altitude: float | None = None
    snr: float | None = None


class MeshMessageCreate(BaseModel):
    incident_id: UUID | None = None
    from_node: str
    to_node: str | None = None
    channel: int = 0
    message_text: str
    is_emergency: bool = False


class MeshNodeResponse(BaseModel):
    node_id: str
    incident_id: UUID | None
    user_id: UUID | None
    long_name: str | None
    short_name: str | None
    hw_model: str | None
    battery_level: int | None
    last_lat: float | None
    last_lon: float | None
    last_altitude: float | None
    snr: float | None
    last_heard_at: str


class MeshMessageResponse(BaseModel):
    id: UUID
    incident_id: UUID | None
    from_node: str
    to_node: str | None
    channel: int
    message_text: str
    is_emergency: bool
    received_at: str


# --- MQTT Bridge Ingestion ---
# These endpoints are called by the MQTT bridge service
# when mesh data arrives via a Meshtastic MQTT gateway.


@router.post("/nodes", response_model=MeshNodeResponse)
async def update_mesh_node(
    body: MeshNodeUpdate,
    user: CurrentUser,
    pool: Annotated[asyncpg.Pool, Depends(get_pool)],
) -> MeshNodeResponse:
    """Update or create a mesh node (called by MQTT bridge)."""
    row = await upsert_mesh_node(
        pool,
        node_id=body.node_id,
        incident_id=body.incident_id,
        user_id=body.user_id,
        long_name=body.long_name,
        short_name=body.short_name,
        hw_model=body.hw_model,
        battery_level=body.battery_level,
        last_lat=body.last_lat,
        last_lon=body.last_lon,
        last_altitude=body.last_altitude,
        snr=body.snr,
    )
    return MeshNodeResponse(
        node_id=row["node_id"],
        incident_id=row["incident_id"],
        user_id=row["user_id"],
        long_name=row["long_name"],
        short_name=row["short_name"],
        hw_model=row["hw_model"],
        battery_level=row["battery_level"],
        last_lat=row["last_lat"],
        last_lon=row["last_lon"],
        last_altitude=row["last_altitude"],
        snr=row["snr"],
        last_heard_at=row["last_heard_at"].isoformat(),
    )


@router.post("/messages", response_model=MeshMessageResponse)
async def create_mesh_message(
    body: MeshMessageCreate,
    user: CurrentUser,
    pool: Annotated[asyncpg.Pool, Depends(get_pool)],
) -> MeshMessageResponse:
    """Record a mesh message (called by MQTT bridge)."""
    row = await insert_mesh_message(
        pool,
        incident_id=body.incident_id,
        from_node=body.from_node,
        to_node=body.to_node,
        channel=body.channel,
        message_text=body.message_text,
        is_emergency=body.is_emergency,
    )
    return MeshMessageResponse(
        id=row["id"],
        incident_id=row["incident_id"],
        from_node=row["from_node"],
        to_node=row["to_node"],
        channel=row["channel"],
        message_text=row["message_text"],
        is_emergency=row["is_emergency"],
        received_at=row["received_at"].isoformat(),
    )


# --- Query Endpoints ---


@router.get(
    "/incidents/{incident_id}/nodes",
    response_model=list[MeshNodeResponse],
)
async def get_mesh_nodes(
    incident_id: UUID,
    user: CurrentUser,
    pool: Annotated[asyncpg.Pool, Depends(get_pool)],
) -> list[MeshNodeResponse]:
    rows = await list_mesh_nodes(pool, incident_id)
    return [
        MeshNodeResponse(
            node_id=r["node_id"],
            incident_id=r["incident_id"],
            user_id=r["user_id"],
            long_name=r["long_name"],
            short_name=r["short_name"],
            hw_model=r["hw_model"],
            battery_level=r["battery_level"],
            last_lat=r["last_lat"],
            last_lon=r["last_lon"],
            last_altitude=r["last_altitude"],
            snr=r["snr"],
            last_heard_at=r["last_heard_at"].isoformat(),
        )
        for r in rows
    ]


@router.get(
    "/incidents/{incident_id}/messages",
    response_model=list[MeshMessageResponse],
)
async def get_mesh_messages(
    incident_id: UUID,
    user: CurrentUser,
    pool: Annotated[asyncpg.Pool, Depends(get_pool)],
) -> list[MeshMessageResponse]:
    rows = await list_mesh_messages(pool, incident_id)
    return [
        MeshMessageResponse(
            id=r["id"],
            incident_id=r["incident_id"],
            from_node=r["from_node"],
            to_node=r["to_node"],
            channel=r["channel"],
            message_text=r["message_text"],
            is_emergency=r["is_emergency"],
            received_at=r["received_at"].isoformat(),
        )
        for r in rows
    ]
