"use client";

import { useEffect, useRef } from "react";
import maplibregl from "maplibre-gl";
import type { MeshNode, MeshPosition } from "@/lib/mesh/types";

interface MeshPositionsLayerProps {
  map: maplibregl.Map | null;
  positions: Map<string, MeshPosition>;
  nodes: Map<string, MeshNode>;
}

export default function MeshPositionsLayer({
  map,
  positions,
  nodes,
}: MeshPositionsLayerProps) {
  const markersRef = useRef<maplibregl.Marker[]>([]);

  useEffect(() => {
    if (!map) return;

    markersRef.current.forEach((m) => m.remove());
    markersRef.current = [];

    positions.forEach((pos, nodeId) => {
      const node = nodes.get(nodeId);
      const name = node?.longName || node?.shortName || nodeId;
      const battery = node?.batteryLevel ?? 0;
      const snr = pos.timestamp ? `SNR: ${node?.snr?.toFixed(1) ?? "?"}` : "";

      const el = document.createElement("div");
      el.style.width = "14px";
      el.style.height = "14px";
      el.style.borderRadius = "3px";
      el.style.backgroundColor = "#8b5cf6";
      el.style.border = "2px solid white";
      el.style.boxShadow = "0 1px 3px rgba(0,0,0,0.3)";
      el.style.transform = "rotate(45deg)"; // Diamond shape

      const age = Math.round((Date.now() / 1000 - pos.timestamp) / 60);
      const ageStr = age < 60 ? `${age}m ago` : `${Math.round(age / 60)}h ago`;

      const marker = new maplibregl.Marker({ element: el })
        .setLngLat([pos.longitude, pos.latitude])
        .setPopup(
          new maplibregl.Popup({ offset: 10 }).setHTML(
            `<div class="text-sm">
              <strong>${name}</strong> (mesh)<br/>
              Battery: ${battery}%<br/>
              ${snr}<br/>
              Alt: ${pos.altitude ?? "?"} m<br/>
              Sats: ${pos.satsInView}<br/>
              <span class="text-gray-400 text-xs">${ageStr}</span>
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
  }, [map, positions, nodes]);

  return null;
}
