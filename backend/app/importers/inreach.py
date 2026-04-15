"""Garmin inReach MapShare KML feed integration.

Polls a Garmin MapShare URL for live position data from inReach devices.
MapShare provides a KML feed at:
  https://share.garmin.com/Feed/Share/<MapShareID>

This returns KML with Placemarks containing the latest positions.
"""

import httpx

from app.importers.kml import parse_kml
from app.importers.models import ImportResult


async def fetch_inreach_feed(mapshare_url: str) -> ImportResult:
    """Fetch and parse a Garmin inReach MapShare KML feed."""
    # Ensure we're hitting the KML feed endpoint
    if not mapshare_url.endswith("/Feed/Share"):
        # Extract the MapShare ID and construct the feed URL
        parts = mapshare_url.rstrip("/").split("/")
        share_id = parts[-1]
        mapshare_url = f"https://share.garmin.com/Feed/Share/{share_id}"

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(mapshare_url)
        response.raise_for_status()

    result = parse_kml(response.text)
    # Override source format
    result.source_format = "inreach"
    for track in result.tracks:
        track.source_format = "inreach"
        track.source_device = "Garmin inReach"

    return result
