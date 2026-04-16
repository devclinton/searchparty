"""Camera FOV and track spacing calculator for drone search patterns.

Calculates ground coverage from camera parameters and flight altitude
to determine optimal track spacing for search patterns.
"""

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class CameraProfile:
    name: str
    drone_model: str
    sensor_width_mm: float
    sensor_height_mm: float
    focal_length_mm: float
    image_width_px: int
    image_height_px: int
    has_thermal: bool = False
    fov_h_deg: float | None = None  # Override if known
    fov_v_deg: float | None = None


# Common SAR drone camera presets
CAMERA_PRESETS: dict[str, CameraProfile] = {
    "dji_m3e": CameraProfile(
        name="DJI Mavic 3 Enterprise (Wide)",
        drone_model="DJI Mavic 3 Enterprise",
        sensor_width_mm=17.3,
        sensor_height_mm=13.0,
        focal_length_mm=12.3,
        image_width_px=5280,
        image_height_px=3956,
        fov_h_deg=84.0,
    ),
    "dji_m3t_thermal": CameraProfile(
        name="DJI Mavic 3T Thermal",
        drone_model="DJI Mavic 3 Thermal",
        sensor_width_mm=7.68,
        sensor_height_mm=6.14,
        focal_length_mm=9.1,
        image_width_px=640,
        image_height_px=512,
        has_thermal=True,
        fov_h_deg=61.0,
    ),
    "dji_m30t_wide": CameraProfile(
        name="DJI Matrice 30T (Wide)",
        drone_model="DJI Matrice 30T",
        sensor_width_mm=9.6,
        sensor_height_mm=7.2,
        focal_length_mm=7.0,
        image_width_px=4000,
        image_height_px=3000,
        fov_h_deg=84.0,
    ),
    "dji_m30t_thermal": CameraProfile(
        name="DJI Matrice 30T (Thermal)",
        drone_model="DJI Matrice 30T",
        sensor_width_mm=7.68,
        sensor_height_mm=6.14,
        focal_length_mm=9.1,
        image_width_px=640,
        image_height_px=512,
        has_thermal=True,
        fov_h_deg=61.0,
    ),
    "dji_m350_h20t": CameraProfile(
        name="DJI Matrice 350 RTK + H20T",
        drone_model="DJI Matrice 350 RTK",
        sensor_width_mm=6.4,
        sensor_height_mm=4.8,
        focal_length_mm=6.83,
        image_width_px=4056,
        image_height_px=3040,
        fov_h_deg=82.9,
    ),
    "autel_evo2_dual": CameraProfile(
        name="Autel EVO II Dual 640T",
        drone_model="Autel EVO II Dual 640T",
        sensor_width_mm=12.8,
        sensor_height_mm=9.6,
        focal_length_mm=8.6,
        image_width_px=8000,
        image_height_px=6000,
        fov_h_deg=79.0,
    ),
    "skydio_x10": CameraProfile(
        name="Skydio X10 (Wide)",
        drone_model="Skydio X10",
        sensor_width_mm=9.6,
        sensor_height_mm=7.2,
        focal_length_mm=4.5,
        image_width_px=8064,
        image_height_px=6048,
        fov_h_deg=93.0,
    ),
    "parrot_anafi_usa": CameraProfile(
        name="Parrot ANAFI USA",
        drone_model="Parrot ANAFI USA",
        sensor_width_mm=6.17,
        sensor_height_mm=4.55,
        focal_length_mm=7.5,
        image_width_px=5344,
        image_height_px=4016,
        fov_h_deg=75.5,
    ),
}


def calculate_fov(camera: CameraProfile) -> tuple[float, float]:
    """Calculate horizontal and vertical FOV in degrees."""
    if camera.fov_h_deg and camera.fov_v_deg:
        return camera.fov_h_deg, camera.fov_v_deg

    fov_h = camera.fov_h_deg or (
        2 * math.degrees(math.atan(camera.sensor_width_mm / (2 * camera.focal_length_mm)))
    )
    fov_v = camera.fov_v_deg or (
        2 * math.degrees(math.atan(camera.sensor_height_mm / (2 * camera.focal_length_mm)))
    )
    return fov_h, fov_v


def ground_coverage(
    altitude_m: float,
    fov_h_deg: float,
    fov_v_deg: float,
    gimbal_pitch_deg: float = -90.0,
) -> tuple[float, float]:
    """Calculate ground coverage width and height in meters at given altitude.

    For nadir (gimbal_pitch=-90), this is straightforward trigonometry.
    For oblique angles, the footprint expands asymmetrically.
    """
    if gimbal_pitch_deg == -90.0:
        width = 2 * altitude_m * math.tan(math.radians(fov_h_deg / 2))
        height = 2 * altitude_m * math.tan(math.radians(fov_v_deg / 2))
        return width, height

    # Oblique: approximate by using the center-ground distance
    pitch_rad = math.radians(abs(gimbal_pitch_deg))
    ground_dist = altitude_m / math.sin(pitch_rad) if pitch_rad > 0.1 else altitude_m
    width = 2 * ground_dist * math.tan(math.radians(fov_h_deg / 2))
    height = 2 * ground_dist * math.tan(math.radians(fov_v_deg / 2))
    return width, height


def track_spacing(
    altitude_m: float,
    camera: CameraProfile,
    overlap_percent: float = 70.0,
    gimbal_pitch_deg: float = -90.0,
) -> float:
    """Calculate optimal track spacing in meters for a search pattern.

    Returns the lateral distance between parallel tracks that achieves
    the specified overlap percentage.
    """
    fov_h, fov_v = calculate_fov(camera)
    width, _ = ground_coverage(altitude_m, fov_h, fov_v, gimbal_pitch_deg)
    spacing = width * (1 - overlap_percent / 100.0)
    return max(spacing, 1.0)  # Minimum 1m spacing


def gsd(altitude_m: float, camera: CameraProfile) -> float:
    """Calculate Ground Sample Distance (cm/pixel) at given altitude."""
    fov_h, _ = calculate_fov(camera)
    width = 2 * altitude_m * math.tan(math.radians(fov_h / 2))
    gsd_m = width / camera.image_width_px
    return gsd_m * 100  # Convert to cm
