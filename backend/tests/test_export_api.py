"""Tests for data export API."""

from httpx import AsyncClient


async def test_export_incident(client: AsyncClient, auth_headers: dict):
    # Create incident
    resp = await client.post(
        "/api/v1/incidents",
        headers=auth_headers,
        json={"name": "Export Test"},
    )
    incident_id = resp.json()["id"]

    resp = await client.get(
        f"/api/v1/export/incidents/{incident_id}",
        headers=auth_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["version"] == 1
    assert data["incident"]["name"] == "Export Test"
    assert "teams" in data
    assert "segments" in data
    assert "hazards" in data
    assert "clues" in data


async def test_export_not_found(client: AsyncClient, auth_headers: dict):
    resp = await client.get(
        "/api/v1/export/incidents/00000000-0000-0000-0000-000000000000",
        headers=auth_headers,
    )
    assert resp.status_code == 404
