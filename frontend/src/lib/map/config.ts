export const MAP_STYLES = {
  osm: {
    version: 8 as const,
    name: "OpenStreetMap",
    sources: {
      osm: {
        type: "raster" as const,
        tiles: ["https://tile.openstreetmap.org/{z}/{x}/{y}.png"],
        tileSize: 256,
        attribution:
          '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
      },
    },
    layers: [
      {
        id: "osm-tiles",
        type: "raster" as const,
        source: "osm",
        minzoom: 0,
        maxzoom: 19,
      },
    ],
  },
  topo: {
    version: 8 as const,
    name: "OpenTopoMap",
    sources: {
      topo: {
        type: "raster" as const,
        tiles: ["https://tile.opentopomap.org/{z}/{x}/{y}.png"],
        tileSize: 256,
        attribution:
          '&copy; <a href="https://opentopomap.org">OpenTopoMap</a> (<a href="https://creativecommons.org/licenses/by-sa/3.0/">CC-BY-SA</a>)',
      },
    },
    layers: [
      {
        id: "topo-tiles",
        type: "raster" as const,
        source: "topo",
        minzoom: 0,
        maxzoom: 17,
      },
    ],
  },
};

export type MapStyleKey = keyof typeof MAP_STYLES;

export const DEFAULT_CENTER: [number, number] = [-121.6959, 45.3735]; // Mt. Hood area
export const DEFAULT_ZOOM = 10;

export const COORDINATE_FORMATS = ["dd", "dms", "utm", "mgrs"] as const;
export type CoordinateFormat = (typeof COORDINATE_FORMATS)[number];
