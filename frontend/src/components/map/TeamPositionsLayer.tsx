"use client";

import { useEffect, useRef } from "react";
import maplibregl from "maplibre-gl";

export interface TeamPosition {
  userId: string;
  displayName: string;
  teamName: string;
  lat: number;
  lon: number;
  accuracy: number;
  timestamp: number;
  role: string;
}

interface TeamPositionsLayerProps {
  map: maplibregl.Map | null;
  positions: TeamPosition[];
}

const ROLE_COLORS: Record<string, string> = {
  incident_commander: "#dc2626",
  operations_chief: "#ea580c",
  division_supervisor: "#ca8a04",
  safety_officer: "#16a34a",
  team_leader: "#2563eb",
  searcher: "#6b7280",
};

export default function TeamPositionsLayer({
  map,
  positions,
}: TeamPositionsLayerProps) {
  const markersRef = useRef<maplibregl.Marker[]>([]);

  useEffect(() => {
    if (!map) return;

    // Clear existing markers
    markersRef.current.forEach((m) => m.remove());
    markersRef.current = [];

    // Add new markers
    positions.forEach((pos) => {
      const color = ROLE_COLORS[pos.role] ?? "#6b7280";

      const el = document.createElement("div");
      el.style.width = "12px";
      el.style.height = "12px";
      el.style.borderRadius = "50%";
      el.style.backgroundColor = color;
      el.style.border = "2px solid white";
      el.style.boxShadow = "0 1px 3px rgba(0,0,0,0.3)";

      const marker = new maplibregl.Marker({ element: el })
        .setLngLat([pos.lon, pos.lat])
        .setPopup(
          new maplibregl.Popup({ offset: 10 }).setHTML(
            `<div class="text-sm">
              <strong>${pos.displayName}</strong><br/>
              <span class="text-gray-600">${pos.teamName} - ${pos.role}</span><br/>
              <span class="text-gray-400 text-xs">
                Accuracy: ${Math.round(pos.accuracy)}m
              </span>
            </div>`,
          ),
        )
        .addTo(map);

      markersRef.current.push(marker);
    });

    return () => {
      markersRef.current.forEach((m) => m.remove());
      markersRef.current = [];
    };
  }, [map, positions]);

  return null;
}
