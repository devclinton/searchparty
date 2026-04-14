/**
 * Offline action queue.
 *
 * When the app is offline, API mutations (POST, PATCH, DELETE) are
 * stored in IndexedDB and replayed in order when connectivity returns.
 */

const DB_NAME = "searchparty-queue";
const DB_VERSION = 1;
const STORE_NAME = "actions";

export interface QueuedAction {
  id: string;
  method: string;
  url: string;
  body: string | null;
  headers: Record<string, string>;
  createdAt: number;
  retries: number;
}

function openDB(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(DB_NAME, DB_VERSION);
    request.onerror = () => reject(request.error);
    request.onsuccess = () => resolve(request.result);
    request.onupgradeneeded = () => {
      const db = request.result;
      if (!db.objectStoreNames.contains(STORE_NAME)) {
        db.createObjectStore(STORE_NAME, { keyPath: "id" });
      }
    };
  });
}

/**
 * Add an action to the offline queue.
 */
export async function enqueueAction(
  action: Omit<QueuedAction, "id" | "createdAt" | "retries">,
): Promise<string> {
  const db = await openDB();
  const id = `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
  const entry: QueuedAction = {
    ...action,
    id,
    createdAt: Date.now(),
    retries: 0,
  };
  return new Promise((resolve, reject) => {
    const tx = db.transaction(STORE_NAME, "readwrite");
    tx.objectStore(STORE_NAME).put(entry);
    tx.oncomplete = () => resolve(id);
    tx.onerror = () => reject(tx.error);
  });
}

/**
 * Get all queued actions in order.
 */
export async function getQueuedActions(): Promise<QueuedAction[]> {
  const db = await openDB();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(STORE_NAME, "readonly");
    const request = tx.objectStore(STORE_NAME).getAll();
    request.onerror = () => reject(request.error);
    request.onsuccess = () => {
      const actions = (request.result as QueuedAction[]).sort(
        (a, b) => a.createdAt - b.createdAt,
      );
      resolve(actions);
    };
  });
}

/**
 * Remove an action from the queue (after successful replay).
 */
export async function removeAction(id: string): Promise<void> {
  const db = await openDB();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(STORE_NAME, "readwrite");
    tx.objectStore(STORE_NAME).delete(id);
    tx.oncomplete = () => resolve();
    tx.onerror = () => reject(tx.error);
  });
}

/**
 * Increment retry count for a failed action.
 */
async function incrementRetry(action: QueuedAction): Promise<void> {
  const db = await openDB();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(STORE_NAME, "readwrite");
    tx.objectStore(STORE_NAME).put({ ...action, retries: action.retries + 1 });
    tx.oncomplete = () => resolve();
    tx.onerror = () => reject(tx.error);
  });
}

/**
 * Get count of queued actions.
 */
export async function getQueueSize(): Promise<number> {
  const db = await openDB();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(STORE_NAME, "readonly");
    const request = tx.objectStore(STORE_NAME).count();
    request.onerror = () => reject(request.error);
    request.onsuccess = () => resolve(request.result);
  });
}

/**
 * Replay all queued actions in order.
 * Returns the number of successfully replayed actions.
 */
export async function replayQueue(
  onProgress?: (completed: number, total: number, action: QueuedAction) => void,
): Promise<{ succeeded: number; failed: number }> {
  const actions = await getQueuedActions();
  let succeeded = 0;
  let failed = 0;
  const MAX_RETRIES = 3;

  for (let i = 0; i < actions.length; i++) {
    const action = actions[i]!;
    onProgress?.(i, actions.length, action);

    if (action.retries >= MAX_RETRIES) {
      await removeAction(action.id);
      failed++;
      continue;
    }

    try {
      const response = await fetch(action.url, {
        method: action.method,
        headers: action.headers,
        body: action.body,
      });

      if (response.ok || response.status === 409) {
        // Success or conflict (already applied) — remove from queue
        await removeAction(action.id);
        succeeded++;
      } else if (response.status >= 500) {
        // Server error — retry later
        await incrementRetry(action);
        failed++;
      } else {
        // Client error (4xx) — won't succeed on retry, discard
        await removeAction(action.id);
        failed++;
      }
    } catch {
      // Network error — stop replaying, we're offline again
      break;
    }
  }

  return { succeeded, failed };
}

/**
 * Clear the entire queue.
 */
export async function clearQueue(): Promise<void> {
  const db = await openDB();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(STORE_NAME, "readwrite");
    tx.objectStore(STORE_NAME).clear();
    tx.oncomplete = () => resolve();
    tx.onerror = () => reject(tx.error);
  });
}
