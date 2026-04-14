/**
 * Local storage for GPS tracks using IndexedDB.
 * Tracks are recorded locally and synced to the server when online.
 */

const DB_NAME = "searchparty-gps";
const DB_VERSION = 1;
const TRACKS_STORE = "tracks";
const POINTS_STORE = "points";

export interface GpsPoint {
  lat: number;
  lon: number;
  altitude: number | null;
  accuracy: number;
  timestamp: number;
  trackId: string;
}

export interface GpsTrack {
  id: string;
  userId: string;
  incidentId: string;
  teamId: string | null;
  startedAt: number;
  endedAt: number | null;
  synced: boolean;
  pointCount: number;
}

function openDB(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(DB_NAME, DB_VERSION);
    request.onerror = () => reject(request.error);
    request.onsuccess = () => resolve(request.result);
    request.onupgradeneeded = () => {
      const db = request.result;
      if (!db.objectStoreNames.contains(TRACKS_STORE)) {
        const trackStore = db.createObjectStore(TRACKS_STORE, {
          keyPath: "id",
        });
        trackStore.createIndex("synced", "synced");
        trackStore.createIndex("incidentId", "incidentId");
      }
      if (!db.objectStoreNames.contains(POINTS_STORE)) {
        const pointStore = db.createObjectStore(POINTS_STORE, {
          autoIncrement: true,
        });
        pointStore.createIndex("trackId", "trackId");
      }
    };
  });
}

export async function createTrack(track: GpsTrack): Promise<void> {
  const db = await openDB();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(TRACKS_STORE, "readwrite");
    const store = tx.objectStore(TRACKS_STORE);
    const request = store.put(track);
    request.onerror = () => reject(request.error);
    request.onsuccess = () => resolve();
  });
}

export async function addPoint(point: GpsPoint): Promise<void> {
  const db = await openDB();
  return new Promise((resolve, reject) => {
    const tx = db.transaction([POINTS_STORE, TRACKS_STORE], "readwrite");
    const pointStore = tx.objectStore(POINTS_STORE);
    pointStore.add(point);

    // Update point count on track
    const trackStore = tx.objectStore(TRACKS_STORE);
    const getReq = trackStore.get(point.trackId);
    getReq.onsuccess = () => {
      const track = getReq.result as GpsTrack | undefined;
      if (track) {
        track.pointCount++;
        trackStore.put(track);
      }
    };

    tx.oncomplete = () => resolve();
    tx.onerror = () => reject(tx.error);
  });
}

export async function endTrack(trackId: string): Promise<void> {
  const db = await openDB();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(TRACKS_STORE, "readwrite");
    const store = tx.objectStore(TRACKS_STORE);
    const request = store.get(trackId);
    request.onsuccess = () => {
      const track = request.result as GpsTrack | undefined;
      if (track) {
        track.endedAt = Date.now();
        store.put(track);
      }
    };
    tx.oncomplete = () => resolve();
    tx.onerror = () => reject(tx.error);
  });
}

export async function getTrackPoints(trackId: string): Promise<GpsPoint[]> {
  const db = await openDB();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(POINTS_STORE, "readonly");
    const store = tx.objectStore(POINTS_STORE);
    const index = store.index("trackId");
    const request = index.getAll(trackId);
    request.onerror = () => reject(request.error);
    request.onsuccess = () => resolve(request.result as GpsPoint[]);
  });
}

export async function getUnsyncedTracks(): Promise<GpsTrack[]> {
  const db = await openDB();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(TRACKS_STORE, "readonly");
    const store = tx.objectStore(TRACKS_STORE);
    const request = store.getAll();
    request.onerror = () => reject(request.error);
    request.onsuccess = () => {
      const all = request.result as GpsTrack[];
      resolve(all.filter((t) => !t.synced));
    };
  });
}

export async function markTrackSynced(trackId: string): Promise<void> {
  const db = await openDB();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(TRACKS_STORE, "readwrite");
    const store = tx.objectStore(TRACKS_STORE);
    const request = store.get(trackId);
    request.onsuccess = () => {
      const track = request.result as GpsTrack | undefined;
      if (track) {
        track.synced = true;
        store.put(track);
      }
    };
    tx.oncomplete = () => resolve();
    tx.onerror = () => reject(tx.error);
  });
}
