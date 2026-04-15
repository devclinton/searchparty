"""Tests for mesh network API endpoints."""

from httpx import AsyncClient


async def test_update_mesh_node(client: AsyncClient, auth_headers: dict):
    resp = await client.post(
        "/api/v1/mesh/nodes",
        headers=auth_headers,
        json={
            "node_id": "!aabbccdd",
            "long_name": "Team Alpha Radio",
            "short_name": "ALPH",
            "battery_level": 85,
            "last_lat": 45.3735,
            "last_lon": -121.6959,
            "snr": 12.5,
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["node_id"] == "!aabbccdd"
    assert data["long_name"] == "Team Alpha Radio"
    assert data["battery_level"] == 85


async def test_create_mesh_message(client: AsyncClient, auth_headers: dict):
    resp = await client.post(
        "/api/v1/mesh/messages",
        headers=auth_headers,
        json={
            "from_node": "!aabbccdd",
            "message_text": "CHECK-IN: OK",
            "is_emergency": False,
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["message_text"] == "CHECK-IN: OK"
    assert data["is_emergency"] is False


async def test_create_emergency_mesh_message(client: AsyncClient, auth_headers: dict):
    resp = await client.post(
        "/api/v1/mesh/messages",
        headers=auth_headers,
        json={
            "from_node": "!11223344",
            "message_text": "EMERGENCY: DISTRESS",
            "is_emergency": True,
        },
    )
    assert resp.status_code == 200
    assert resp.json()["is_emergency"] is True
