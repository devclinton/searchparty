"""CSV coordinate file parser with auto-detect column mapping."""

import csv
import io
from datetime import UTC, datetime

from app.importers.models import ImportedPoint, ImportedTrack, ImportResult

# Common column name patterns for lat/lon
LAT_NAMES = {"lat", "latitude", "y", "lat_dd", "point_y"}
LON_NAMES = {"lon", "lng", "longitude", "long", "x", "lon_dd", "point_x"}
ALT_NAMES = {"alt", "altitude", "elevation", "ele", "z", "height"}
TIME_NAMES = {"time", "timestamp", "datetime", "date_time", "recorded_at", "utc_time"}
NAME_NAMES = {"name", "label", "title", "description", "id"}


def _detect_columns(headers: list[str]) -> dict[str, int | None]:
    """Auto-detect column indices from header names."""
    lower_headers = [h.strip().lower() for h in headers]
    mapping: dict[str, int | None] = {
        "lat": None,
        "lon": None,
        "alt": None,
        "time": None,
        "name": None,
    }

    for i, h in enumerate(lower_headers):
        if h in LAT_NAMES:
            mapping["lat"] = i
        elif h in LON_NAMES:
            mapping["lon"] = i
        elif h in ALT_NAMES:
            mapping["alt"] = i
        elif h in TIME_NAMES:
            mapping["time"] = i
        elif h in NAME_NAMES and mapping["name"] is None:
            mapping["name"] = i

    return mapping


def _parse_timestamp(value: str) -> datetime | None:
    for fmt in (
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%d %H:%M:%S",
        "%m/%d/%Y %H:%M:%S",
        "%Y-%m-%d",
    ):
        try:
            dt = datetime.strptime(value.strip(), fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=UTC)
            return dt
        except ValueError:
            continue
    return None


def parse_csv(content: str | bytes) -> ImportResult:
    """Parse a CSV file with lat/lon columns."""
    if isinstance(content, bytes):
        content = content.decode("utf-8")

    reader = csv.reader(io.StringIO(content))
    points: list[ImportedPoint] = []
    errors: list[str] = []

    headers = next(reader, None)
    if headers is None:
        return ImportResult(
            tracks=[],
            waypoints=[],
            total_points=0,
            source_format="csv",
            errors=["Empty CSV file"],
        )

    mapping = _detect_columns(headers)

    if mapping["lat"] is None or mapping["lon"] is None:
        return ImportResult(
            tracks=[],
            waypoints=[],
            total_points=0,
            source_format="csv",
            errors=[f"Could not detect lat/lon columns from headers: {headers}"],
        )

    for row_num, row in enumerate(reader, start=2):
        try:
            lat = float(row[mapping["lat"]])
            lon = float(row[mapping["lon"]])

            altitude = None
            if mapping["alt"] is not None and mapping["alt"] < len(row):
                val = row[mapping["alt"]].strip()
                if val:
                    altitude = float(val)

            timestamp = None
            if mapping["time"] is not None and mapping["time"] < len(row):
                val = row[mapping["time"]].strip()
                if val:
                    timestamp = _parse_timestamp(val)

            name = None
            if mapping["name"] is not None and mapping["name"] < len(row):
                name = row[mapping["name"]].strip() or None

            points.append(
                ImportedPoint(lat=lat, lon=lon, altitude=altitude, timestamp=timestamp, name=name)
            )
        except (ValueError, IndexError) as e:
            errors.append(f"Row {row_num}: {e}")

    tracks = []
    if points:
        tracks.append(ImportedTrack(name="CSV Import", points=points, source_format="csv"))

    return ImportResult(
        tracks=tracks,
        waypoints=[],
        total_points=len(points),
        source_format="csv",
        errors=errors,
    )
