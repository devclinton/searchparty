"""Tests for trail data and OSM parsing."""

from app.importers.osm_trails import coords_to_wkt


def test_coords_to_wkt():
    coords = [[-121.69, 45.37], [-121.70, 45.38], [-121.71, 45.39]]
    wkt = coords_to_wkt(coords)
    assert wkt == "LINESTRING(-121.69 45.37, -121.7 45.38, -121.71 45.39)"


def test_coords_to_wkt_two_points():
    coords = [[-121.69, 45.37], [-121.70, 45.38]]
    wkt = coords_to_wkt(coords)
    assert "LINESTRING" in wkt
    assert "-121.69 45.37" in wkt


def test_coords_to_wkt_format():
    coords = [[0.0, 0.0], [1.0, 1.0]]
    wkt = coords_to_wkt(coords)
    assert wkt == "LINESTRING(0.0 0.0, 1.0 1.0)"
