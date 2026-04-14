"use client";

import { useSyncStatus } from "@/hooks/useSyncStatus";

export default function SyncStatusIndicator() {
  const { status, pendingActions, lastSyncAt, lastError, triggerSync } =
    useSyncStatus();

  const statusConfig = {
    online: {
      label: "Online",
      color: "bg-green-500",
      textColor: "text-green-700",
    },
    offline: {
      label: "Offline",
      color: "bg-yellow-500",
      textColor: "text-yellow-700",
    },
    syncing: {
      label: "Syncing...",
      color: "bg-blue-500",
      textColor: "text-blue-700",
    },
    error: {
      label: "Sync Error",
      color: "bg-red-500",
      textColor: "text-red-700",
    },
  };

  const config = statusConfig[status];

  return (
    <div className="flex items-center gap-2 text-xs">
      <span className={`inline-block w-2 h-2 rounded-full ${config.color}`} />
      <span className={config.textColor}>{config.label}</span>

      {pendingActions > 0 && (
        <span className="text-zinc-500">({pendingActions} pending)</span>
      )}

      {status === "offline" && pendingActions > 0 && (
        <span className="text-zinc-400">Will sync when online</span>
      )}

      {status === "online" && pendingActions > 0 && (
        <button
          onClick={() => triggerSync()}
          className="text-blue-600 hover:underline dark:text-blue-400"
        >
          Sync now
        </button>
      )}

      {lastError && <span className="text-red-500">{lastError}</span>}
    </div>
  );
}
