/**
 * Sync manager — coordinates online/offline state, background sync,
 * and conflict resolution.
 *
 * Conflict resolution strategy: last-writer-wins with timestamp.
 * Each record includes an `updated_at` field. When syncing, the server
 * compares timestamps and keeps the most recent version. For concurrent
 * edits to the same field, the latest timestamp wins.
 */

import { getQueueSize, replayQueue } from "./action-queue";
import { syncGpsTracks } from "../map/gps-sync";

export type SyncStatus = "online" | "offline" | "syncing" | "error";

export interface SyncState {
  status: SyncStatus;
  pendingActions: number;
  lastSyncAt: number | null;
  lastError: string | null;
}

type SyncListener = (state: SyncState) => void;

class SyncManager {
  private state: SyncState = {
    status: navigator.onLine ? "online" : "offline",
    pendingActions: 0,
    lastSyncAt: null,
    lastError: null,
  };
  private listeners: Set<SyncListener> = new Set();
  private syncInProgress = false;

  constructor() {
    if (typeof window !== "undefined") {
      window.addEventListener("online", () => this.handleOnline());
      window.addEventListener("offline", () => this.handleOffline());
      // Check queue size on init
      this.updateQueueSize();
    }
  }

  subscribe(listener: SyncListener): () => void {
    this.listeners.add(listener);
    listener(this.state);
    return () => this.listeners.delete(listener);
  }

  getState(): SyncState {
    return { ...this.state };
  }

  private notify(): void {
    for (const listener of this.listeners) {
      listener({ ...this.state });
    }
  }

  private async updateQueueSize(): Promise<void> {
    try {
      this.state.pendingActions = await getQueueSize();
      this.notify();
    } catch {
      // IndexedDB not available (SSR)
    }
  }

  private handleOffline(): void {
    this.state.status = "offline";
    this.notify();
  }

  private async handleOnline(): Promise<void> {
    this.state.status = "online";
    this.notify();

    // Auto-sync when coming back online
    await this.sync();
  }

  /**
   * Trigger a manual sync. Replays queued actions and syncs GPS tracks.
   */
  async sync(apiBase?: string, accessToken?: string): Promise<void> {
    if (this.syncInProgress || !navigator.onLine) return;

    this.syncInProgress = true;
    this.state.status = "syncing";
    this.state.lastError = null;
    this.notify();

    try {
      // Replay queued actions
      const { succeeded, failed } = await replayQueue();

      // Sync GPS tracks if credentials provided
      if (apiBase && accessToken) {
        await syncGpsTracks(apiBase, accessToken);
      }

      this.state.lastSyncAt = Date.now();
      this.state.status = "online";

      if (failed > 0) {
        this.state.lastError = `${failed} action(s) failed to sync`;
      }
    } catch (err) {
      this.state.status = "error";
      this.state.lastError = err instanceof Error ? err.message : "Sync failed";
    } finally {
      this.syncInProgress = false;
      await this.updateQueueSize();
    }
  }
}

// Singleton
export const syncManager =
  typeof window !== "undefined" ? new SyncManager() : null;
