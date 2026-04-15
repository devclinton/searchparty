"""Garmin FIT binary file parser using fitdecode."""

from datetime import UTC

import fitdecode

from app.importers.models import ImportedPoint, ImportedTrack, ImportResult


def parse_fit(content: bytes) -> ImportResult:
    """Parse a Garmin FIT binary file."""
    points: list[ImportedPoint] = []
    errors: list[str] = []
    device_name: str | None = None

    try:
        with fitdecode.FitReader(content) as reader:
            for frame in reader:
                if not isinstance(frame, fitdecode.FitDataMessage):
                    continue

                if frame.name == "device_info":
                    manufacturer = frame.get_value("manufacturer", fallback=None)
                    product = frame.get_value("garmin_product", fallback=None)
                    if manufacturer:
                        device_name = str(manufacturer)
                        if product:
                            device_name += f" {product}"

                if frame.name == "record":
                    lat_semi = frame.get_value("position_lat", fallback=None)
                    lon_semi = frame.get_value("position_long", fallback=None)

                    if lat_semi is None or lon_semi is None:
                        continue

                    # FIT uses semicircles; convert to degrees
                    lat = lat_semi * (180.0 / 2**31)
                    lon = lon_semi * (180.0 / 2**31)

                    altitude = frame.get_value("enhanced_altitude", fallback=None)
                    if altitude is None:
                        altitude = frame.get_value("altitude", fallback=None)

                    timestamp = frame.get_value("timestamp", fallback=None)
                    if timestamp and not timestamp.tzinfo:
                        timestamp = timestamp.replace(tzinfo=UTC)

                    points.append(
                        ImportedPoint(
                            lat=lat,
                            lon=lon,
                            altitude=altitude,
                            timestamp=timestamp,
                        )
                    )
    except Exception as e:
        errors.append(f"FIT parse error: {e}")

    tracks = []
    if points:
        tracks.append(
            ImportedTrack(
                name=device_name or "FIT Track",
                points=points,
                source_format="fit",
                source_device=device_name,
            )
        )

    return ImportResult(
        tracks=tracks,
        waypoints=[],
        total_points=len(points),
        source_format="fit",
        errors=errors,
    )
