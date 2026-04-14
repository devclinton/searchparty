import math
from typing import Annotated
from uuid import UUID

import asyncpg
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.auth.dependencies import CurrentUser
from app.db.connection import get_pool
from app.db.incidents import get_incident_by_id
from app.search.lpb_data import PROFILES, get_all_categories, get_distance_rings_km, get_profile

router = APIRouter(prefix="/lpb", tags=["lpb"])


class ProfileResponse(BaseModel):
    category: str
    label: str
    description: str
    distances_km: dict[str, float]
    behaviors: list[str]
    terrain_notes: str


class RingGeoJSON(BaseModel):
    """GeoJSON FeatureCollection of probability rings around an IPP."""

    type: str = "FeatureCollection"
    features: list[dict]


class PrioritySuggestion(BaseModel):
    segment_id: str
    segment_name: str
    probability_score: float
    reason: str


def _generate_circle_coords(
    center_lon: float, center_lat: float, radius_km: float, num_points: int = 64
) -> list[list[float]]:
    """Generate a polygon approximating a circle on the Earth's surface."""
    coords = []
    for i in range(num_points + 1):
        angle = (2 * math.pi * i) / num_points
        # Approximate degrees per km at this latitude
        lat_offset = (radius_km / 111.32) * math.cos(angle)
        lon_offset = (radius_km / (111.32 * math.cos(math.radians(center_lat)))) * math.sin(angle)
        coords.append([center_lon + lon_offset, center_lat + lat_offset])
    return coords


@router.get("/categories")
async def list_categories() -> list[dict]:
    return get_all_categories()


@router.get("/profiles/{category}", response_model=ProfileResponse)
async def get_profile_detail(category: str) -> ProfileResponse:
    profile = get_profile(category)
    if profile is None:
        raise HTTPException(status_code=404, detail=f"Unknown category: {category}")
    return ProfileResponse(
        category=profile.category,
        label=profile.label,
        description=profile.description,
        distances_km={
            "p25": profile.distances.p25,
            "p50": profile.distances.p50,
            "p75": profile.distances.p75,
            "p95": profile.distances.p95,
        },
        behaviors=profile.behaviors,
        terrain_notes=profile.terrain_notes,
    )


@router.get("/incidents/{incident_id}/rings", response_model=RingGeoJSON)
async def get_probability_rings(
    incident_id: UUID,
    user: CurrentUser,
    pool: Annotated[asyncpg.Pool, Depends(get_pool)],
) -> RingGeoJSON:
    """Generate probability distance rings based on incident subject profile and IPP."""
    incident = await get_incident_by_id(pool, incident_id)
    if incident is None:
        raise HTTPException(status_code=404, detail="Incident not found")

    ipp_lat = incident["ipp_lat"]
    ipp_lon = incident["ipp_lon"]
    if ipp_lat is None or ipp_lon is None:
        raise HTTPException(status_code=422, detail="Incident has no IPP coordinates")

    # Use subject category from incident, fall back to activity, then adult
    category = incident["subject_age_category"]
    if category is None:
        activity = incident["subject_activity"]
        category = activity if activity and activity in PROFILES else "adult"

    distances = get_distance_rings_km(category)
    if distances is None:
        distances = get_distance_rings_km("adult")
    assert distances is not None

    profile = get_profile(category)
    profile_label = profile.label if profile else "Adult"

    percentiles = [
        ("p25", 0.25, "#d32f2f"),
        ("p50", 0.50, "#f57c00"),
        ("p75", 0.75, "#fbc02d"),
        ("p95", 0.95, "#388e3c"),
    ]

    features = []
    for key, pct, color in percentiles:
        radius = distances[key]
        coords = _generate_circle_coords(ipp_lon, ipp_lat, radius)
        features.append(
            {
                "type": "Feature",
                "properties": {
                    "percentile": pct,
                    "percentile_label": f"{int(pct * 100)}th percentile",
                    "radius_km": radius,
                    "color": color,
                    "profile": profile_label,
                },
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [coords],
                },
            }
        )

    # IPP marker
    features.append(
        {
            "type": "Feature",
            "properties": {
                "type": "ipp",
                "label": "Initial Planning Point",
            },
            "geometry": {
                "type": "Point",
                "coordinates": [ipp_lon, ipp_lat],
            },
        }
    )

    return RingGeoJSON(features=features)


@router.get("/incidents/{incident_id}/behaviors")
async def get_subject_behaviors(
    incident_id: UUID,
    user: CurrentUser,
    pool: Annotated[asyncpg.Pool, Depends(get_pool)],
) -> dict:
    """Get travel behavior annotations for the incident's subject profile."""
    incident = await get_incident_by_id(pool, incident_id)
    if incident is None:
        raise HTTPException(status_code=404, detail="Incident not found")

    category = incident["subject_age_category"] or incident["subject_activity"] or "adult"
    profile = get_profile(category) or get_profile("adult")
    assert profile is not None

    return {
        "category": profile.category,
        "label": profile.label,
        "behaviors": profile.behaviors,
        "terrain_notes": profile.terrain_notes,
        "distances_km": {
            "p25": profile.distances.p25,
            "p50": profile.distances.p50,
            "p75": profile.distances.p75,
            "p95": profile.distances.p95,
        },
    }
