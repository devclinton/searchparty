"""Tests for GPS track API endpoints."""

from httpx import AsyncClient

from .conftest import TEST_USER_ID


async def test_upload_gps_track(client: AsyncClient, auth_headers: dict):
    # First create an incident
    inc_resp = await client.post(
        "/api/v1/incidents",
        headers=auth_headers,
        json={"name": "GPS Test Incident"},
    )
    incident_id = inc_resp.json()["id"]

    resp = await client.post(
        "/api/v1/gps/tracks",
        headers=auth_headers,
        json={
            "track_id": f"{TEST_USER_ID}-123456",
            "incident_id": incident_id,
            "started_at": "2026-04-13T10:00:00Z",
            "ended_at": "2026-04-13T12:00:00Z",
            "points": [
                {
                    "lat": 45.3735,
                    "lon": -121.6959,
                    "altitude": 1200.0,
                    "accuracy": 5.0,
                    "timestamp": "2026-04-13T10:00:00Z",
                },
                {
                    "lat": 45.3740,
                    "lon": -121.6950,
                    "altitude": 1210.0,
                    "accuracy": 4.0,
                    "timestamp": "2026-04-13T10:05:00Z",
                },
            ],
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["point_count"] == 2


async def test_upload_track_unauthenticated(client: AsyncClient):
    resp = await client.post(
        "/api/v1/gps/tracks",
        json={
            "track_id": "no-auth-track",
            "incident_id": "00000000-0000-0000-0000-000000000000",
            "started_at": "2026-04-13T10:00:00Z",
            "points": [],
        },
    )
    assert resp.status_code in (401, 403)
