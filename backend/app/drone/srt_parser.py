"""DJI SRT subtitle file parser for video telemetry.

DJI drones create .SRT sidecar files alongside video recordings that
contain per-frame telemetry: GPS coordinates, altitude, gimbal angles,
ISO, shutter speed, and more.

Format example:
1
00:00:00,000 --> 00:00:00,033
<font size="28">SrtCnt : 1, DiffTime : 33ms
2024-03-15 14:30:00.000
[iso : 100] [shutter : 1/640.0] [fnum : 280] [ev : 0]
[latitude: 45.3735] [longitude: -121.6959] [altitude: 1200.0]
[ct : 5600] [color_md : default]
[focal_len : 24.00] [dzoom_ratio: 10000]
[gb_yaw: 0.0] [gb_pitch: -90.0] [gb_roll: 0.0]
</font>
"""

import re
from dataclasses import dataclass


@dataclass
class SrtFrame:
    index: int
    timestamp_ms: int
    lat: float | None = None
    lon: float | None = None
    altitude: float | None = None
    gimbal_yaw: float | None = None
    gimbal_pitch: float | None = None
    gimbal_roll: float | None = None
    iso: int | None = None
    shutter: str | None = None
    focal_length: float | None = None


def _parse_time_ms(time_str: str) -> int:
    """Parse SRT timestamp to milliseconds."""
    parts = time_str.strip().split(":")
    if len(parts) == 3:
        h, m, s_ms = int(parts[0]), int(parts[1]), parts[2]
        if "," in s_ms:
            s, ms = s_ms.split(",")
        elif "." in s_ms:
            s, ms = s_ms.split(".")
        else:
            s, ms = s_ms, "0"
        return h * 3600000 + m * 60000 + int(s) * 1000 + int(ms)
    return 0


def parse_srt(content: str) -> list[SrtFrame]:
    """Parse a DJI SRT file and extract per-frame telemetry."""
    frames: list[SrtFrame] = []

    # Split into subtitle blocks (separated by blank lines)
    blocks = re.split(r"\n\s*\n", content.strip())

    for block in blocks:
        lines = block.strip().split("\n")
        if len(lines) < 2:
            continue

        # First line: index
        try:
            index = int(lines[0].strip())
        except ValueError:
            continue

        # Second line: timestamp range
        time_match = re.match(r"(\d+:\d+:\d+[,.]\d+)\s*-->\s*(\d+:\d+:\d+[,.]\d+)", lines[1])
        if not time_match:
            continue
        timestamp_ms = _parse_time_ms(time_match.group(1))

        # Remaining lines: telemetry data
        text = " ".join(lines[2:])

        frame = SrtFrame(index=index, timestamp_ms=timestamp_ms)

        # Extract values using regex
        lat_match = re.search(r"\[latitude[:\s]+([+-]?\d+\.?\d*)\]", text, re.IGNORECASE)
        lon_match = re.search(r"\[longitude[:\s]+([+-]?\d+\.?\d*)\]", text, re.IGNORECASE)
        alt_match = re.search(r"\[altitude[:\s]+([+-]?\d+\.?\d*)\]", text, re.IGNORECASE)
        yaw_match = re.search(r"\[gb_yaw[:\s]+([+-]?\d+\.?\d*)\]", text, re.IGNORECASE)
        pitch_match = re.search(r"\[gb_pitch[:\s]+([+-]?\d+\.?\d*)\]", text, re.IGNORECASE)
        roll_match = re.search(r"\[gb_roll[:\s]+([+-]?\d+\.?\d*)\]", text, re.IGNORECASE)
        iso_match = re.search(r"\[iso[:\s]+(\d+)\]", text, re.IGNORECASE)
        shutter_match = re.search(r"\[shutter[:\s]+([^\]]+)\]", text, re.IGNORECASE)
        focal_match = re.search(r"\[focal_len[:\s]+([+-]?\d+\.?\d*)\]", text, re.IGNORECASE)

        if lat_match:
            frame.lat = float(lat_match.group(1))
        if lon_match:
            frame.lon = float(lon_match.group(1))
        if alt_match:
            frame.altitude = float(alt_match.group(1))
        if yaw_match:
            frame.gimbal_yaw = float(yaw_match.group(1))
        if pitch_match:
            frame.gimbal_pitch = float(pitch_match.group(1))
        if roll_match:
            frame.gimbal_roll = float(roll_match.group(1))
        if iso_match:
            frame.iso = int(iso_match.group(1))
        if shutter_match:
            frame.shutter = shutter_match.group(1).strip()
        if focal_match:
            frame.focal_length = float(focal_match.group(1))

        frames.append(frame)

    return frames
