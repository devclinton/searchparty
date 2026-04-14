"""Tests for Lost Person Behavior data and API."""

from httpx import AsyncClient

from app.search.lpb_data import (
    PROFILES,
    get_all_categories,
    get_distance_rings_km,
    get_profile,
)

# --- Unit tests for LPB data ---


def test_all_profiles_have_distances():
    for key, profile in PROFILES.items():
        assert profile.distances.p25 > 0, f"{key} p25 must be > 0"
        assert profile.distances.p50 >= profile.distances.p25, f"{key} p50 >= p25"
        assert profile.distances.p75 >= profile.distances.p50, f"{key} p75 >= p50"
        assert profile.distances.p95 >= profile.distances.p75, f"{key} p95 >= p75"


def test_all_profiles_have_behaviors():
    for key, profile in PROFILES.items():
        assert len(profile.behaviors) > 0, f"{key} must have behaviors"
        assert profile.terrain_notes, f"{key} must have terrain notes"


def test_get_profile_valid():
    profile = get_profile("hiker")
    assert profile is not None
    assert profile.label == "Hiker"


def test_get_profile_invalid():
    assert get_profile("nonexistent") is None


def test_get_all_categories():
    cats = get_all_categories()
    assert len(cats) == len(PROFILES)
    assert all("category" in c and "label" in c for c in cats)


def test_get_distance_rings():
    rings = get_distance_rings_km("dementia")
    assert rings is not None
    assert rings["p25"] < rings["p50"] < rings["p75"] < rings["p95"]


def test_child_distances_shorter_than_adult():
    child = get_distance_rings_km("child_1_3")
    adult = get_distance_rings_km("adult")
    assert child is not None and adult is not None
    assert child["p95"] < adult["p95"]


def test_runner_has_longest_distances():
    runner = get_distance_rings_km("runner")
    assert runner is not None
    for key, profile in PROFILES.items():
        if key == "runner":
            continue
        assert runner["p95"] >= profile.distances.p95, f"Runner p95 should be >= {key} p95"


def test_dementia_has_linear_behavior():
    profile = get_profile("dementia")
    assert profile is not None
    assert any("straight line" in b.lower() for b in profile.behaviors)


# --- API tests ---


async def test_list_categories(client: AsyncClient):
    resp = await client.get("/api/v1/lpb/categories")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) > 10


async def test_get_profile_api(client: AsyncClient):
    resp = await client.get("/api/v1/lpb/profiles/hiker")
    assert resp.status_code == 200
    data = resp.json()
    assert data["category"] == "hiker"
    assert "behaviors" in data
    assert data["distances_km"]["p25"] > 0


async def test_get_profile_not_found(client: AsyncClient):
    resp = await client.get("/api/v1/lpb/profiles/nonexistent")
    assert resp.status_code == 404


async def test_probability_rings(client: AsyncClient, auth_headers: dict):
    # Create incident with IPP
    inc = await client.post(
        "/api/v1/incidents",
        headers=auth_headers,
        json={
            "name": "LPB Test",
            "subject_age_category": "child_7_12",
            "ipp_lat": 45.3735,
            "ipp_lon": -121.6959,
        },
    )
    incident_id = inc.json()["id"]

    resp = await client.get(
        f"/api/v1/lpb/incidents/{incident_id}/rings",
        headers=auth_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["type"] == "FeatureCollection"
    # 4 rings + 1 IPP point
    assert len(data["features"]) == 5


async def test_probability_rings_no_ipp(client: AsyncClient, auth_headers: dict):
    inc = await client.post(
        "/api/v1/incidents",
        headers=auth_headers,
        json={"name": "No IPP"},
    )
    incident_id = inc.json()["id"]

    resp = await client.get(
        f"/api/v1/lpb/incidents/{incident_id}/rings",
        headers=auth_headers,
    )
    assert resp.status_code == 422


async def test_subject_behaviors(client: AsyncClient, auth_headers: dict):
    inc = await client.post(
        "/api/v1/incidents",
        headers=auth_headers,
        json={
            "name": "Behavior Test",
            "subject_activity": "dementia",
            "ipp_lat": 45.37,
            "ipp_lon": -121.69,
        },
    )
    incident_id = inc.json()["id"]

    resp = await client.get(
        f"/api/v1/lpb/incidents/{incident_id}/behaviors",
        headers=auth_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["behaviors"]) > 0
