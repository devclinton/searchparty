"""Tests for reporting and analytics API endpoints."""

from httpx import AsyncClient


async def test_operation_summary(client: AsyncClient, auth_headers: dict):
    resp = await client.post(
        "/api/v1/incidents",
        headers=auth_headers,
        json={"name": "Report Test"},
    )
    incident_id = resp.json()["id"]

    resp = await client.get(
        f"/api/v1/reports/incidents/{incident_id}/summary",
        headers=auth_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["incident_name"] == "Report Test"
    assert "total_teams" in data
    assert "total_clues" in data


async def test_team_performance(client: AsyncClient, auth_headers: dict):
    resp = await client.post(
        "/api/v1/incidents",
        headers=auth_headers,
        json={"name": "Perf Test"},
    )
    incident_id = resp.json()["id"]

    resp = await client.get(
        f"/api/v1/reports/incidents/{incident_id}/team-performance",
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


async def test_incident_action_plan(client: AsyncClient, auth_headers: dict):
    resp = await client.post(
        "/api/v1/incidents",
        headers=auth_headers,
        json={
            "name": "IAP Test",
            "subject_name": "Jane Doe",
            "ipp_lat": 45.37,
            "ipp_lon": -121.69,
        },
    )
    incident_id = resp.json()["id"]

    resp = await client.get(
        f"/api/v1/reports/incidents/{incident_id}/iap",
        headers=auth_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["incident_name"] == "IAP Test"
    assert "teams" in data
    assert "hazards" in data
    assert "safety_message" in data


async def test_clues_csv_export(client: AsyncClient, auth_headers: dict):
    resp = await client.post(
        "/api/v1/incidents",
        headers=auth_headers,
        json={"name": "CSV Test"},
    )
    incident_id = resp.json()["id"]

    resp = await client.get(
        f"/api/v1/reports/incidents/{incident_id}/clues.csv",
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert "id,lat,lon" in resp.text
