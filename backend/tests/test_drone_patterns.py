"""Tests for drone search patterns, FOV calculator, exporters, and SRT parser."""

import json

from app.drone.camera import (
    CAMERA_PRESETS,
    calculate_fov,
    ground_coverage,
    gsd,
    track_spacing,
)
from app.drone.exporters import export_kml, export_litchi_csv, export_mavlink, export_wpml
from app.drone.patterns import (
    Waypoint,
    creeping_line,
    estimate_flight_time,
    expanding_square,
    parallel_track,
    sector_search,
)
from app.drone.srt_parser import parse_srt

# --- Camera FOV ---


def test_calculate_fov_with_override():
    cam = CAMERA_PRESETS["dji_m3e"]
    fov_h, fov_v = calculate_fov(cam)
    assert fov_h == 84.0
    assert fov_v > 0


def test_ground_coverage_nadir():
    width, height = ground_coverage(100.0, 84.0, 60.0, -90.0)
    assert width > 150  # At 100m with 84deg FOV, width > 150m
    assert height > 100


def test_track_spacing_with_overlap():
    cam = CAMERA_PRESETS["dji_m3e"]
    spacing = track_spacing(50.0, cam, 70.0)
    assert spacing > 0
    # With 70% overlap, spacing should be ~30% of swath width
    fov_h, _ = calculate_fov(cam)
    width, _ = ground_coverage(50.0, fov_h, 0)
    assert spacing < width


def test_gsd_increases_with_altitude():
    cam = CAMERA_PRESETS["dji_m3e"]
    gsd_low = gsd(30.0, cam)
    gsd_high = gsd(100.0, cam)
    assert gsd_high > gsd_low


def test_all_presets_have_valid_fov():
    for key, cam in CAMERA_PRESETS.items():
        fov_h, fov_v = calculate_fov(cam)
        assert 20 < fov_h < 180, f"{key} FOV_H out of range"
        assert fov_v > 0, f"{key} FOV_V invalid"


# --- Search Patterns ---


def test_parallel_track_generates_waypoints():
    bounds = {"north": 45.38, "south": 45.37, "east": -121.69, "west": -121.70}
    wps = parallel_track(bounds, altitude_m=50.0, spacing_m=30.0)
    assert len(wps) >= 4
    assert all(isinstance(w, Waypoint) for w in wps)


def test_parallel_track_altitude():
    bounds = {"north": 45.38, "south": 45.37, "east": -121.69, "west": -121.70}
    wps = parallel_track(bounds, altitude_m=75.0)
    assert all(w.altitude_m == 75.0 for w in wps)


def test_expanding_square_from_center():
    wps = expanding_square(45.3735, -121.6959, altitude_m=50.0, spacing_m=20.0)
    assert len(wps) > 4
    # First waypoint should be at center
    assert abs(wps[0].lat - 45.3735) < 0.0001
    assert abs(wps[0].lon - (-121.6959)) < 0.0001


def test_sector_search_returns_to_center():
    wps = sector_search(45.37, -121.69, radius_m=200.0, num_sectors=4)
    # Should return to center between sectors
    center_count = sum(
        1 for w in wps if abs(w.lat - 45.37) < 0.0001 and abs(w.lon - (-121.69)) < 0.0001
    )
    assert center_count >= 4  # At least once per sector


def test_creeping_line_is_rotated_parallel():
    bounds = {"north": 45.38, "south": 45.37, "east": -121.69, "west": -121.70}
    wps = creeping_line(bounds, advance_heading_deg=90.0)
    assert len(wps) >= 4


def test_estimate_flight_time():
    wps = [
        Waypoint(lat=45.37, lon=-121.69, altitude_m=50, speed_ms=10),
        Waypoint(lat=45.38, lon=-121.69, altitude_m=50, speed_ms=10),
    ]
    time_s = estimate_flight_time(wps)
    # ~1.1km at 10m/s = ~110 seconds
    assert 80 < time_s < 150


# --- Exporters ---


def test_export_wpml():
    wps = [Waypoint(lat=45.37, lon=-121.69, altitude_m=50)]
    xml = export_wpml(wps, "Test Mission")
    assert "<?xml" in xml
    assert "wpml:" in xml
    assert "45.37" in xml


def test_export_mavlink():
    wps = [Waypoint(lat=45.37, lon=-121.69, altitude_m=50)]
    plan_str = export_mavlink(wps)
    plan = json.loads(plan_str)
    assert plan["fileType"] == "Plan"
    assert len(plan["mission"]["items"]) >= 3  # Takeoff + waypoint + RTL


def test_export_kml():
    wps = [
        Waypoint(lat=45.37, lon=-121.69, altitude_m=50),
        Waypoint(lat=45.38, lon=-121.70, altitude_m=50),
    ]
    kml = export_kml(wps, "SAR Mission")
    assert "<kml" in kml
    assert "SAR Mission" in kml
    assert "45.37" in kml


def test_export_litchi_csv():
    wps = [
        Waypoint(lat=45.37, lon=-121.69, altitude_m=50, speed_ms=5),
        Waypoint(lat=45.38, lon=-121.70, altitude_m=50, speed_ms=5),
    ]
    csv = export_litchi_csv(wps)
    lines = csv.strip().split("\n")
    assert len(lines) == 3  # Header + 2 waypoints
    assert "latitude" in lines[0]


# --- SRT Parser ---

SRT_SAMPLE = """1
00:00:00,000 --> 00:00:00,033
<font size="28">SrtCnt : 1, DiffTime : 33ms
2024-03-15 14:30:00.000
[iso : 100] [shutter : 1/640.0]
[latitude: 45.3735] [longitude: -121.6959] [altitude: 1200.0]
[gb_yaw: 15.0] [gb_pitch: -90.0] [gb_roll: 0.0]
</font>

2
00:00:00,033 --> 00:00:00,066
<font size="28">SrtCnt : 2, DiffTime : 33ms
2024-03-15 14:30:00.033
[iso : 100] [shutter : 1/640.0]
[latitude: 45.3736] [longitude: -121.6958] [altitude: 1201.0]
[gb_yaw: 15.0] [gb_pitch: -89.5] [gb_roll: 0.0]
</font>"""


def test_srt_parse_frames():
    frames = parse_srt(SRT_SAMPLE)
    assert len(frames) == 2


def test_srt_parse_gps():
    frames = parse_srt(SRT_SAMPLE)
    assert frames[0].lat == 45.3735
    assert frames[0].lon == -121.6959
    assert frames[0].altitude == 1200.0


def test_srt_parse_gimbal():
    frames = parse_srt(SRT_SAMPLE)
    assert frames[0].gimbal_pitch == -90.0
    assert frames[0].gimbal_yaw == 15.0


def test_srt_parse_timestamps():
    frames = parse_srt(SRT_SAMPLE)
    assert frames[0].timestamp_ms == 0
    assert frames[1].timestamp_ms == 33
