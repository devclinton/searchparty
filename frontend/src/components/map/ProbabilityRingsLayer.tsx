"use client";

import { useEffect } from "react";
import maplibregl from "maplibre-gl";

interface RingFeature {
  type: "Feature";
  properties: {
    percentile?: number;
    percentile_label?: string;
    radius_km?: number;
    color?: string;
    profile?: string;
    type?: string;
    label?: string;
  };
  geometry: {
    type: string;
    coordinates: number[] | number[][][];
  };
}

interface ProbabilityRingsLayerProps {
  map: maplibregl.Map | null;
  features: RingFeature[];
}

export default function ProbabilityRingsLayer({
  map,
  features,
}: ProbabilityRingsLayerProps) {
  useEffect(() => {
    if (!map || features.length === 0) return;

    const sourceId = "lpb-rings";
    const fillLayerId = "lpb-rings-fill";
    const outlineLayerId = "lpb-rings-outline";
    const labelLayerId = "lpb-rings-labels";
    const ippMarkerId = "lpb-ipp";

    const ringFeatures = features.filter(
      (f) => f.properties.percentile !== undefined,
    );
    const ippFeature = features.find((f) => f.properties.type === "ipp");

    // Rings — render outermost first (largest) for correct layering
    const sortedRings = [...ringFeatures].sort(
      (a, b) => (b.properties.radius_km ?? 0) - (a.properties.radius_km ?? 0),
    );

    const geojson: GeoJSON.FeatureCollection = {
      type: "FeatureCollection",
      features: sortedRings as unknown as GeoJSON.Feature[],
    };

    const existingSource = map.getSource(sourceId) as
      | maplibregl.GeoJSONSource
      | undefined;
    if (existingSource) {
      existingSource.setData(geojson);
    } else {
      map.addSource(sourceId, { type: "geojson", data: geojson });

      map.addLayer({
        id: fillLayerId,
        type: "fill",
        source: sourceId,
        paint: {
          "fill-color": ["get", "color"],
          "fill-opacity": 0.12,
        },
      });

      map.addLayer({
        id: outlineLayerId,
        type: "line",
        source: sourceId,
        paint: {
          "line-color": ["get", "color"],
          "line-width": 2,
          "line-dasharray": [4, 2],
        },
      });

      // Click popup for rings
      map.on("click", fillLayerId, (e) => {
        if (!e.features?.[0]) return;
        const props = e.features[0].properties;
        if (!props) return;
        new maplibregl.Popup()
          .setLngLat(e.lngLat)
          .setHTML(
            `<div class="text-sm">
              <strong>${props.percentile_label}</strong><br/>
              Radius: ${props.radius_km} km<br/>
              Profile: ${props.profile}
            </div>`,
          )
          .addTo(map);
      });
    }

    // IPP marker
    if (ippFeature && ippFeature.geometry.type === "Point") {
      const coords = ippFeature.geometry.coordinates as [number, number];
      const el = document.createElement("div");
      el.style.width = "16px";
      el.style.height = "16px";
      el.style.borderRadius = "50%";
      el.style.backgroundColor = "#e11d48";
      el.style.border = "3px solid white";
      el.style.boxShadow = "0 2px 6px rgba(0,0,0,0.4)";

      const marker = new maplibregl.Marker({ element: el })
        .setLngLat(coords)
        .setPopup(
          new maplibregl.Popup({ offset: 12 }).setHTML(
            `<div class="text-sm font-medium">Initial Planning Point (IPP)</div>`,
          ),
        )
        .addTo(map);

      return () => {
        marker.remove();
        if (map.getLayer(fillLayerId)) map.removeLayer(fillLayerId);
        if (map.getLayer(outlineLayerId)) map.removeLayer(outlineLayerId);
        if (map.getLayer(labelLayerId)) map.removeLayer(labelLayerId);
        if (map.getSource(sourceId)) map.removeSource(sourceId);
      };
    }

    return () => {
      if (map.getLayer(fillLayerId)) map.removeLayer(fillLayerId);
      if (map.getLayer(outlineLayerId)) map.removeLayer(outlineLayerId);
      if (map.getLayer(labelLayerId)) map.removeLayer(labelLayerId);
      if (map.getSource(sourceId)) map.removeSource(sourceId);
    };
  }, [map, features]);

  return null;
}
