const DB_NAME = "searchparty-tiles";
const DB_VERSION = 1;
const STORE_NAME = "tiles";

function openDB(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(DB_NAME, DB_VERSION);
    request.onerror = () => reject(request.error);
    request.onsuccess = () => resolve(request.result);
    request.onupgradeneeded = () => {
      const db = request.result;
      if (!db.objectStoreNames.contains(STORE_NAME)) {
        db.createObjectStore(STORE_NAME);
      }
    };
  });
}

/**
 * Get a cached tile from IndexedDB.
 */
export async function getCachedTile(key: string): Promise<Blob | null> {
  const db = await openDB();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(STORE_NAME, "readonly");
    const store = tx.objectStore(STORE_NAME);
    const request = store.get(key);
    request.onerror = () => reject(request.error);
    request.onsuccess = () => resolve(request.result as Blob | null);
  });
}

/**
 * Store a tile in IndexedDB.
 */
export async function cacheTile(key: string, blob: Blob): Promise<void> {
  const db = await openDB();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(STORE_NAME, "readwrite");
    const store = tx.objectStore(STORE_NAME);
    const request = store.put(blob, key);
    request.onerror = () => reject(request.error);
    request.onsuccess = () => resolve();
  });
}

/**
 * Generate tile URLs for a bounding box at specified zoom levels.
 */
function getTileRange(
  bounds: { north: number; south: number; east: number; west: number },
  zoom: number,
): { x: number; y: number; z: number }[] {
  const tiles: { x: number; y: number; z: number }[] = [];
  const n = Math.pow(2, zoom);

  const xMin = Math.floor(((bounds.west + 180) / 360) * n);
  const xMax = Math.floor(((bounds.east + 180) / 360) * n);
  const yMin = Math.floor(
    ((1 -
      Math.log(
        Math.tan((bounds.north * Math.PI) / 180) +
          1 / Math.cos((bounds.north * Math.PI) / 180),
      ) /
        Math.PI) /
      2) *
      n,
  );
  const yMax = Math.floor(
    ((1 -
      Math.log(
        Math.tan((bounds.south * Math.PI) / 180) +
          1 / Math.cos((bounds.south * Math.PI) / 180),
      ) /
        Math.PI) /
      2) *
      n,
  );

  for (let x = xMin; x <= xMax; x++) {
    for (let y = yMin; y <= yMax; y++) {
      tiles.push({ x, y, z: zoom });
    }
  }
  return tiles;
}

/**
 * Count tiles that would be downloaded for the given bounds and zoom levels.
 */
export function countTiles(
  bounds: { north: number; south: number; east: number; west: number },
  zoomMin: number,
  zoomMax: number,
): number {
  let count = 0;
  for (let z = zoomMin; z <= zoomMax; z++) {
    count += getTileRange(bounds, z).length;
  }
  return count;
}

/**
 * Download and cache tiles for a given area and zoom range.
 * Returns progress via callback.
 */
export async function downloadTilesForArea(
  tileUrlTemplate: string,
  bounds: { north: number; south: number; east: number; west: number },
  zoomMin: number,
  zoomMax: number,
  onProgress?: (downloaded: number, total: number) => void,
): Promise<number> {
  let downloaded = 0;
  let total = 0;

  const allTiles: { x: number; y: number; z: number }[] = [];
  for (let z = zoomMin; z <= zoomMax; z++) {
    allTiles.push(...getTileRange(bounds, z));
  }
  total = allTiles.length;

  // Download in batches to avoid overwhelming the network
  const BATCH_SIZE = 6;
  for (let i = 0; i < allTiles.length; i += BATCH_SIZE) {
    const batch = allTiles.slice(i, i + BATCH_SIZE);
    await Promise.all(
      batch.map(async (tile) => {
        const url = tileUrlTemplate
          .replace("{z}", String(tile.z))
          .replace("{x}", String(tile.x))
          .replace("{y}", String(tile.y));
        const key = `${tile.z}/${tile.x}/${tile.y}`;

        try {
          // Check if already cached
          const existing = await getCachedTile(key);
          if (!existing) {
            const response = await fetch(url);
            if (response.ok) {
              const blob = await response.blob();
              await cacheTile(key, blob);
            }
          }
          downloaded++;
          onProgress?.(downloaded, total);
        } catch {
          // Skip failed tiles silently
          downloaded++;
          onProgress?.(downloaded, total);
        }
      }),
    );
  }

  return downloaded;
}

/**
 * Get approximate cache size in bytes.
 */
export async function getCacheSize(): Promise<number> {
  const db = await openDB();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(STORE_NAME, "readonly");
    const store = tx.objectStore(STORE_NAME);
    const request = store.getAll();
    request.onerror = () => reject(request.error);
    request.onsuccess = () => {
      const blobs = request.result as Blob[];
      const totalSize = blobs.reduce((sum, blob) => sum + blob.size, 0);
      resolve(totalSize);
    };
  });
}

/**
 * Clear all cached tiles.
 */
export async function clearTileCache(): Promise<void> {
  const db = await openDB();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(STORE_NAME, "readwrite");
    const store = tx.objectStore(STORE_NAME);
    const request = store.clear();
    request.onerror = () => reject(request.error);
    request.onsuccess = () => resolve();
  });
}
