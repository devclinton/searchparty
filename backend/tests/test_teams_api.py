"""Tests for team API endpoints."""

import pytest
from httpx import AsyncClient

from .conftest import TEST_USER_2_ID


@pytest.fixture
async def incident_id(client: AsyncClient, auth_headers: dict) -> str:
    resp = await client.post(
        "/api/v1/incidents",
        headers=auth_headers,
        json={"name": "Team Test Incident"},
    )
    return resp.json()["id"]


async def test_create_team(client: AsyncClient, auth_headers: dict, incident_id: str):
    resp = await client.post(
        f"/api/v1/incidents/{incident_id}/teams",
        headers=auth_headers,
        json={"name": "Alpha Team", "search_type": "grid"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Alpha Team"
    assert data["status"] == "standby"
    assert data["search_type"] == "grid"
    assert data["check_in_interval_minutes"] == 30


async def test_list_teams(client: AsyncClient, auth_headers: dict, incident_id: str):
    await client.post(
        f"/api/v1/incidents/{incident_id}/teams",
        headers=auth_headers,
        json={"name": "Alpha"},
    )
    await client.post(
        f"/api/v1/incidents/{incident_id}/teams",
        headers=auth_headers,
        json={"name": "Bravo"},
    )

    resp = await client.get(
        f"/api/v1/incidents/{incident_id}/teams",
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert len(resp.json()) >= 2


async def test_get_team(client: AsyncClient, auth_headers: dict, incident_id: str):
    create_resp = await client.post(
        f"/api/v1/incidents/{incident_id}/teams",
        headers=auth_headers,
        json={"name": "Charlie"},
    )
    team_id = create_resp.json()["id"]

    resp = await client.get(
        f"/api/v1/incidents/{incident_id}/teams/{team_id}",
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["name"] == "Charlie"


async def test_change_team_status(client: AsyncClient, auth_headers: dict, incident_id: str):
    create_resp = await client.post(
        f"/api/v1/incidents/{incident_id}/teams",
        headers=auth_headers,
        json={"name": "Status Team"},
    )
    team_id = create_resp.json()["id"]

    resp = await client.post(
        f"/api/v1/incidents/{incident_id}/teams/{team_id}/status",
        headers=auth_headers,
        json={"status": "deployed"},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "deployed"
    assert resp.json()["deployed_at"] is not None


async def test_dispatch_team(client: AsyncClient, auth_headers: dict, incident_id: str):
    create_resp = await client.post(
        f"/api/v1/incidents/{incident_id}/teams",
        headers=auth_headers,
        json={"name": "Dispatch Team"},
    )
    team_id = create_resp.json()["id"]

    resp = await client.post(
        f"/api/v1/incidents/{incident_id}/teams/{team_id}/dispatch",
        headers=auth_headers,
        json={"search_type": "hasty"},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "deployed"


async def test_add_and_list_team_members(client: AsyncClient, auth_headers: dict, incident_id: str):
    create_resp = await client.post(
        f"/api/v1/incidents/{incident_id}/teams",
        headers=auth_headers,
        json={"name": "Member Team"},
    )
    team_id = create_resp.json()["id"]

    # Add member
    resp = await client.post(
        f"/api/v1/incidents/{incident_id}/teams/{team_id}/members",
        headers=auth_headers,
        json={"user_id": str(TEST_USER_2_ID), "role": "searcher"},
    )
    assert resp.status_code == 201
    assert resp.json()["role"] == "searcher"

    # List members
    resp = await client.get(
        f"/api/v1/incidents/{incident_id}/teams/{team_id}/members",
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert len(resp.json()) >= 1


async def test_remove_team_member(client: AsyncClient, auth_headers: dict, incident_id: str):
    create_resp = await client.post(
        f"/api/v1/incidents/{incident_id}/teams",
        headers=auth_headers,
        json={"name": "Remove Team"},
    )
    team_id = create_resp.json()["id"]

    # Add then remove
    await client.post(
        f"/api/v1/incidents/{incident_id}/teams/{team_id}/members",
        headers=auth_headers,
        json={"user_id": str(TEST_USER_2_ID), "role": "searcher"},
    )

    resp = await client.delete(
        f"/api/v1/incidents/{incident_id}/teams/{team_id}/members/{TEST_USER_2_ID}",
        headers=auth_headers,
    )
    assert resp.status_code == 204


async def test_team_check_in(client: AsyncClient, auth_headers: dict, incident_id: str):
    create_resp = await client.post(
        f"/api/v1/incidents/{incident_id}/teams",
        headers=auth_headers,
        json={"name": "CheckIn Team"},
    )
    team_id = create_resp.json()["id"]

    resp = await client.post(
        f"/api/v1/incidents/{incident_id}/teams/{team_id}/check-in",
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["last_check_in_at"] is not None


async def test_create_team_unauthenticated(client: AsyncClient, incident_id: str):
    resp = await client.post(
        f"/api/v1/incidents/{incident_id}/teams",
        json={"name": "No Auth Team"},
    )
    assert resp.status_code in (401, 403)
