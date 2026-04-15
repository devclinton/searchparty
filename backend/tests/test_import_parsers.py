"""Tests for GPS import file parsers."""

from app.importers.csv_import import parse_csv
from app.importers.geojson import parse_geojson
from app.importers.google_takeout import parse_google_takeout
from app.importers.gpx import parse_gpx
from app.importers.kml import parse_kml

# --- GPX ---

GPX_SAMPLE = """<?xml version="1.0" encoding="UTF-8"?>
<gpx version="1.1" xmlns="http://www.topografix.com/GPX/1/1">
  <trk>
    <name>Morning Hike</name>
    <trkseg>
      <trkpt lat="45.3735" lon="-121.6959">
        <ele>1200</ele>
        <time>2026-04-13T10:00:00Z</time>
      </trkpt>
      <trkpt lat="45.3740" lon="-121.6950">
        <ele>1210</ele>
        <time>2026-04-13T10:05:00Z</time>
      </trkpt>
    </trkseg>
  </trk>
  <wpt lat="45.3730" lon="-121.6960">
    <name>Trailhead</name>
    <ele>1190</ele>
  </wpt>
</gpx>"""


def test_gpx_parse_tracks():
    result = parse_gpx(GPX_SAMPLE)
    assert result.source_format == "gpx"
    assert len(result.tracks) == 1
    assert result.tracks[0].name == "Morning Hike"
    assert len(result.tracks[0].points) == 2
    assert result.tracks[0].points[0].lat == 45.3735
    assert result.tracks[0].points[0].altitude == 1200


def test_gpx_parse_waypoints():
    result = parse_gpx(GPX_SAMPLE)
    assert len(result.waypoints) == 1
    assert result.waypoints[0].name == "Trailhead"
    assert result.waypoints[0].point_type == "waypoint"


def test_gpx_total_points():
    result = parse_gpx(GPX_SAMPLE)
    assert result.total_points == 3


def test_gpx_handles_bytes():
    result = parse_gpx(GPX_SAMPLE.encode("utf-8"))
    assert len(result.tracks) == 1


# --- KML ---

KML_SAMPLE = """<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
  <Document>
    <Placemark>
      <name>Trail Route</name>
      <LineString>
        <coordinates>-121.6959,45.3735,1200 -121.6950,45.3740,1210</coordinates>
      </LineString>
    </Placemark>
    <Placemark>
      <name>Camp Site</name>
      <Point>
        <coordinates>-121.6955,45.3738,1205</coordinates>
      </Point>
    </Placemark>
  </Document>
</kml>"""


def test_kml_parse_tracks():
    result = parse_kml(KML_SAMPLE)
    assert len(result.tracks) == 1
    assert result.tracks[0].name == "Trail Route"
    assert len(result.tracks[0].points) == 2


def test_kml_parse_waypoints():
    result = parse_kml(KML_SAMPLE)
    assert len(result.waypoints) == 1
    assert result.waypoints[0].name == "Camp Site"


# --- GeoJSON ---


def test_geojson_linestring():
    content = """{
        "type": "Feature",
        "properties": {"name": "My Track"},
        "geometry": {
            "type": "LineString",
            "coordinates": [[-121.69, 45.37, 1200], [-121.70, 45.38, 1210]]
        }
    }"""
    result = parse_geojson(content)
    assert len(result.tracks) == 1
    assert result.tracks[0].name == "My Track"
    assert result.total_points == 2


def test_geojson_point():
    content = """{
        "type": "Feature",
        "properties": {"name": "Marker"},
        "geometry": {"type": "Point", "coordinates": [-121.69, 45.37]}
    }"""
    result = parse_geojson(content)
    assert len(result.waypoints) == 1
    assert result.waypoints[0].lat == 45.37


def test_geojson_feature_collection():
    content = """{
        "type": "FeatureCollection",
        "features": [
            {"type": "Feature", "properties": {}, "geometry":
                {"type": "LineString", "coordinates": [[-121.69, 45.37], [-121.70, 45.38]]}},
            {"type": "Feature", "properties": {"name": "WP"}, "geometry":
                {"type": "Point", "coordinates": [-121.69, 45.37]}}
        ]
    }"""
    result = parse_geojson(content)
    assert len(result.tracks) == 1
    assert len(result.waypoints) == 1


# --- Google Takeout ---


def test_google_takeout_old_format():
    content = (
        '{"locations": ['
        '{"latitudeE7": 453735000, "longitudeE7": -1216959000,'
        ' "timestampMs": "1681380000000", "accuracy": 10},'
        '{"latitudeE7": 453740000, "longitudeE7": -1216950000,'
        ' "timestampMs": "1681380300000", "accuracy": 8}'
        "]}"
    )
    result = parse_google_takeout(content)
    assert len(result.tracks) == 1
    assert result.total_points == 2
    assert abs(result.tracks[0].points[0].lat - 45.3735) < 0.001


def test_google_takeout_empty():
    result = parse_google_takeout('{"locations": []}')
    assert result.total_points == 0
    assert len(result.tracks) == 0


# --- CSV ---


def test_csv_basic():
    content = "lat,lon,altitude\n45.3735,-121.6959,1200\n45.3740,-121.6950,1210"
    result = parse_csv(content)
    assert len(result.tracks) == 1
    assert result.total_points == 2
    assert result.tracks[0].points[0].lat == 45.3735


def test_csv_alternate_headers():
    content = "latitude,longitude,elevation,timestamp\n45.37,-121.69,1200,2026-04-13T10:00:00Z"
    result = parse_csv(content)
    assert result.total_points == 1
    assert result.tracks[0].points[0].altitude == 1200
    assert result.tracks[0].points[0].timestamp is not None


def test_csv_no_lat_lon():
    content = "name,value\nfoo,bar"
    result = parse_csv(content)
    assert result.total_points == 0
    assert len(result.errors) > 0


def test_csv_with_bad_rows():
    content = "lat,lon\n45.37,-121.69\nnot_a_number,bad\n45.38,-121.70"
    result = parse_csv(content)
    assert result.total_points == 2
    assert len(result.errors) == 1  # One bad row
