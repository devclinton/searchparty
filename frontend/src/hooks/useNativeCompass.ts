"use client";

import { useCallback, useEffect, useRef, useState } from "react";

interface CompassState {
  heading: number | null;
  accuracy: number | null;
  isActive: boolean;
  error: string | null;
}

/**
 * Native compass hook using Capacitor Motion plugin (device orientation).
 * Falls back to DeviceOrientationEvent on web.
 */
export function useNativeCompass() {
  const [state, setState] = useState<CompassState>({
    heading: null,
    accuracy: null,
    isActive: false,
    error: null,
  });

  const listenerRef = useRef<(() => void) | null>(null);

  const start = useCallback(async () => {
    try {
      const { Motion } = await import("@capacitor/motion");
      const listener = await Motion.addListener("orientation", (event) => {
        setState({
          heading: event.alpha ?? null,
          accuracy: null,
          isActive: true,
          error: null,
        });
      });
      listenerRef.current = () => listener.remove();
      setState((s) => ({ ...s, isActive: true, error: null }));
    } catch {
      // Fallback to browser DeviceOrientationEvent
      if ("DeviceOrientationEvent" in window) {
        const handler = (event: DeviceOrientationEvent) => {
          // webkitCompassHeading is Safari-specific
          const heading =
            (
              event as DeviceOrientationEvent & {
                webkitCompassHeading?: number;
              }
            ).webkitCompassHeading ?? event.alpha;
          setState({
            heading: heading ?? null,
            accuracy: null,
            isActive: true,
            error: null,
          });
        };
        window.addEventListener("deviceorientation", handler);
        listenerRef.current = () =>
          window.removeEventListener("deviceorientation", handler);
        setState((s) => ({ ...s, isActive: true, error: null }));
      } else {
        setState((s) => ({ ...s, error: "Compass not available" }));
      }
    }
  }, []);

  const stop = useCallback(() => {
    listenerRef.current?.();
    listenerRef.current = null;
    setState((s) => ({ ...s, isActive: false }));
  }, []);

  useEffect(() => {
    return () => listenerRef.current?.();
  }, []);

  return { ...state, start, stop };
}
