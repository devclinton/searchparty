"use client";

import { useEffect, useRef } from "react";
import maplibregl from "maplibre-gl";

export interface HazardZone {
  id: string;
  name: string;
  hazardType: string;
  severity: "caution" | "warning" | "danger";
  centerLat: number;
  centerLon: number;
  radiusMeters: number;
  alertBufferMeters: number;
  description?: string;
}

interface HazardZonesLayerProps {
  map: maplibregl.Map | null;
  hazards: HazardZone[];
}

const SEVERITY_COLORS: Record<string, string> = {
  caution: "#f59e0b",
  warning: "#f97316",
  danger: "#ef4444",
};

const HAZARD_ICONS: Record<string, string> = {
  cliff: "⛰️",
  mine_shaft: "⚠️",
  avalanche: "🏔️",
  flood: "🌊",
  water: "💧",
  wildlife: "🐻",
  unstable_ground: "⚠️",
  other: "⚠️",
};

function generateCircle(
  lon: number,
  lat: number,
  radiusKm: number,
  points: number = 64,
): [number, number][] {
  const coords: [number, number][] = [];
  for (let i = 0; i <= points; i++) {
    const angle = (2 * Math.PI * i) / points;
    const latOffset = (radiusKm / 111.32) * Math.cos(angle);
    const lonOffset =
      (radiusKm / (111.32 * Math.cos((lat * Math.PI) / 180))) * Math.sin(angle);
    coords.push([lon + lonOffset, lat + latOffset]);
  }
  return coords;
}

export default function HazardZonesLayer({
  map,
  hazards,
}: HazardZonesLayerProps) {
  const markersRef = useRef<maplibregl.Marker[]>([]);

  useEffect(() => {
    if (!map || hazards.length === 0) return;

    const sourceId = "hazard-zones";
    const fillLayerId = "hazard-zones-fill";
    const outlineLayerId = "hazard-zones-outline";
    const bufferSourceId = "hazard-buffers";
    const bufferLayerId = "hazard-buffers-outline";

    const zoneFeatures: GeoJSON.Feature[] = hazards.map((h) => ({
      type: "Feature",
      properties: {
        id: h.id,
        name: h.name,
        hazardType: h.hazardType,
        severity: h.severity,
        color: SEVERITY_COLORS[h.severity] ?? "#f97316",
        description: h.description ?? "",
      },
      geometry: {
        type: "Polygon",
        coordinates: [
          generateCircle(h.centerLon, h.centerLat, h.radiusMeters / 1000),
        ],
      },
    }));

    const bufferFeatures: GeoJSON.Feature[] = hazards.map((h) => ({
      type: "Feature",
      properties: { color: SEVERITY_COLORS[h.severity] ?? "#f97316" },
      geometry: {
        type: "Polygon",
        coordinates: [
          generateCircle(
            h.centerLon,
            h.centerLat,
            (h.radiusMeters + h.alertBufferMeters) / 1000,
          ),
        ],
      },
    }));

    // Hazard zone fill
    const existingSource = map.getSource(sourceId);
    if (!existingSource) {
      map.addSource(sourceId, {
        type: "geojson",
        data: { type: "FeatureCollection", features: zoneFeatures },
      });
      map.addLayer({
        id: fillLayerId,
        type: "fill",
        source: sourceId,
        paint: { "fill-color": ["get", "color"], "fill-opacity": 0.25 },
      });
      map.addLayer({
        id: outlineLayerId,
        type: "line",
        source: sourceId,
        paint: { "line-color": ["get", "color"], "line-width": 2 },
      });

      // Alert buffer dashed outline
      map.addSource(bufferSourceId, {
        type: "geojson",
        data: { type: "FeatureCollection", features: bufferFeatures },
      });
      map.addLayer({
        id: bufferLayerId,
        type: "line",
        source: bufferSourceId,
        paint: {
          "line-color": ["get", "color"],
          "line-width": 1,
          "line-dasharray": [4, 4],
          "line-opacity": 0.5,
        },
      });

      map.on("click", fillLayerId, (e) => {
        if (!e.features?.[0]?.properties) return;
        const p = e.features[0].properties;
        new maplibregl.Popup()
          .setLngLat(e.lngLat)
          .setHTML(
            `<div class="text-sm">
              <strong>${p.name}</strong><br/>
              Type: ${p.hazardType}<br/>
              Severity: <span style="color:${p.color}">${p.severity}</span><br/>
              ${p.description ? `<p class="mt-1">${p.description}</p>` : ""}
            </div>`,
          )
          .addTo(map);
      });
    }

    // Center icon markers
    markersRef.current.forEach((m) => m.remove());
    markersRef.current = [];
    hazards.forEach((h) => {
      const el = document.createElement("div");
      el.style.fontSize = "18px";
      el.textContent = HAZARD_ICONS[h.hazardType] ?? "⚠️";
      const marker = new maplibregl.Marker({ element: el })
        .setLngLat([h.centerLon, h.centerLat])
        .addTo(map);
      markersRef.current.push(marker);
    });

    return () => {
      markersRef.current.forEach((m) => m.remove());
      markersRef.current = [];
      if (map.getLayer(bufferLayerId)) map.removeLayer(bufferLayerId);
      if (map.getLayer(outlineLayerId)) map.removeLayer(outlineLayerId);
      if (map.getLayer(fillLayerId)) map.removeLayer(fillLayerId);
      if (map.getSource(bufferSourceId)) map.removeSource(bufferSourceId);
      if (map.getSource(sourceId)) map.removeSource(sourceId);
    };
  }, [map, hazards]);

  return null;
}
