"use client";

import { useMesh } from "@/hooks/useMesh";
import type { MeshNode } from "@/lib/mesh/types";

export default function MeshDashboard() {
  const {
    connectionState,
    nodes,
    positions,
    messages,
    error,
    connectSerial,
    connectBluetooth,
    disconnect,
    sendCheckIn,
    sendMessage,
  } = useMesh();

  const stateColors = {
    disconnected: "text-zinc-500",
    connecting: "text-yellow-600",
    connected: "text-green-600",
    error: "text-red-600",
  };

  return (
    <div className="space-y-4 text-sm">
      {/* Connection */}
      <div className="flex items-center gap-3">
        <span className={`font-medium ${stateColors[connectionState]}`}>
          Mesh: {connectionState}
        </span>
        {connectionState === "disconnected" && (
          <div className="flex gap-2">
            <button
              onClick={connectSerial}
              className="px-3 py-1 bg-zinc-800 text-white rounded text-xs hover:bg-zinc-700"
            >
              USB
            </button>
            <button
              onClick={connectBluetooth}
              className="px-3 py-1 bg-indigo-600 text-white rounded text-xs hover:bg-indigo-500"
            >
              Bluetooth
            </button>
          </div>
        )}
        {connectionState === "connected" && (
          <button
            onClick={disconnect}
            className="px-3 py-1 bg-zinc-200 rounded text-xs hover:bg-zinc-300 dark:bg-zinc-700"
          >
            Disconnect
          </button>
        )}
        {error && <span className="text-red-500 text-xs">{error}</span>}
      </div>

      {connectionState !== "connected" && (
        <p className="text-zinc-400 text-xs">
          Connect a Meshtastic device via USB or Bluetooth for off-grid team
          tracking.
        </p>
      )}

      {connectionState === "connected" && (
        <>
          {/* Nodes */}
          <div>
            <h4 className="font-medium mb-1">Nodes ({nodes.size})</h4>
            <div className="space-y-1">
              {Array.from(nodes.values()).map((node) => (
                <NodeRow
                  key={node.id}
                  node={node}
                  hasPosition={positions.has(node.id)}
                />
              ))}
              {nodes.size === 0 && (
                <p className="text-zinc-400 text-xs">
                  Waiting for node discovery...
                </p>
              )}
            </div>
          </div>

          {/* Quick Check-in */}
          <div>
            <h4 className="font-medium mb-1">Quick Check-in</h4>
            <div className="flex flex-wrap gap-1">
              <button
                onClick={() => sendCheckIn("OK")}
                className="px-2 py-1 bg-green-100 text-green-800 rounded text-xs dark:bg-green-900 dark:text-green-200"
              >
                OK
              </button>
              <button
                onClick={() => sendCheckIn("RETURNING")}
                className="px-2 py-1 bg-blue-100 text-blue-800 rounded text-xs dark:bg-blue-900 dark:text-blue-200"
              >
                Returning
              </button>
              <button
                onClick={() => sendCheckIn("NEED_ASSIST")}
                className="px-2 py-1 bg-yellow-100 text-yellow-800 rounded text-xs dark:bg-yellow-900 dark:text-yellow-200"
              >
                Need Help
              </button>
              <button
                onClick={() => sendCheckIn("EMERGENCY")}
                className="px-2 py-1 bg-red-100 text-red-800 rounded text-xs font-bold dark:bg-red-900 dark:text-red-200"
              >
                EMERGENCY
              </button>
            </div>
          </div>

          {/* Messages */}
          <div>
            <h4 className="font-medium mb-1">Messages ({messages.length})</h4>
            <div className="max-h-40 overflow-y-auto space-y-1">
              {messages
                .slice(-10)
                .reverse()
                .map((msg) => {
                  const node = nodes.get(msg.from);
                  const sender = node?.shortName || msg.from;
                  const time = new Date(
                    msg.timestamp * 1000,
                  ).toLocaleTimeString();
                  const isEmergency = msg.text.includes("EMERGENCY");
                  return (
                    <div
                      key={msg.id}
                      className={`text-xs px-2 py-1 rounded ${
                        isEmergency
                          ? "bg-red-100 dark:bg-red-900"
                          : "bg-zinc-100 dark:bg-zinc-800"
                      }`}
                    >
                      <span className="font-medium">{sender}</span>
                      <span className="text-zinc-400 ml-1">{time}</span>
                      <p>{msg.text}</p>
                    </div>
                  );
                })}
              {messages.length === 0 && (
                <p className="text-zinc-400 text-xs">No messages yet</p>
              )}
            </div>
          </div>
        </>
      )}
    </div>
  );
}

function NodeRow({
  node,
  hasPosition,
}: {
  node: MeshNode;
  hasPosition: boolean;
}) {
  const age = Math.round((Date.now() / 1000 - node.lastHeard) / 60);
  const ageStr = age < 60 ? `${age}m` : `${Math.round(age / 60)}h`;
  const batteryColor =
    node.batteryLevel > 50
      ? "text-green-600"
      : node.batteryLevel > 20
        ? "text-yellow-600"
        : "text-red-600";

  return (
    <div className="flex items-center gap-2 text-xs bg-zinc-50 dark:bg-zinc-800 px-2 py-1 rounded">
      <span className="font-medium w-20 truncate">
        {node.longName || node.shortName}
      </span>
      <span className={batteryColor}>{node.batteryLevel}%</span>
      <span className="text-zinc-400">SNR:{node.snr.toFixed(0)}</span>
      {hasPosition && <span className="text-green-500">GPS</span>}
      <span className="text-zinc-400 ml-auto">{ageStr}</span>
    </div>
  );
}
