"""Tests for incident API endpoints."""

from httpx import AsyncClient


async def test_create_incident(client: AsyncClient, auth_headers: dict):
    resp = await client.post(
        "/api/v1/incidents",
        headers=auth_headers,
        json={
            "name": "Missing Hiker - Mt. Hood",
            "description": "Subject last seen at trailhead",
            "subject_name": "John Doe",
            "subject_age_category": "adult",
            "subject_activity": "hiker",
            "ipp_lat": 45.3735,
            "ipp_lon": -121.6959,
            "terrain_type": "alpine",
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Missing Hiker - Mt. Hood"
    assert data["status"] == "planning"
    assert data["subject_age_category"] == "adult"
    assert data["ipp_lat"] == 45.3735


async def test_list_incidents(client: AsyncClient, auth_headers: dict):
    # Create two incidents
    await client.post(
        "/api/v1/incidents",
        headers=auth_headers,
        json={"name": "Incident A"},
    )
    await client.post(
        "/api/v1/incidents",
        headers=auth_headers,
        json={"name": "Incident B"},
    )

    resp = await client.get("/api/v1/incidents", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 2


async def test_get_incident_by_id(client: AsyncClient, auth_headers: dict):
    create_resp = await client.post(
        "/api/v1/incidents",
        headers=auth_headers,
        json={"name": "Get Me"},
    )
    incident_id = create_resp.json()["id"]

    resp = await client.get(f"/api/v1/incidents/{incident_id}", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["name"] == "Get Me"


async def test_get_incident_not_found(client: AsyncClient, auth_headers: dict):
    resp = await client.get(
        "/api/v1/incidents/00000000-0000-0000-0000-000000000000",
        headers=auth_headers,
    )
    assert resp.status_code == 404


async def test_incident_status_transition_planning_to_active(
    client: AsyncClient, auth_headers: dict
):
    create_resp = await client.post(
        "/api/v1/incidents",
        headers=auth_headers,
        json={"name": "Status Test"},
    )
    incident_id = create_resp.json()["id"]

    resp = await client.post(
        f"/api/v1/incidents/{incident_id}/status",
        headers=auth_headers,
        json={"status": "active"},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "active"


async def test_incident_status_invalid_transition(client: AsyncClient, auth_headers: dict):
    create_resp = await client.post(
        "/api/v1/incidents",
        headers=auth_headers,
        json={"name": "Bad Transition"},
    )
    incident_id = create_resp.json()["id"]

    # planning -> suspended is not valid
    resp = await client.post(
        f"/api/v1/incidents/{incident_id}/status",
        headers=auth_headers,
        json={"status": "suspended"},
    )
    assert resp.status_code == 422


async def test_incident_status_only_ic_can_change(
    client: AsyncClient, auth_headers_user2: dict, auth_headers: dict
):
    # Create incident as user 1
    create_resp = await client.post(
        "/api/v1/incidents",
        headers=auth_headers,
        json={"name": "IC Only"},
    )
    incident_id = create_resp.json()["id"]

    # Try to change status as user 2
    resp = await client.post(
        f"/api/v1/incidents/{incident_id}/status",
        headers=auth_headers_user2,
        json={"status": "active"},
    )
    assert resp.status_code == 403


async def test_incident_close_sets_closed_at(client: AsyncClient, auth_headers: dict):
    create_resp = await client.post(
        "/api/v1/incidents",
        headers=auth_headers,
        json={"name": "Close Me"},
    )
    incident_id = create_resp.json()["id"]

    # planning -> closed is valid
    resp = await client.post(
        f"/api/v1/incidents/{incident_id}/status",
        headers=auth_headers,
        json={"status": "closed"},
    )
    assert resp.status_code == 200
    assert resp.json()["closed_at"] is not None


async def test_create_incident_unauthenticated(client: AsyncClient):
    resp = await client.post(
        "/api/v1/incidents",
        json={"name": "No Auth"},
    )
    assert resp.status_code in (401, 403)
