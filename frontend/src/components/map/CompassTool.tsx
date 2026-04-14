"use client";

import {
  bearing,
  distanceMeters,
  formatBearing,
  type LatLon,
} from "@/lib/map/coordinates";

interface CompassToolProps {
  pointA: LatLon | null;
  pointB: LatLon | null;
  onClear?: () => void;
}

export default function CompassTool({
  pointA,
  pointB,
  onClear,
}: CompassToolProps) {
  if (!pointA) {
    return (
      <div className="bg-white/90 dark:bg-zinc-900/90 p-3 rounded shadow text-sm">
        <p className="text-zinc-500">Click on the map to set the first point</p>
      </div>
    );
  }

  if (!pointB) {
    return (
      <div className="bg-white/90 dark:bg-zinc-900/90 p-3 rounded shadow text-sm">
        <p>
          Point A: {pointA.lat.toFixed(6)}, {pointA.lon.toFixed(6)}
        </p>
        <p className="text-zinc-500">
          Click on the map to set the second point
        </p>
      </div>
    );
  }

  const dist = distanceMeters(pointA, pointB);
  const bear = bearing(pointA, pointB);

  const formatDistance = (m: number): string => {
    if (m < 1000) return `${Math.round(m)} m`;
    return `${(m / 1000).toFixed(2)} km`;
  };

  return (
    <div className="bg-white/90 dark:bg-zinc-900/90 p-3 rounded shadow text-sm space-y-1">
      <p>
        <span className="font-medium">Distance:</span> {formatDistance(dist)}
      </p>
      <p>
        <span className="font-medium">Bearing:</span> {formatBearing(bear)}
      </p>
      <p className="text-zinc-500 text-xs">
        A: {pointA.lat.toFixed(6)}, {pointA.lon.toFixed(6)}
      </p>
      <p className="text-zinc-500 text-xs">
        B: {pointB.lat.toFixed(6)}, {pointB.lon.toFixed(6)}
      </p>
      {onClear && (
        <button
          onClick={onClear}
          className="text-xs text-blue-600 dark:text-blue-400 hover:underline"
        >
          Clear measurement
        </button>
      )}
    </div>
  );
}
