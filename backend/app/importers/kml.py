"""KML/KMZ file parser."""

import io
import xml.etree.ElementTree as ET
import zipfile

from app.importers.models import ImportedPoint, ImportedTrack, ImportPointType, ImportResult

KML_NS = {"kml": "http://www.opengis.net/kml/2.2"}


def _parse_coordinates(text: str) -> list[ImportedPoint]:
    """Parse KML coordinate string: 'lon,lat,alt lon,lat,alt ...'"""
    points = []
    for coord in text.strip().split():
        parts = coord.split(",")
        if len(parts) >= 2:
            lon = float(parts[0])
            lat = float(parts[1])
            alt = float(parts[2]) if len(parts) > 2 else None
            points.append(ImportedPoint(lat=lat, lon=lon, altitude=alt))
    return points


def parse_kml(content: str | bytes) -> ImportResult:
    """Parse a KML file."""
    if isinstance(content, bytes):
        content = content.decode("utf-8")

    root = ET.fromstring(content)  # noqa: S314
    ns = KML_NS

    tracks: list[ImportedTrack] = []
    waypoints: list[ImportedPoint] = []
    errors: list[str] = []
    total_points = 0

    # Find all Placemarks
    for pm in root.iter(f"{{{ns['kml']}}}Placemark"):
        name_elem = pm.find(f"{{{ns['kml']}}}name")
        name = name_elem.text if name_elem is not None and name_elem.text else None

        # LineString (track)
        ls = pm.find(f".//{{{ns['kml']}}}LineString/{{{ns['kml']}}}coordinates")
        if ls is not None and ls.text:
            points = _parse_coordinates(ls.text)
            total_points += len(points)
            if points:
                tracks.append(ImportedTrack(name=name, points=points, source_format="kml"))
            continue

        # Point (waypoint)
        pt = pm.find(f".//{{{ns['kml']}}}Point/{{{ns['kml']}}}coordinates")
        if pt is not None and pt.text:
            parsed = _parse_coordinates(pt.text)
            for p in parsed:
                p.name = name
                p.point_type = ImportPointType.WAYPOINT
                waypoints.append(p)
                total_points += 1

    return ImportResult(
        tracks=tracks,
        waypoints=waypoints,
        total_points=total_points,
        source_format="kml",
        errors=errors,
    )


def parse_kmz(content: bytes) -> ImportResult:
    """Parse a KMZ (zipped KML) file."""
    with zipfile.ZipFile(io.BytesIO(content)) as zf:
        for name in zf.namelist():
            if name.endswith(".kml"):
                kml_content = zf.read(name)
                return parse_kml(kml_content)
    return ImportResult(
        tracks=[],
        waypoints=[],
        total_points=0,
        source_format="kmz",
        errors=["No KML file found in KMZ archive"],
    )
