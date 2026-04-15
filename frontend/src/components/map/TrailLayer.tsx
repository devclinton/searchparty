"use client";

import { useEffect } from "react";
import maplibregl from "maplibre-gl";

interface TrailLayerProps {
  map: maplibregl.Map | null;
  geojson: GeoJSON.FeatureCollection | null;
  visible?: boolean;
}

const TRAIL_TYPE_COLORS: Record<string, string> = {
  path: "#8b5cf6",
  footway: "#6366f1",
  track: "#a16207",
  bridleway: "#059669",
  cycleway: "#0891b2",
  road: "#6b7280",
  custom: "#ec4899",
};

const TRAIL_TYPE_DASH: Record<string, number[]> = {
  path: [6, 3],
  footway: [6, 3],
  track: [10, 2],
  bridleway: [4, 4],
  cycleway: [8, 4],
  road: [],
  custom: [2, 4],
};

export default function TrailLayer({
  map,
  geojson,
  visible = true,
}: TrailLayerProps) {
  useEffect(() => {
    if (!map || !geojson) return;

    const sourceId = "trails";
    const layerId = "trails-line";
    const labelLayerId = "trails-labels";

    const existingSource = map.getSource(sourceId) as
      | maplibregl.GeoJSONSource
      | undefined;
    if (existingSource) {
      existingSource.setData(geojson);
    } else {
      map.addSource(sourceId, { type: "geojson", data: geojson });

      map.addLayer({
        id: layerId,
        type: "line",
        source: sourceId,
        paint: {
          "line-color": [
            "match",
            ["get", "trail_type"],
            "path",
            "#8b5cf6",
            "footway",
            "#6366f1",
            "track",
            "#a16207",
            "bridleway",
            "#059669",
            "cycleway",
            "#0891b2",
            "road",
            "#6b7280",
            "custom",
            "#ec4899",
            "#8b5cf6",
          ] as unknown as maplibregl.ExpressionSpecification,
          "line-width": 2.5,
          "line-opacity": 0.8,
        },
        layout: {
          visibility: visible ? "visible" : "none",
        },
      });

      map.addLayer({
        id: labelLayerId,
        type: "symbol",
        source: sourceId,
        layout: {
          "symbol-placement": "line",
          "text-field": ["get", "name"],
          "text-size": 11,
          "text-offset": [0, -0.8],
          visibility: visible ? "visible" : "none",
        },
        paint: {
          "text-color": "#374151",
          "text-halo-color": "#ffffff",
          "text-halo-width": 1.5,
        },
      });

      map.on("click", layerId, (e) => {
        if (!e.features?.[0]?.properties) return;
        const p = e.features[0].properties;
        const length = p.length_meters
          ? `${(Number(p.length_meters) / 1000).toFixed(1)} km`
          : "Unknown";
        new maplibregl.Popup()
          .setLngLat(e.lngLat)
          .setHTML(
            `<div class="text-sm">
              <strong>${p.name || "Unnamed trail"}</strong><br/>
              Type: ${p.trail_type}<br/>
              Length: ${length}<br/>
              ${p.surface ? `Surface: ${p.surface}<br/>` : ""}
              ${p.difficulty ? `Difficulty: ${p.difficulty}<br/>` : ""}
              Source: ${p.source}
            </div>`,
          )
          .addTo(map);
      });
    }

    // Toggle visibility
    if (map.getLayer(layerId)) {
      map.setLayoutProperty(
        layerId,
        "visibility",
        visible ? "visible" : "none",
      );
    }
    if (map.getLayer(labelLayerId)) {
      map.setLayoutProperty(
        labelLayerId,
        "visibility",
        visible ? "visible" : "none",
      );
    }

    return () => {
      if (map.getLayer(labelLayerId)) map.removeLayer(labelLayerId);
      if (map.getLayer(layerId)) map.removeLayer(layerId);
      if (map.getSource(sourceId)) map.removeSource(sourceId);
    };
  }, [map, geojson, visible]);

  return null;
}
