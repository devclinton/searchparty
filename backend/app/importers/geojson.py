"""GeoJSON file parser."""

import json

from app.importers.models import ImportedPoint, ImportedTrack, ImportPointType, ImportResult


def parse_geojson(content: str | bytes) -> ImportResult:
    """Parse a GeoJSON file. Handles FeatureCollection, Feature, and bare geometries."""
    if isinstance(content, bytes):
        content = content.decode("utf-8")

    data = json.loads(content)
    tracks: list[ImportedTrack] = []
    waypoints: list[ImportedPoint] = []
    errors: list[str] = []
    total_points = 0

    features = []
    if data.get("type") == "FeatureCollection":
        features = data.get("features", [])
    elif data.get("type") == "Feature":
        features = [data]
    elif "coordinates" in data:
        features = [{"type": "Feature", "geometry": data, "properties": {}}]

    for feature in features:
        geom = feature.get("geometry", {})
        props = feature.get("properties", {}) or {}
        name = props.get("name") or props.get("title")
        geom_type = geom.get("type", "")
        coords = geom.get("coordinates", [])

        if geom_type == "Point" and len(coords) >= 2:
            waypoints.append(
                ImportedPoint(
                    lat=coords[1],
                    lon=coords[0],
                    altitude=coords[2] if len(coords) > 2 else None,
                    name=name,
                    point_type=ImportPointType.WAYPOINT,
                )
            )
            total_points += 1

        elif geom_type == "LineString":
            points = []
            for c in coords:
                if len(c) >= 2:
                    points.append(
                        ImportedPoint(
                            lat=c[1],
                            lon=c[0],
                            altitude=c[2] if len(c) > 2 else None,
                        )
                    )
                    total_points += 1
            if points:
                tracks.append(ImportedTrack(name=name, points=points, source_format="geojson"))

        elif geom_type == "MultiLineString":
            for line_idx, line in enumerate(coords):
                points = []
                for c in line:
                    if len(c) >= 2:
                        points.append(
                            ImportedPoint(
                                lat=c[1],
                                lon=c[0],
                                altitude=c[2] if len(c) > 2 else None,
                            )
                        )
                        total_points += 1
                if points:
                    track_name = f"{name} ({line_idx + 1})" if name else None
                    tracks.append(
                        ImportedTrack(name=track_name, points=points, source_format="geojson")
                    )

        elif geom_type == "MultiPoint":
            for c in coords:
                if len(c) >= 2:
                    waypoints.append(
                        ImportedPoint(
                            lat=c[1],
                            lon=c[0],
                            altitude=c[2] if len(c) > 2 else None,
                            name=name,
                            point_type=ImportPointType.WAYPOINT,
                        )
                    )
                    total_points += 1

    return ImportResult(
        tracks=tracks,
        waypoints=waypoints,
        total_points=total_points,
        source_format="geojson",
        errors=errors,
    )
