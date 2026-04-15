/**
 * Meshtastic mesh network types.
 *
 * Based on the Meshtastic protobuf definitions.
 * We use a simplified JS representation since we decode
 * protobuf binary on the device side and receive JSON-like objects.
 */

export interface MeshNode {
  id: string; // Node number as hex string
  longName: string;
  shortName: string;
  macaddr: string;
  hwModel: string;
  role: string;
  lastHeard: number; // Unix timestamp
  snr: number;
  batteryLevel: number; // 0-100
  voltage: number;
  channelUtilization: number;
  airUtilTx: number;
}

export interface MeshPosition {
  nodeId: string;
  latitude: number;
  longitude: number;
  altitude: number | null;
  satsInView: number;
  precisionBits: number;
  timestamp: number;
}

export interface MeshMessage {
  id: string;
  from: string; // Node ID
  to: string; // Node ID or "broadcast"
  channel: number;
  text: string;
  timestamp: number;
  hopLimit: number;
  rxSnr: number;
}

export interface MeshPacket {
  type: "position" | "text" | "nodeinfo" | "telemetry" | "unknown";
  from: string;
  to: string;
  payload: MeshPosition | MeshMessage | MeshNode | Record<string, unknown>;
  rxTime: number;
  rxSnr: number;
  hopLimit: number;
}

export type MeshConnectionState =
  | "disconnected"
  | "connecting"
  | "connected"
  | "error";

export interface MeshConfig {
  channelName: string;
  channelPsk: string; // Pre-shared key (base64)
  region: string;
  positionBroadcastSecs: number;
  hopLimit: number;
}

export const DEFAULT_MESH_CONFIG: MeshConfig = {
  channelName: "SearchParty",
  channelPsk: "",
  region: "US",
  positionBroadcastSecs: 60,
  hopLimit: 3,
};

// Predefined check-in messages
export const CHECKIN_MESSAGES = {
  OK: "CHECK-IN: OK",
  NEED_ASSIST: "CHECK-IN: NEED ASSISTANCE",
  EMERGENCY: "EMERGENCY: DISTRESS",
  RETURNING: "CHECK-IN: RETURNING",
  AT_WAYPOINT: "CHECK-IN: AT WAYPOINT",
} as const;

export type CheckInMessageKey = keyof typeof CHECKIN_MESSAGES;
