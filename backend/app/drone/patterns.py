"""Drone search pattern generators for SAR operations.

Generates waypoint lists for common SAR search patterns that can be
exported to various drone flight plan formats.
"""

import math
from dataclasses import dataclass


@dataclass
class Waypoint:
    lat: float
    lon: float
    altitude_m: float
    speed_ms: float = 5.0
    gimbal_pitch: float = -90.0
    action: str = "fly"  # fly, hover, photo, start_video, stop_video


def _offset_point(lat: float, lon: float, north_m: float, east_m: float) -> tuple[float, float]:
    """Offset a lat/lon by meters north and east."""
    lat_offset = north_m / 111320.0
    lon_offset = east_m / (111320.0 * math.cos(math.radians(lat)))
    return lat + lat_offset, lon + lon_offset


def _bbox_dimensions(
    north: float, south: float, east: float, west: float, center_lat: float
) -> tuple[float, float]:
    """Calculate bounding box width and height in meters."""
    height_m = (north - south) * 111320.0
    width_m = (east - west) * 111320.0 * math.cos(math.radians(center_lat))
    return width_m, height_m


def parallel_track(
    bounds: dict,
    altitude_m: float = 50.0,
    spacing_m: float = 20.0,
    speed_ms: float = 5.0,
    gimbal_pitch: float = -90.0,
    heading_deg: float = 0.0,
) -> list[Waypoint]:
    """Generate a parallel track (lawnmower) pattern.

    Args:
        bounds: dict with north, south, east, west
        altitude_m: flight altitude AGL
        spacing_m: lateral distance between tracks (from FOV calculator)
        speed_ms: flight speed in m/s
        gimbal_pitch: camera gimbal angle (-90 = nadir)
        heading_deg: primary heading for tracks (0 = N-S, 90 = E-W)
    """
    north, south = bounds["north"], bounds["south"]
    east, west = bounds["east"], bounds["west"]
    center_lat = (north + south) / 2
    center_lon = (east + west) / 2
    width_m, height_m = _bbox_dimensions(north, south, east, west, center_lat)

    heading_rad = math.radians(heading_deg)
    cos_h, sin_h = math.cos(heading_rad), math.sin(heading_rad)

    # Calculate number of tracks
    cross_dim = width_m * abs(cos_h) + height_m * abs(sin_h)
    along_dim = width_m * abs(sin_h) + height_m * abs(cos_h)
    num_tracks = max(1, int(math.ceil(cross_dim / spacing_m)))

    waypoints: list[Waypoint] = []
    half_along = along_dim / 2
    half_cross = cross_dim / 2

    for i in range(num_tracks):
        cross_offset = -half_cross + i * spacing_m
        reverse = i % 2 == 1

        # Start and end of this track in local coordinates
        start_along = -half_along if not reverse else half_along
        end_along = half_along if not reverse else -half_along

        for along in [start_along, end_along]:
            north_m = along * cos_h - cross_offset * sin_h
            east_m = along * sin_h + cross_offset * cos_h
            lat, lon = _offset_point(center_lat, center_lon, north_m, east_m)
            waypoints.append(
                Waypoint(
                    lat=lat,
                    lon=lon,
                    altitude_m=altitude_m,
                    speed_ms=speed_ms,
                    gimbal_pitch=gimbal_pitch,
                )
            )

    return waypoints


def expanding_square(
    center_lat: float,
    center_lon: float,
    altitude_m: float = 50.0,
    spacing_m: float = 20.0,
    max_radius_m: float = 500.0,
    speed_ms: float = 5.0,
    gimbal_pitch: float = -90.0,
) -> list[Waypoint]:
    """Generate an expanding square pattern from a center point (IPP).

    Spirals outward in a square pattern with each leg increasing by spacing_m.
    """
    waypoints: list[Waypoint] = []
    waypoints.append(
        Waypoint(
            lat=center_lat,
            lon=center_lon,
            altitude_m=altitude_m,
            speed_ms=speed_ms,
            gimbal_pitch=gimbal_pitch,
            action="start_video",
        )
    )

    current_lat, current_lon = center_lat, center_lon
    leg_num = 0
    # Directions: E, N, W, S (right, up, left, down)
    directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]

    distance = spacing_m
    while distance <= max_radius_m * 2:
        dir_idx = leg_num % 4
        north_dir, east_dir = directions[dir_idx]
        leg_length = distance

        end_lat, end_lon = _offset_point(
            current_lat,
            current_lon,
            north_dir * leg_length,
            east_dir * leg_length,
        )
        waypoints.append(
            Waypoint(
                lat=end_lat,
                lon=end_lon,
                altitude_m=altitude_m,
                speed_ms=speed_ms,
                gimbal_pitch=gimbal_pitch,
            )
        )
        current_lat, current_lon = end_lat, end_lon

        leg_num += 1
        if leg_num % 2 == 0:
            distance += spacing_m

    return waypoints


def sector_search(
    center_lat: float,
    center_lon: float,
    radius_m: float = 300.0,
    altitude_m: float = 50.0,
    num_sectors: int = 6,
    speed_ms: float = 5.0,
    gimbal_pitch: float = -90.0,
) -> list[Waypoint]:
    """Generate a sector search (pie-slice sweeps from center).

    Sweeps out from center to radius along evenly spaced radial lines,
    returning to center between each sweep.
    """
    waypoints: list[Waypoint] = []
    angle_step = 360.0 / num_sectors

    for i in range(num_sectors):
        angle = math.radians(i * angle_step)
        # Go to center
        waypoints.append(
            Waypoint(
                lat=center_lat,
                lon=center_lon,
                altitude_m=altitude_m,
                speed_ms=speed_ms,
                gimbal_pitch=gimbal_pitch,
            )
        )
        # Fly to edge
        north_m = radius_m * math.cos(angle)
        east_m = radius_m * math.sin(angle)
        lat, lon = _offset_point(center_lat, center_lon, north_m, east_m)
        waypoints.append(
            Waypoint(
                lat=lat,
                lon=lon,
                altitude_m=altitude_m,
                speed_ms=speed_ms,
                gimbal_pitch=gimbal_pitch,
            )
        )

    # Return to center
    waypoints.append(
        Waypoint(
            lat=center_lat,
            lon=center_lon,
            altitude_m=altitude_m,
            speed_ms=speed_ms,
            gimbal_pitch=gimbal_pitch,
        )
    )
    return waypoints


def creeping_line(
    bounds: dict,
    advance_heading_deg: float = 0.0,
    altitude_m: float = 50.0,
    spacing_m: float = 20.0,
    speed_ms: float = 5.0,
    gimbal_pitch: float = -90.0,
) -> list[Waypoint]:
    """Generate a creeping line ahead pattern.

    Like parallel track but perpendicular to the likely travel direction,
    advancing toward the probable direction of the subject.
    The advance_heading is the direction the subject likely traveled.
    Tracks run perpendicular to this, advancing in that direction.
    """
    # Creeping line is essentially parallel track with heading perpendicular
    # to the advance direction
    track_heading = (advance_heading_deg + 90) % 360
    return parallel_track(bounds, altitude_m, spacing_m, speed_ms, gimbal_pitch, track_heading)


def estimate_flight_time(waypoints: list[Waypoint]) -> float:
    """Estimate total flight time in seconds for a waypoint sequence."""
    if len(waypoints) < 2:
        return 0.0
    total_time = 0.0
    for i in range(1, len(waypoints)):
        prev, curr = waypoints[i - 1], waypoints[i]
        dlat = (curr.lat - prev.lat) * 111320.0
        dlon = (curr.lon - prev.lon) * 111320.0 * math.cos(math.radians(prev.lat))
        dist = math.sqrt(dlat * dlat + dlon * dlon)
        speed = curr.speed_ms if curr.speed_ms > 0 else 5.0
        total_time += dist / speed
    return total_time
