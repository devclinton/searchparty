"""Tests for search segment and clue API endpoints."""

from httpx import AsyncClient


async def _create_incident(client: AsyncClient, auth_headers: dict) -> str:
    resp = await client.post(
        "/api/v1/incidents",
        headers=auth_headers,
        json={"name": "Search Test Incident"},
    )
    return resp.json()["id"]


async def test_create_clue(client: AsyncClient, auth_headers: dict):
    incident_id = await _create_incident(client, auth_headers)

    resp = await client.post(
        f"/api/v1/incidents/{incident_id}/clues",
        headers=auth_headers,
        json={
            "lat": 45.3735,
            "lon": -121.6959,
            "description": "Backpack found near trail",
            "clue_type": "physical",
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["description"] == "Backpack found near trail"
    assert data["clue_type"] == "physical"
    assert data["lat"] == 45.3735


async def test_list_clues(client: AsyncClient, auth_headers: dict):
    incident_id = await _create_incident(client, auth_headers)

    await client.post(
        f"/api/v1/incidents/{incident_id}/clues",
        headers=auth_headers,
        json={
            "lat": 45.37,
            "lon": -121.69,
            "description": "Footprint",
            "clue_type": "track",
        },
    )
    await client.post(
        f"/api/v1/incidents/{incident_id}/clues",
        headers=auth_headers,
        json={
            "lat": 45.38,
            "lon": -121.70,
            "description": "Water bottle",
            "clue_type": "physical",
        },
    )

    resp = await client.get(
        f"/api/v1/incidents/{incident_id}/clues",
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert len(resp.json()) >= 2


async def test_create_clue_unauthenticated(client: AsyncClient):
    resp = await client.post(
        "/api/v1/incidents/00000000-0000-0000-0000-000000000000/clues",
        json={
            "lat": 45.0,
            "lon": -121.0,
            "description": "test",
        },
    )
    assert resp.status_code in (401, 403)
