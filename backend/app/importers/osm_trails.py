"""OpenStreetMap trail data fetcher via Overpass API."""

import httpx

OVERPASS_URL = "https://overpass-api.de/api/interpreter"

# Query for trails within a bounding box
TRAIL_QUERY_TEMPLATE = """
[out:json][timeout:30];
(
  way["highway"="path"]({south},{west},{north},{east});
  way["highway"="footway"]({south},{west},{north},{east});
  way["highway"="track"]({south},{west},{north},{east});
  way["highway"="bridleway"]({south},{west},{north},{east});
  way["highway"="cycleway"]({south},{west},{north},{east});
);
out body;
>;
out skel qt;
"""

# Map OSM highway tags to our trail types
HIGHWAY_MAP = {
    "path": "path",
    "footway": "footway",
    "track": "track",
    "bridleway": "bridleway",
    "cycleway": "cycleway",
}


class OSMTrail:
    def __init__(
        self,
        osm_id: str,
        name: str | None,
        trail_type: str,
        surface: str | None,
        difficulty: str | None,
        coordinates: list[list[float]],
    ):
        self.osm_id = osm_id
        self.name = name
        self.trail_type = trail_type
        self.surface = surface
        self.difficulty = difficulty
        self.coordinates = coordinates  # [[lon, lat], ...]


async def fetch_osm_trails(north: float, south: float, east: float, west: float) -> list[OSMTrail]:
    """Fetch trail data from OSM Overpass API for a bounding box."""
    query = TRAIL_QUERY_TEMPLATE.format(north=north, south=south, east=east, west=west)

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            OVERPASS_URL,
            data={"data": query},
        )
        response.raise_for_status()

    data = response.json()

    # Build node lookup
    nodes: dict[int, tuple[float, float]] = {}
    for elem in data.get("elements", []):
        if elem["type"] == "node":
            nodes[elem["id"]] = (elem["lon"], elem["lat"])

    # Parse ways into trails
    trails: list[OSMTrail] = []
    for elem in data.get("elements", []):
        if elem["type"] != "way":
            continue

        tags = elem.get("tags", {})
        highway = tags.get("highway", "path")
        trail_type = HIGHWAY_MAP.get(highway, "path")

        # Build coordinate list from node refs
        coordinates = []
        for node_id in elem.get("nodes", []):
            if node_id in nodes:
                coordinates.append(list(nodes[node_id]))

        if len(coordinates) < 2:
            continue

        trails.append(
            OSMTrail(
                osm_id=str(elem["id"]),
                name=tags.get("name"),
                trail_type=trail_type,
                surface=tags.get("surface"),
                difficulty=tags.get("sac_scale"),
                coordinates=coordinates,
            )
        )

    return trails


def coords_to_wkt(coordinates: list[list[float]]) -> str:
    """Convert [[lon, lat], ...] to WKT LINESTRING."""
    points = ", ".join(f"{c[0]} {c[1]}" for c in coordinates)
    return f"LINESTRING({points})"
