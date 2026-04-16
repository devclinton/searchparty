"""Flight plan exporters for drone mission formats.

Converts waypoint lists to DJI WPML, MAVLink, KML, and Litchi CSV.
"""

import json
import math
import xml.etree.ElementTree as ET
from xml.dom.minidom import parseString

from app.drone.patterns import Waypoint


def export_wpml(
    waypoints: list[Waypoint],
    mission_name: str = "SearchParty Mission",
    drone_model: str = "67",  # DJI M3E enum
    obstacle_avoidance: str = "stop",
) -> str:
    """Export to DJI Waypoint Mission Language (WPML) XML.

    Compatible with DJI Pilot 2 and DJI FlightHub 2.
    """
    root = ET.Element(
        "kml",
        xmlns="http://www.opengis.net/kml/2.2",
        **{"xmlns:wpml": "http://www.dji.com/wpmz/1.0.0"},
    )
    doc = ET.SubElement(root, "Document")

    # Mission config
    mission = ET.SubElement(doc, "wpml:missionConfig")
    ET.SubElement(mission, "wpml:flyToWaylineMode").text = "safely"
    ET.SubElement(mission, "wpml:finishAction").text = "goHome"
    ET.SubElement(mission, "wpml:exitOnRCLost").text = "executeLostAction"
    ET.SubElement(mission, "wpml:executeRCLostAction").text = "goBack"
    ET.SubElement(mission, "wpml:droneInfo").text = drone_model

    # Wayline (template)
    folder = ET.SubElement(doc, "Folder")
    ET.SubElement(folder, "wpml:templateId").text = "0"
    speed = waypoints[0].speed_ms if waypoints else 5.0
    ET.SubElement(folder, "wpml:autoFlightSpeed").text = str(speed)

    placemark = ET.SubElement(folder, "Placemark")
    ET.SubElement(placemark, "name").text = mission_name

    for i, wp in enumerate(waypoints):
        point = ET.SubElement(placemark, "wpml:point")
        ET.SubElement(point, "wpml:index").text = str(i)
        ET.SubElement(point, "wpml:latitude").text = f"{wp.lat:.8f}"
        ET.SubElement(point, "wpml:longitude").text = f"{wp.lon:.8f}"
        ET.SubElement(point, "wpml:height").text = f"{wp.altitude_m:.1f}"
        ET.SubElement(point, "wpml:speed").text = f"{wp.speed_ms:.1f}"

        if wp.gimbal_pitch != -90.0:
            action = ET.SubElement(point, "wpml:waypointGimbalPitchAngle")
            action.text = f"{wp.gimbal_pitch:.1f}"

    xml_str = ET.tostring(root, encoding="unicode", xml_declaration=True)
    return parseString(xml_str).toprettyxml(indent="  ")  # noqa: S318


def export_mavlink(waypoints: list[Waypoint]) -> str:
    """Export as MAVLink mission items in QGroundControl JSON plan format.

    Compatible with ArduPilot, PX4, QGroundControl, and Mission Planner.
    """
    items = []
    # Takeoff
    items.append(
        {
            "autoContinue": True,
            "command": 22,  # MAV_CMD_NAV_TAKEOFF
            "coordinate": [
                waypoints[0].lat if waypoints else 0,
                waypoints[0].lon if waypoints else 0,
                waypoints[0].altitude_m if waypoints else 50,
            ],
            "frame": 3,  # MAV_FRAME_GLOBAL_RELATIVE_ALT
            "type": "SimpleItem",
            "params": [0, 0, 0, 0],
        }
    )

    for wp in waypoints:
        items.append(
            {
                "autoContinue": True,
                "command": 16,  # MAV_CMD_NAV_WAYPOINT
                "coordinate": [wp.lat, wp.lon, wp.altitude_m],
                "frame": 3,
                "type": "SimpleItem",
                "params": [0, 0, 0, 0],
            }
        )

    # Return to launch
    items.append(
        {
            "autoContinue": True,
            "command": 20,  # MAV_CMD_NAV_RETURN_TO_LAUNCH
            "coordinate": [0, 0, 0],
            "frame": 3,
            "type": "SimpleItem",
            "params": [0, 0, 0, 0],
        }
    )

    plan = {
        "fileType": "Plan",
        "version": 1,
        "groundStation": "SearchParty",
        "mission": {
            "cruiseSpeed": waypoints[0].speed_ms if waypoints else 5.0,
            "hoverSpeed": waypoints[0].speed_ms if waypoints else 5.0,
            "items": items,
            "plannedHomePosition": {
                "coordinate": [
                    waypoints[0].lat if waypoints else 0,
                    waypoints[0].lon if waypoints else 0,
                    0,
                ],
            },
        },
    }
    return json.dumps(plan, indent=2)


def export_kml(
    waypoints: list[Waypoint],
    mission_name: str = "SearchParty Mission",
) -> str:
    """Export as KML for universal compatibility."""
    coords = " ".join(f"{wp.lon:.8f},{wp.lat:.8f},{wp.altitude_m:.1f}" for wp in waypoints)

    kml = f"""<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
  <Document>
    <name>{mission_name}</name>
    <Style id="flightPath">
      <LineStyle>
        <color>ff0000ff</color>
        <width>3</width>
      </LineStyle>
    </Style>
    <Placemark>
      <name>Flight Path</name>
      <styleUrl>#flightPath</styleUrl>
      <LineString>
        <altitudeMode>relativeToGround</altitudeMode>
        <coordinates>{coords}</coordinates>
      </LineString>
    </Placemark>"""

    for i, wp in enumerate(waypoints):
        kml += f"""
    <Placemark>
      <name>WP{i}</name>
      <Point>
        <altitudeMode>relativeToGround</altitudeMode>
        <coordinates>{wp.lon:.8f},{wp.lat:.8f},{wp.altitude_m:.1f}</coordinates>
      </Point>
    </Placemark>"""

    kml += """
  </Document>
</kml>"""
    return kml


def export_litchi_csv(waypoints: list[Waypoint]) -> str:
    """Export as Litchi CSV for DJI consumer drones.

    Columns: latitude, longitude, altitude(m), heading(deg), curvesize(m),
    rotationdir, gimbalmode, gimbalpitchangle, actiontype1, ...
    """
    lines = [
        "latitude,longitude,altitude(m),heading(deg),curvesize(m),"
        "rotationdir,gimbalmode,gimbalpitchangle,actiontype1,"
        "actionparam1,actiontype2,actionparam2,altitudemode,speed(m/s),"
        "poi_latitude,poi_longitude,poi_altitude(m),poi_altitudemode,"
        "photo_timeinterval,photo_distinterval"
    ]

    for i, wp in enumerate(waypoints):
        heading = 0
        if i > 0:
            prev = waypoints[i - 1]
            dlat = wp.lat - prev.lat
            dlon = wp.lon - prev.lon
            heading = math.degrees(math.atan2(dlon, dlat)) % 360

        action = "-1" if wp.action == "fly" else "1"  # 1 = take photo
        lines.append(
            f"{wp.lat:.8f},{wp.lon:.8f},{wp.altitude_m:.1f},{heading:.1f},0.0,"
            f"0,2,{wp.gimbal_pitch:.1f},{action},"
            f"0,-1,0,1,{wp.speed_ms:.1f},"
            f"0,0,0,0,-1,-1"
        )

    return "\n".join(lines)
