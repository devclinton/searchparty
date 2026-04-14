"use client";

import { useCallback, useState } from "react";

interface CameraResult {
  dataUrl: string | null;
  error: string | null;
}

/**
 * Native camera hook using Capacitor Camera plugin.
 * Falls back to file input on web.
 */
export function useNativeCamera() {
  const [result, setResult] = useState<CameraResult>({
    dataUrl: null,
    error: null,
  });

  const takePhoto = useCallback(async (): Promise<string | null> => {
    try {
      const { Camera, CameraResultType, CameraSource } =
        await import("@capacitor/camera");
      await Camera.requestPermissions();

      const photo = await Camera.getPhoto({
        resultType: CameraResultType.DataUrl,
        source: CameraSource.Camera,
        quality: 80,
        width: 1280,
        allowEditing: false,
      });

      const dataUrl = photo.dataUrl ?? null;
      setResult({ dataUrl, error: null });
      return dataUrl;
    } catch {
      // Capacitor not available — return null, let UI use file input
      setResult({
        dataUrl: null,
        error: "Camera not available on this platform",
      });
      return null;
    }
  }, []);

  const pickFromGallery = useCallback(async (): Promise<string | null> => {
    try {
      const { Camera, CameraResultType, CameraSource } =
        await import("@capacitor/camera");

      const photo = await Camera.getPhoto({
        resultType: CameraResultType.DataUrl,
        source: CameraSource.Photos,
        quality: 80,
        width: 1280,
      });

      const dataUrl = photo.dataUrl ?? null;
      setResult({ dataUrl, error: null });
      return dataUrl;
    } catch {
      setResult({
        dataUrl: null,
        error: "Gallery not available on this platform",
      });
      return null;
    }
  }, []);

  return { ...result, takePhoto, pickFromGallery };
}
