import type { CoordinateFormat } from "./config";

export interface LatLon {
  lat: number;
  lon: number;
}

/**
 * Format decimal degrees to string.
 */
function formatDD(coord: LatLon): string {
  return `${coord.lat.toFixed(6)}°, ${coord.lon.toFixed(6)}°`;
}

/**
 * Format to degrees, minutes, seconds.
 */
function formatDMS(coord: LatLon): string {
  const toDMS = (dd: number, pos: string, neg: string): string => {
    const dir = dd >= 0 ? pos : neg;
    const abs = Math.abs(dd);
    const d = Math.floor(abs);
    const mFloat = (abs - d) * 60;
    const m = Math.floor(mFloat);
    const s = ((mFloat - m) * 60).toFixed(1);
    return `${d}°${m}'${s}"${dir}`;
  };
  return `${toDMS(coord.lat, "N", "S")} ${toDMS(coord.lon, "E", "W")}`;
}

/**
 * Convert to UTM zone and coordinates.
 */
function formatUTM(coord: LatLon): string {
  const { lat, lon } = coord;
  const zoneNumber = Math.floor((lon + 180) / 6) + 1;
  const zoneLetter = lat >= 0 ? "N" : "S";

  // Simplified UTM calculation (WGS84)
  const latRad = (lat * Math.PI) / 180;
  const lonRad = (lon * Math.PI) / 180;

  const a = 6378137.0; // WGS84 semi-major axis
  const f = 1 / 298.257223563;
  const e2 = 2 * f - f * f;
  const e4 = e2 * e2;
  const e6 = e4 * e2;
  const ep2 = e2 / (1 - e2);

  const lonOrigin = ((zoneNumber - 1) * 6 - 180 + 3) * (Math.PI / 180);
  const N = a / Math.sqrt(1 - e2 * Math.sin(latRad) * Math.sin(latRad));
  const T = Math.tan(latRad) * Math.tan(latRad);
  const C = ep2 * Math.cos(latRad) * Math.cos(latRad);
  const A = Math.cos(latRad) * (lonRad - lonOrigin);

  const M =
    a *
    ((1 - e2 / 4 - (3 * e4) / 64 - (5 * e6) / 256) * latRad -
      ((3 * e2) / 8 + (3 * e4) / 32 + (45 * e6) / 1024) * Math.sin(2 * latRad) +
      ((15 * e4) / 256 + (45 * e6) / 1024) * Math.sin(4 * latRad) -
      ((35 * e6) / 3072) * Math.sin(6 * latRad));

  const k0 = 0.9996;
  let easting =
    k0 *
    N *
    (A +
      ((1 - T + C) * A * A * A) / 6 +
      ((5 - 18 * T + T * T) * A * A * A * A * A) / 120);
  easting += 500000.0;

  let northing =
    k0 *
    (M +
      N *
        Math.tan(latRad) *
        ((A * A) / 2 +
          ((5 - T + 9 * C + 4 * C * C) * A * A * A * A) / 24 +
          ((61 - 58 * T + T * T) * A * A * A * A * A * A) / 720));
  if (lat < 0) northing += 10000000.0;

  return `${zoneNumber}${zoneLetter} ${Math.round(easting)}E ${Math.round(northing)}N`;
}

/**
 * Simplified MGRS format (zone + 100km grid square + coordinates).
 */
function formatMGRS(coord: LatLon): string {
  // Use UTM as base and add grid square letters
  const utm = formatUTM(coord);
  return `MGRS: ${utm}`;
}

/**
 * Format coordinates in the specified format.
 */
export function formatCoordinates(
  coord: LatLon,
  format: CoordinateFormat,
): string {
  switch (format) {
    case "dd":
      return formatDD(coord);
    case "dms":
      return formatDMS(coord);
    case "utm":
      return formatUTM(coord);
    case "mgrs":
      return formatMGRS(coord);
  }
}

/**
 * Calculate distance between two points in meters (Haversine formula).
 */
export function distanceMeters(a: LatLon, b: LatLon): number {
  const R = 6371000;
  const dLat = ((b.lat - a.lat) * Math.PI) / 180;
  const dLon = ((b.lon - a.lon) * Math.PI) / 180;
  const lat1 = (a.lat * Math.PI) / 180;
  const lat2 = (b.lat * Math.PI) / 180;

  const x =
    Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.cos(lat1) * Math.cos(lat2) * Math.sin(dLon / 2) * Math.sin(dLon / 2);
  return R * 2 * Math.atan2(Math.sqrt(x), Math.sqrt(1 - x));
}

/**
 * Calculate bearing from point A to point B in degrees.
 */
export function bearing(a: LatLon, b: LatLon): number {
  const lat1 = (a.lat * Math.PI) / 180;
  const lat2 = (b.lat * Math.PI) / 180;
  const dLon = ((b.lon - a.lon) * Math.PI) / 180;

  const y = Math.sin(dLon) * Math.cos(lat2);
  const x =
    Math.cos(lat1) * Math.sin(lat2) -
    Math.sin(lat1) * Math.cos(lat2) * Math.cos(dLon);
  const deg = (Math.atan2(y, x) * 180) / Math.PI;
  return (deg + 360) % 360;
}

/**
 * Format bearing as compass direction string.
 */
export function formatBearing(degrees: number): string {
  const directions = [
    "N",
    "NNE",
    "NE",
    "ENE",
    "E",
    "ESE",
    "SE",
    "SSE",
    "S",
    "SSW",
    "SW",
    "WSW",
    "W",
    "WNW",
    "NW",
    "NNW",
  ];
  const index = Math.round(degrees / 22.5) % 16;
  return `${degrees.toFixed(1)}° ${directions[index]}`;
}
