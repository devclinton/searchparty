"use client";

import { useEffect, useState } from "react";
import { syncManager, type SyncState } from "@/lib/offline/sync-manager";

const DEFAULT_STATE: SyncState = {
  status: "online",
  pendingActions: 0,
  lastSyncAt: null,
  lastError: null,
};

export function useSyncStatus() {
  const [state, setState] = useState<SyncState>(
    syncManager?.getState() ?? DEFAULT_STATE,
  );

  useEffect(() => {
    if (!syncManager) return;
    return syncManager.subscribe(setState);
  }, []);

  const triggerSync = async (apiBase?: string, accessToken?: string) => {
    await syncManager?.sync(apiBase, accessToken);
  };

  return { ...state, triggerSync };
}
