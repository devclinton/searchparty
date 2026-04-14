"use client";

import { useEffect, useRef } from "react";
import maplibregl from "maplibre-gl";

export interface ClueMarker {
  id: string;
  lat: number;
  lon: number;
  description: string;
  clueType: string;
  foundAt: string;
}

interface ClueMarkersLayerProps {
  map: maplibregl.Map | null;
  clues: ClueMarker[];
}

const CLUE_TYPE_EMOJI: Record<string, string> = {
  physical: "📦",
  track: "👣",
  scent: "🐕",
  witness: "👁",
  other: "📌",
};

export default function ClueMarkersLayer({
  map,
  clues,
}: ClueMarkersLayerProps) {
  const markersRef = useRef<maplibregl.Marker[]>([]);

  useEffect(() => {
    if (!map) return;

    markersRef.current.forEach((m) => m.remove());
    markersRef.current = [];

    clues.forEach((clue) => {
      const emoji = CLUE_TYPE_EMOJI[clue.clueType] ?? "📌";

      const el = document.createElement("div");
      el.style.fontSize = "20px";
      el.style.cursor = "pointer";
      el.textContent = emoji;

      const marker = new maplibregl.Marker({ element: el })
        .setLngLat([clue.lon, clue.lat])
        .setPopup(
          new maplibregl.Popup({ offset: 10 }).setHTML(
            `<div class="text-sm">
              <strong>${clue.clueType}</strong><br/>
              ${clue.description}<br/>
              <span class="text-gray-400 text-xs">${clue.foundAt}</span>
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
  }, [map, clues]);

  return null;
}
