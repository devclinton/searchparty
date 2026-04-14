"use client";

import { useCallback, useEffect, useRef, useState } from "react";

interface NativeGpsState {
  isTracking: boolean;
  latitude: number | null;
  longitude: number | null;
  altitude: number | null;
  accuracy: number | null;
  speed: number | null;
  heading: number | null;
  timestamp: number | null;
  error: string | null;
}

/**
 * Native GPS hook using Capacitor Geolocation plugin.
 * Falls back to browser Geolocation API on web.
 */
export function useNativeGps() {
  const [state, setState] = useState<NativeGpsState>({
    isTracking: false,
    latitude: null,
    longitude: null,
    altitude: null,
    accuracy: null,
    speed: null,
    heading: null,
    timestamp: null,
    error: null,
  });

  const watchIdRef = useRef<string | number | null>(null);

  const startTracking = useCallback(async () => {
    try {
      // Try Capacitor native plugin first
      const { Geolocation } = await import("@capacitor/geolocation");
      await Geolocation.requestPermissions();

      const id = await Geolocation.watchPosition(
        { enableHighAccuracy: true, timeout: 30000, maximumAge: 5000 },
        (position, err) => {
          if (err) {
            setState((s) => ({ ...s, error: err.message }));
            return;
          }
          if (position) {
            setState((s) => ({
              ...s,
              isTracking: true,
              latitude: position.coords.latitude,
              longitude: position.coords.longitude,
              altitude: position.coords.altitude,
              accuracy: position.coords.accuracy,
              speed: position.coords.speed,
              heading: position.coords.heading,
              timestamp: position.timestamp,
              error: null,
            }));
          }
        },
      );
      watchIdRef.current = id;
      setState((s) => ({ ...s, isTracking: true, error: null }));
    } catch {
      // Capacitor not available, fall back to browser API
      if ("geolocation" in navigator) {
        const id = navigator.geolocation.watchPosition(
          (position) => {
            setState((s) => ({
              ...s,
              isTracking: true,
              latitude: position.coords.latitude,
              longitude: position.coords.longitude,
              altitude: position.coords.altitude,
              accuracy: position.coords.accuracy,
              speed: position.coords.speed,
              heading: position.coords.heading,
              timestamp: position.timestamp,
              error: null,
            }));
          },
          (err) => setState((s) => ({ ...s, error: err.message })),
          { enableHighAccuracy: true, timeout: 30000, maximumAge: 5000 },
        );
        watchIdRef.current = id;
        setState((s) => ({ ...s, isTracking: true, error: null }));
      } else {
        setState((s) => ({ ...s, error: "Geolocation not available" }));
      }
    }
  }, []);

  const stopTracking = useCallback(async () => {
    if (watchIdRef.current !== null) {
      try {
        const { Geolocation } = await import("@capacitor/geolocation");
        await Geolocation.clearWatch({ id: watchIdRef.current as string });
      } catch {
        if (typeof watchIdRef.current === "number") {
          navigator.geolocation.clearWatch(watchIdRef.current);
        }
      }
      watchIdRef.current = null;
    }
    setState((s) => ({ ...s, isTracking: false }));
  }, []);

  useEffect(() => {
    return () => {
      if (
        watchIdRef.current !== null &&
        typeof watchIdRef.current === "number"
      ) {
        navigator.geolocation.clearWatch(watchIdRef.current);
      }
    };
  }, []);

  return { ...state, startTracking, stopTracking };
}
