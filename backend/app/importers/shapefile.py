"""ESRI Shapefile parser for agency trail data (USFS, BLM, NPS).

Uses a pure-Python approach to parse the basic shapefile format
without external GIS libraries. Supports .shp/.dbf/.shx in a zip archive.
"""

import io
import struct
import zipfile


class ShapefileTrail:
    def __init__(
        self,
        name: str | None,
        trail_type: str,
        coordinates: list[list[float]],
        attributes: dict,
    ):
        self.name = name
        self.trail_type = trail_type
        self.coordinates = coordinates  # [[lon, lat], ...]
        self.attributes = attributes


def _read_dbf_records(data: bytes) -> list[dict]:
    """Parse a DBF file and return records as dicts."""
    num_records = struct.unpack_from("<I", data, 4)[0]
    header_size = struct.unpack_from("<H", data, 8)[0]
    record_size = struct.unpack_from("<H", data, 10)[0]

    # Read field descriptors
    fields = []
    offset = 32
    while offset < header_size - 1:
        if data[offset] == 0x0D:
            break
        name = data[offset : offset + 11].split(b"\x00")[0].decode("ascii", errors="ignore")
        field_type = chr(data[offset + 11])
        field_size = data[offset + 16]
        fields.append((name, field_type, field_size))
        offset += 32

    # Read records
    records = []
    data_offset = header_size
    for _ in range(num_records):
        record = {}
        pos = data_offset + 1  # Skip deletion flag
        for name, _field_type, field_size in fields:
            raw = data[pos : pos + field_size].decode("ascii", errors="ignore").strip()
            record[name] = raw
            pos += field_size
        records.append(record)
        data_offset += record_size

    return records


def _read_shp_polylines(data: bytes) -> list[list[list[float]]]:
    """Parse polyline geometries from a .shp file."""
    geometries = []
    offset = 100  # Skip file header

    while offset < len(data) - 8:
        # Record header
        try:
            content_length = struct.unpack_from(">I", data, offset + 4)[0] * 2
        except struct.error:
            break

        record_start = offset + 8
        shape_type = struct.unpack_from("<I", data, record_start)[0]

        if shape_type == 3:  # PolyLine
            num_parts = struct.unpack_from("<I", data, record_start + 36)[0]
            num_points = struct.unpack_from("<I", data, record_start + 40)[0]

            parts_offset = record_start + 44
            points_offset = parts_offset + num_parts * 4

            parts = []
            for i in range(num_parts):
                parts.append(struct.unpack_from("<I", data, parts_offset + i * 4)[0])

            coords = []
            for i in range(num_points):
                x = struct.unpack_from("<d", data, points_offset + i * 16)[0]
                y = struct.unpack_from("<d", data, points_offset + i * 16 + 8)[0]
                coords.append([x, y])  # [lon, lat]

            # Split by parts
            for i, start in enumerate(parts):
                end = parts[i + 1] if i + 1 < len(parts) else num_points
                geometries.append(coords[start:end])
        else:
            geometries.append([])

        offset += 8 + content_length

    return geometries


def parse_shapefile_zip(content: bytes, source: str = "shapefile") -> list[ShapefileTrail]:
    """Parse a zip archive containing .shp, .dbf, and optionally .shx files."""
    trails = []

    with zipfile.ZipFile(io.BytesIO(content)) as zf:
        shp_name = None
        dbf_name = None

        for name in zf.namelist():
            lower = name.lower()
            if lower.endswith(".shp"):
                shp_name = name
            elif lower.endswith(".dbf"):
                dbf_name = name

        if shp_name is None:
            return trails

        shp_data = zf.read(shp_name)
        geometries = _read_shp_polylines(shp_data)

        records: list[dict] = []
        if dbf_name:
            dbf_data = zf.read(dbf_name)
            records = _read_dbf_records(dbf_data)

        for i, coords in enumerate(geometries):
            if len(coords) < 2:
                continue

            attrs = records[i] if i < len(records) else {}
            name = (
                attrs.get("TRAIL_NAME")
                or attrs.get("TRAIL_NM")
                or attrs.get("NAME")
                or attrs.get("TRAILNAME")
            )

            trails.append(
                ShapefileTrail(
                    name=name,
                    trail_type="track",
                    coordinates=coords,
                    attributes=attrs,
                )
            )

    return trails
