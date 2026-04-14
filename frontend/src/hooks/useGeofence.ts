"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { distanceMeters, type LatLon } from "@/lib/map/coordinates";

export interface HazardProximity {
  id: string;
  name: string;
  hazardType: string;
  severity: string;
  distanceMeters: number;
}

interface GeofenceConfig {
  hazards: {
    id: string;
    name: string;
    hazardType: string;
    severity: string;
    centerLat: number;
    centerLon: number;
    radiusMeters: number;
    alertBufferMeters: number;
  }[];
  currentPosition: LatLon | null;
  onAlert?: (hazards: HazardProximity[]) => void;
}

/**
 * Client-side geofence check — works offline by comparing GPS position
 * against locally cached hazard zone data.
 */
export function useGeofence({
  hazards,
  currentPosition,
  onAlert,
}: GeofenceConfig) {
  const [nearbyHazards, setNearbyHazards] = useState<HazardProximity[]>([]);
  const lastAlertRef = useRef<string>("");

  const checkGeofence = useCallback(() => {
    if (!currentPosition || hazards.length === 0) {
      setNearbyHazards([]);
      return;
    }

    const nearby: HazardProximity[] = [];

    for (const h of hazards) {
      const dist = distanceMeters(currentPosition, {
        lat: h.centerLat,
        lon: h.centerLon,
      });
      const alertDistance = h.radiusMeters + h.alertBufferMeters;

      if (dist <= alertDistance) {
        nearby.push({
          id: h.id,
          name: h.name,
          hazardType: h.hazardType,
          severity: h.severity,
          distanceMeters: Math.max(0, dist - h.radiusMeters),
        });
      }
    }

    setNearbyHazards(nearby);

    // Only fire alert callback when the set of nearby hazards changes
    const key = nearby
      .map((n) => n.id)
      .sort()
      .join(",");
    if (key !== lastAlertRef.current && nearby.length > 0) {
      lastAlertRef.current = key;
      onAlert?.(nearby);
    }
  }, [hazards, currentPosition, onAlert]);

  useEffect(() => {
    checkGeofence();
  }, [checkGeofence]);

  return { nearbyHazards };
}
