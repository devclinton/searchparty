"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import {
  addPoint,
  createTrack,
  endTrack,
  type GpsPoint,
} from "@/lib/map/gps-store";

interface GpsState {
  isTracking: boolean;
  currentPosition: GeolocationPosition | null;
  trackId: string | null;
  pointCount: number;
  error: string | null;
}

interface UseGpsTrackingOptions {
  userId: string;
  incidentId: string;
  teamId?: string;
  intervalMs?: number;
}

export function useGpsTracking(options: UseGpsTrackingOptions) {
  const { userId, incidentId, teamId, intervalMs = 5000 } = options;
  const [state, setState] = useState<GpsState>({
    isTracking: false,
    currentPosition: null,
    trackId: null,
    pointCount: 0,
    error: null,
  });

  const watchIdRef = useRef<number | null>(null);
  const trackIdRef = useRef<string | null>(null);

  const startTracking = useCallback(async () => {
    if (!("geolocation" in navigator)) {
      setState((s) => ({ ...s, error: "Geolocation not available" }));
      return;
    }

    const newTrackId = `${userId}-${Date.now()}`;
    trackIdRef.current = newTrackId;

    await createTrack({
      id: newTrackId,
      userId,
      incidentId,
      teamId: teamId ?? null,
      startedAt: Date.now(),
      endedAt: null,
      synced: false,
      pointCount: 0,
    });

    setState((s) => ({
      ...s,
      isTracking: true,
      trackId: newTrackId,
      pointCount: 0,
      error: null,
    }));

    watchIdRef.current = navigator.geolocation.watchPosition(
      async (position) => {
        setState((s) => ({ ...s, currentPosition: position }));

        if (trackIdRef.current) {
          const point: GpsPoint = {
            lat: position.coords.latitude,
            lon: position.coords.longitude,
            altitude: position.coords.altitude,
            accuracy: position.coords.accuracy,
            timestamp: position.timestamp,
            trackId: trackIdRef.current,
          };
          await addPoint(point);
          setState((s) => ({ ...s, pointCount: s.pointCount + 1 }));
        }
      },
      (err) => {
        setState((s) => ({ ...s, error: err.message }));
      },
      {
        enableHighAccuracy: true,
        maximumAge: intervalMs,
        timeout: 30000,
      },
    );
  }, [userId, incidentId, teamId, intervalMs]);

  const stopTracking = useCallback(async () => {
    if (watchIdRef.current !== null) {
      navigator.geolocation.clearWatch(watchIdRef.current);
      watchIdRef.current = null;
    }
    if (trackIdRef.current) {
      await endTrack(trackIdRef.current);
      trackIdRef.current = null;
    }
    setState((s) => ({ ...s, isTracking: false }));
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (watchIdRef.current !== null) {
        navigator.geolocation.clearWatch(watchIdRef.current);
      }
    };
  }, []);

  return {
    ...state,
    startTracking,
    stopTracking,
  };
}
