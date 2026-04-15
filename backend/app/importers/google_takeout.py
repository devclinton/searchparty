"""Google Takeout location history JSON parser.

Parses the JSON export from Google Takeout (Settings > Location History).
This is critical for SAR as it can reconstruct a missing person's
last known movements from their phone data.
"""

import json
from datetime import UTC, datetime

from app.importers.models import ImportedPoint, ImportedTrack, ImportResult


def parse_google_takeout(content: str | bytes) -> ImportResult:
    """Parse Google Takeout location history JSON."""
    if isinstance(content, bytes):
        content = content.decode("utf-8")

    data = json.loads(content)
    points: list[ImportedPoint] = []
    errors: list[str] = []

    # Google Takeout format has changed over time. Handle both formats.
    locations = []

    # New format (2024+): array of timeline objects
    if isinstance(data, list):
        locations = data
    # Old format: {"locations": [...]}
    elif "locations" in data:
        locations = data["locations"]
    # Semantic location history format
    elif "timelineObjects" in data:
        for obj in data["timelineObjects"]:
            if "activitySegment" in obj:
                seg = obj["activitySegment"]
                start = seg.get("startLocation", {})
                if "latitudeE7" in start:
                    locations.append(start)
            if "placeVisit" in obj:
                visit = obj["placeVisit"]
                loc = visit.get("location", {})
                if "latitudeE7" in loc:
                    locations.append(loc)

    for loc in locations:
        try:
            # Handle E7 format (integers * 10^7)
            if "latitudeE7" in loc:
                lat = loc["latitudeE7"] / 1e7
                lon = loc["longitudeE7"] / 1e7
            elif "latitude" in loc:
                lat = float(loc["latitude"])
                lon = float(loc["longitude"])
            else:
                continue

            altitude = loc.get("altitude")

            # Parse timestamp
            timestamp = None
            ts_str = loc.get("timestamp") or loc.get("timestampMs")
            if ts_str:
                if isinstance(ts_str, str) and ts_str.endswith("Z"):
                    timestamp = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                elif isinstance(ts_str, int | str):
                    ms = int(ts_str)
                    timestamp = datetime.fromtimestamp(ms / 1000, tz=UTC)

            accuracy = loc.get("accuracy")

            points.append(
                ImportedPoint(
                    lat=lat,
                    lon=lon,
                    altitude=altitude,
                    timestamp=timestamp,
                    accuracy=float(accuracy) if accuracy else None,
                )
            )
        except (ValueError, KeyError, TypeError) as e:
            errors.append(f"Error parsing location: {e}")

    # Sort by timestamp
    points.sort(key=lambda p: p.timestamp or datetime.min.replace(tzinfo=UTC))

    tracks = []
    if points:
        tracks.append(
            ImportedTrack(
                name="Google Location History",
                points=points,
                source_format="google_takeout",
                source_device="Google Account",
            )
        )

    return ImportResult(
        tracks=tracks,
        waypoints=[],
        total_points=len(points),
        source_format="google_takeout",
        errors=errors,
    )
