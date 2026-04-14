/**
 * Unified offline data store using IndexedDB.
 *
 * Caches incident data, team data, hazard zones, and other
 * field-critical information for offline access.
 */

const DB_NAME = "searchparty-offline";
const DB_VERSION = 1;

const STORES = {
  incidents: "incidents",
  teams: "teams",
  segments: "segments",
  hazards: "hazards",
  clues: "clues",
  members: "members",
  briefings: "briefings",
} as const;

function openDB(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(DB_NAME, DB_VERSION);
    request.onerror = () => reject(request.error);
    request.onsuccess = () => resolve(request.result);
    request.onupgradeneeded = () => {
      const db = request.result;
      for (const name of Object.values(STORES)) {
        if (!db.objectStoreNames.contains(name)) {
          const store = db.createObjectStore(name, { keyPath: "id" });
          store.createIndex("incident_id", "incident_id");
        }
      }
    };
  });
}

/**
 * Save a single record to a store.
 */
export async function put(
  storeName: string,
  record: Record<string, unknown>,
): Promise<void> {
  const db = await openDB();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(storeName, "readwrite");
    tx.objectStore(storeName).put(record);
    tx.oncomplete = () => resolve();
    tx.onerror = () => reject(tx.error);
  });
}

/**
 * Save multiple records to a store (replaces all for an incident).
 */
export async function putMany(
  storeName: string,
  records: Record<string, unknown>[],
  incidentId?: string,
): Promise<void> {
  const db = await openDB();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(storeName, "readwrite");
    const store = tx.objectStore(storeName);

    // If incident-scoped, delete existing records for this incident first
    if (incidentId) {
      const index = store.index("incident_id");
      const request = index.openCursor(IDBKeyRange.only(incidentId));
      request.onsuccess = () => {
        const cursor = request.result;
        if (cursor) {
          cursor.delete();
          cursor.continue();
        } else {
          // All old records deleted, now add new ones
          for (const record of records) {
            store.put(record);
          }
        }
      };
    } else {
      for (const record of records) {
        store.put(record);
      }
    }

    tx.oncomplete = () => resolve();
    tx.onerror = () => reject(tx.error);
  });
}

/**
 * Get a single record by ID.
 */
export async function get(
  storeName: string,
  id: string,
): Promise<Record<string, unknown> | null> {
  const db = await openDB();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(storeName, "readonly");
    const request = tx.objectStore(storeName).get(id);
    request.onerror = () => reject(request.error);
    request.onsuccess = () =>
      resolve((request.result as Record<string, unknown>) ?? null);
  });
}

/**
 * Get all records for an incident from a store.
 */
export async function getByIncident(
  storeName: string,
  incidentId: string,
): Promise<Record<string, unknown>[]> {
  const db = await openDB();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(storeName, "readonly");
    const index = tx.objectStore(storeName).index("incident_id");
    const request = index.getAll(incidentId);
    request.onerror = () => reject(request.error);
    request.onsuccess = () =>
      resolve(request.result as Record<string, unknown>[]);
  });
}

/**
 * Get all records from a store.
 */
export async function getAll(
  storeName: string,
): Promise<Record<string, unknown>[]> {
  const db = await openDB();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(storeName, "readonly");
    const request = tx.objectStore(storeName).getAll();
    request.onerror = () => reject(request.error);
    request.onsuccess = () =>
      resolve(request.result as Record<string, unknown>[]);
  });
}

/**
 * Delete a record by ID.
 */
export async function remove(storeName: string, id: string): Promise<void> {
  const db = await openDB();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(storeName, "readwrite");
    tx.objectStore(storeName).delete(id);
    tx.oncomplete = () => resolve();
    tx.onerror = () => reject(tx.error);
  });
}

/**
 * Clear all data from all stores.
 */
export async function clearAll(): Promise<void> {
  const db = await openDB();
  return new Promise((resolve, reject) => {
    const storeNames = Object.values(STORES);
    const tx = db.transaction(storeNames, "readwrite");
    for (const name of storeNames) {
      tx.objectStore(name).clear();
    }
    tx.oncomplete = () => resolve();
    tx.onerror = () => reject(tx.error);
  });
}
