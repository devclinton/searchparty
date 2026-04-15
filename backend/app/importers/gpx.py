"""GPX file parser."""

import xml.etree.ElementTree as ET
from datetime import UTC, datetime

from app.importers.models import ImportedPoint, ImportedTrack, ImportPointType, ImportResult

GPX_NS = {"gpx": "http://www.topografix.com/GPX/1/1"}
GPX_NS_10 = {"gpx": "http://www.topografix.com/GPX/1/0"}


def _find_ns(root: ET.Element) -> dict[str, str]:
    """Detect GPX namespace version."""
    tag = root.tag
    if "1/1" in tag:
        return GPX_NS
    if "1/0" in tag:
        return GPX_NS_10
    # Try without namespace
    return {}


def _parse_time(elem: ET.Element | None) -> datetime | None:
    if elem is None or elem.text is None:
        return None
    text = elem.text.strip()
    for fmt in ("%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%dT%H:%M:%S%z"):
        try:
            return datetime.strptime(text, fmt).replace(tzinfo=UTC)
        except ValueError:
            continue
    return None


def parse_gpx(content: str | bytes) -> ImportResult:
    """Parse a GPX file and extract tracks and waypoints."""
    if isinstance(content, bytes):
        content = content.decode("utf-8")

    root = ET.fromstring(content)  # noqa: S314
    ns = _find_ns(root)
    prefix = "gpx:" if ns else ""

    tracks: list[ImportedTrack] = []
    waypoints: list[ImportedPoint] = []
    errors: list[str] = []
    total_points = 0

    # Parse tracks
    for trk in root.findall(f"{prefix}trk", ns):
        name_elem = trk.find(f"{prefix}name", ns)
        track_name = name_elem.text if name_elem is not None and name_elem.text else None
        points: list[ImportedPoint] = []

        for trkseg in trk.findall(f"{prefix}trkseg", ns):
            for trkpt in trkseg.findall(f"{prefix}trkpt", ns):
                try:
                    lat = float(trkpt.get("lat", "0"))
                    lon = float(trkpt.get("lon", "0"))
                    ele_elem = trkpt.find(f"{prefix}ele", ns)
                    altitude = (
                        float(ele_elem.text) if ele_elem is not None and ele_elem.text else None
                    )
                    time = _parse_time(trkpt.find(f"{prefix}time", ns))
                    points.append(
                        ImportedPoint(lat=lat, lon=lon, altitude=altitude, timestamp=time)
                    )
                    total_points += 1
                except (ValueError, TypeError) as e:
                    errors.append(f"Error parsing trackpoint: {e}")

        if points:
            tracks.append(
                ImportedTrack(
                    name=track_name,
                    points=points,
                    source_format="gpx",
                )
            )

    # Parse waypoints
    for wpt in root.findall(f"{prefix}wpt", ns):
        try:
            lat = float(wpt.get("lat", "0"))
            lon = float(wpt.get("lon", "0"))
            ele_elem = wpt.find(f"{prefix}ele", ns)
            altitude = float(ele_elem.text) if ele_elem is not None and ele_elem.text else None
            name_elem = wpt.find(f"{prefix}name", ns)
            name = name_elem.text if name_elem is not None else None
            time = _parse_time(wpt.find(f"{prefix}time", ns))
            waypoints.append(
                ImportedPoint(
                    lat=lat,
                    lon=lon,
                    altitude=altitude,
                    timestamp=time,
                    name=name,
                    point_type=ImportPointType.WAYPOINT,
                )
            )
            total_points += 1
        except (ValueError, TypeError) as e:
            errors.append(f"Error parsing waypoint: {e}")

    return ImportResult(
        tracks=tracks,
        waypoints=waypoints,
        total_points=total_points,
        source_format="gpx",
        errors=errors,
    )
