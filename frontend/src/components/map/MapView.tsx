"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import maplibregl from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import {
  DEFAULT_CENTER,
  DEFAULT_ZOOM,
  MAP_STYLES,
  type MapStyleKey,
} from "@/lib/map/config";
import { formatCoordinates, type LatLon } from "@/lib/map/coordinates";
import type { CoordinateFormat } from "@/lib/map/config";

interface MapViewProps {
  center?: [number, number];
  zoom?: number;
  style?: MapStyleKey;
  coordinateFormat?: CoordinateFormat;
  onMapClick?: (latlng: LatLon) => void;
  onMapReady?: (map: maplibregl.Map) => void;
  className?: string;
}

export default function MapView({
  center = DEFAULT_CENTER,
  zoom = DEFAULT_ZOOM,
  style = "osm",
  coordinateFormat = "dd",
  onMapClick,
  onMapReady,
  className = "",
}: MapViewProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<maplibregl.Map | null>(null);
  const [cursorCoords, setCursorCoords] = useState<LatLon | null>(null);
  const [currentStyle, setCurrentStyle] = useState<MapStyleKey>(style);

  useEffect(() => {
    if (!containerRef.current || mapRef.current) return;

    const map = new maplibregl.Map({
      container: containerRef.current,
      style: MAP_STYLES[currentStyle],
      center,
      zoom,
    });

    map.addControl(new maplibregl.NavigationControl(), "top-right");
    map.addControl(
      new maplibregl.GeolocateControl({
        positionOptions: { enableHighAccuracy: true },
        trackUserLocation: true,
      }),
      "top-right",
    );
    map.addControl(
      new maplibregl.ScaleControl({ unit: "metric" }),
      "bottom-left",
    );

    map.on("mousemove", (e) => {
      setCursorCoords({ lat: e.lngLat.lat, lon: e.lngLat.lng });
    });

    if (onMapClick) {
      map.on("click", (e) => {
        onMapClick({ lat: e.lngLat.lat, lon: e.lngLat.lng });
      });
    }

    mapRef.current = map;
    onMapReady?.(map);

    return () => {
      map.remove();
      mapRef.current = null;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const switchStyle = useCallback((newStyle: MapStyleKey) => {
    if (mapRef.current) {
      mapRef.current.setStyle(MAP_STYLES[newStyle]);
      setCurrentStyle(newStyle);
    }
  }, []);

  return (
    <div className={`relative w-full h-full ${className}`}>
      <div ref={containerRef} className="w-full h-full" />

      {/* Style switcher */}
      <div className="absolute top-2 left-2 z-10 flex gap-1">
        <button
          onClick={() => switchStyle("osm")}
          className={`px-2 py-1 text-xs rounded ${
            currentStyle === "osm"
              ? "bg-black text-white dark:bg-white dark:text-black"
              : "bg-white text-black dark:bg-zinc-800 dark:text-white"
          } shadow`}
        >
          Map
        </button>
        <button
          onClick={() => switchStyle("topo")}
          className={`px-2 py-1 text-xs rounded ${
            currentStyle === "topo"
              ? "bg-black text-white dark:bg-white dark:text-black"
              : "bg-white text-black dark:bg-zinc-800 dark:text-white"
          } shadow`}
        >
          Topo
        </button>
      </div>

      {/* Coordinate display */}
      {cursorCoords && (
        <div className="absolute bottom-8 right-2 z-10 bg-white/90 dark:bg-zinc-900/90 px-2 py-1 rounded text-xs font-mono shadow">
          {formatCoordinates(cursorCoords, coordinateFormat)}
        </div>
      )}
    </div>
  );
}
