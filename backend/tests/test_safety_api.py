"""Tests for safety and hazard management API endpoints."""

from httpx import AsyncClient


async def _create_incident(client: AsyncClient, auth_headers: dict) -> str:
    resp = await client.post(
        "/api/v1/incidents",
        headers=auth_headers,
        json={"name": "Safety Test Incident"},
    )
    return resp.json()["id"]


async def test_create_hazard_zone(client: AsyncClient, auth_headers: dict):
    incident_id = await _create_incident(client, auth_headers)

    resp = await client.post(
        f"/api/v1/incidents/{incident_id}/hazards",
        headers=auth_headers,
        json={
            "name": "Cliff Edge",
            "hazard_type": "cliff",
            "severity": "danger",
            "description": "200ft drop",
            "center_lat": 45.374,
            "center_lon": -121.696,
            "radius_meters": 50.0,
            "alert_buffer_meters": 100.0,
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Cliff Edge"
    assert data["hazard_type"] == "cliff"
    assert data["severity"] == "danger"


async def test_list_hazard_zones(client: AsyncClient, auth_headers: dict):
    incident_id = await _create_incident(client, auth_headers)

    await client.post(
        f"/api/v1/incidents/{incident_id}/hazards",
        headers=auth_headers,
        json={
            "name": "Mine Shaft",
            "hazard_type": "mine_shaft",
            "center_lat": 45.37,
            "center_lon": -121.69,
        },
    )

    resp = await client.get(
        f"/api/v1/incidents/{incident_id}/hazards",
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert len(resp.json()) >= 1


async def test_send_emergency_alert(client: AsyncClient, auth_headers: dict):
    incident_id = await _create_incident(client, auth_headers)

    resp = await client.post(
        f"/api/v1/incidents/{incident_id}/emergency",
        headers=auth_headers,
        json={
            "lat": 45.375,
            "lon": -121.697,
            "message": "Team member injured, need evacuation",
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["status"] == "active"
    assert data["message"] == "Team member injured, need evacuation"


async def test_list_emergency_alerts(client: AsyncClient, auth_headers: dict):
    incident_id = await _create_incident(client, auth_headers)

    await client.post(
        f"/api/v1/incidents/{incident_id}/emergency",
        headers=auth_headers,
        json={"lat": 45.37, "lon": -121.69},
    )

    resp = await client.get(
        f"/api/v1/incidents/{incident_id}/emergency",
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert len(resp.json()) >= 1


async def test_acknowledge_emergency_alert(client: AsyncClient, auth_headers: dict):
    incident_id = await _create_incident(client, auth_headers)

    create_resp = await client.post(
        f"/api/v1/incidents/{incident_id}/emergency",
        headers=auth_headers,
        json={"lat": 45.37, "lon": -121.69},
    )
    alert_id = create_resp.json()["id"]

    resp = await client.patch(
        f"/api/v1/emergency/{alert_id}",
        headers=auth_headers,
        json={"status": "acknowledged"},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "acknowledged"
    assert resp.json()["acknowledged_at"] is not None


async def test_safety_dashboard(client: AsyncClient, auth_headers: dict):
    incident_id = await _create_incident(client, auth_headers)

    # Create a hazard and an alert
    await client.post(
        f"/api/v1/incidents/{incident_id}/hazards",
        headers=auth_headers,
        json={
            "name": "River",
            "hazard_type": "water",
            "center_lat": 45.37,
            "center_lon": -121.69,
        },
    )
    await client.post(
        f"/api/v1/incidents/{incident_id}/emergency",
        headers=auth_headers,
        json={"lat": 45.37, "lon": -121.69},
    )

    resp = await client.get(
        f"/api/v1/incidents/{incident_id}/safety-dashboard",
        headers=auth_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["active_hazard_zones"] >= 1
    assert data["active_emergency_alerts"] >= 1


async def test_create_hazard_unauthenticated(client: AsyncClient):
    resp = await client.post(
        "/api/v1/incidents/00000000-0000-0000-0000-000000000000/hazards",
        json={
            "name": "test",
            "hazard_type": "cliff",
            "center_lat": 45.0,
            "center_lon": -121.0,
        },
    )
    assert resp.status_code in (401, 403)
