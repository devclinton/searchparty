"use client";

import { useEffect } from "react";
import maplibregl from "maplibre-gl";
import { podToColor } from "@/lib/map/pod";

export interface SegmentPod {
  id: string;
  polygon: [number, number][]; // [lon, lat] pairs
  pod: number;
  name: string;
  passes: number;
}

interface PodHeatmapLayerProps {
  map: maplibregl.Map | null;
  segments: SegmentPod[];
}

export default function PodHeatmapLayer({
  map,
  segments,
}: PodHeatmapLayerProps) {
  useEffect(() => {
    if (!map || segments.length === 0) return;

    const sourceId = "pod-heatmap";
    const fillLayerId = "pod-heatmap-fill";
    const outlineLayerId = "pod-heatmap-outline";

    const features: GeoJSON.Feature[] = segments.map((seg) => ({
      type: "Feature",
      properties: {
        id: seg.id,
        name: seg.name,
        pod: seg.pod,
        passes: seg.passes,
        color: podToColor(seg.pod),
      },
      geometry: {
        type: "Polygon",
        coordinates: [seg.polygon],
      },
    }));

    const geojson: GeoJSON.FeatureCollection = {
      type: "FeatureCollection",
      features,
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
          "fill-opacity": 0.35,
        },
      });

      map.addLayer({
        id: outlineLayerId,
        type: "line",
        source: sourceId,
        paint: {
          "line-color": "#000",
          "line-width": 1.5,
          "line-opacity": 0.6,
        },
      });

      // Popup on click
      map.on("click", fillLayerId, (e) => {
        if (!e.features?.[0]) return;
        const props = e.features[0].properties;
        if (!props) return;
        const podPct = (Number(props.pod) * 100).toFixed(1);
        new maplibregl.Popup()
          .setLngLat(e.lngLat)
          .setHTML(
            `<div class="text-sm">
              <strong>${props.name}</strong><br/>
              POD: ${podPct}%<br/>
              Passes: ${props.passes}
            </div>`,
          )
          .addTo(map);
      });
    }

    return () => {
      if (map.getLayer(fillLayerId)) map.removeLayer(fillLayerId);
      if (map.getLayer(outlineLayerId)) map.removeLayer(outlineLayerId);
      if (map.getSource(sourceId)) map.removeSource(sourceId);
    };
  }, [map, segments]);

  return null;
}
