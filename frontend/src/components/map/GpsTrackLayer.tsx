"use client";

import { useEffect } from "react";
import maplibregl from "maplibre-gl";
import type { GpsPoint } from "@/lib/map/gps-store";

interface GpsTrackLayerProps {
  map: maplibregl.Map | null;
  points: GpsPoint[];
  trackId: string;
  color?: string;
}

export default function GpsTrackLayer({
  map,
  points,
  trackId,
  color = "#2563eb",
}: GpsTrackLayerProps) {
  useEffect(() => {
    if (!map || points.length < 2) return;

    const sourceId = `track-${trackId}`;
    const layerId = `track-line-${trackId}`;

    const coordinates = points.map((p) => [p.lon, p.lat]);

    const geojson: GeoJSON.FeatureCollection = {
      type: "FeatureCollection",
      features: [
        {
          type: "Feature",
          geometry: {
            type: "LineString",
            coordinates,
          },
          properties: {},
        },
      ],
    };

    // Add or update source
    const existingSource = map.getSource(sourceId) as
      | maplibregl.GeoJSONSource
      | undefined;
    if (existingSource) {
      existingSource.setData(geojson);
    } else {
      map.addSource(sourceId, {
        type: "geojson",
        data: geojson,
      });

      map.addLayer({
        id: layerId,
        type: "line",
        source: sourceId,
        paint: {
          "line-color": color,
          "line-width": 3,
          "line-opacity": 0.8,
        },
      });
    }

    return () => {
      if (map.getLayer(layerId)) map.removeLayer(layerId);
      if (map.getSource(sourceId)) map.removeSource(sourceId);
    };
  }, [map, points, trackId, color]);

  return null;
}
