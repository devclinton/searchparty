"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { meshConnection } from "@/lib/mesh/connection";
import type {
  MeshConnectionState,
  MeshMessage,
  MeshNode,
  MeshPacket,
  MeshPosition,
} from "@/lib/mesh/types";
import { CHECKIN_MESSAGES, type CheckInMessageKey } from "@/lib/mesh/types";

interface MeshState {
  connectionState: MeshConnectionState;
  nodes: Map<string, MeshNode>;
  positions: Map<string, MeshPosition>;
  messages: MeshMessage[];
  error: string | null;
}

export function useMesh() {
  const [state, setState] = useState<MeshState>({
    connectionState: "disconnected",
    nodes: new Map(),
    positions: new Map(),
    messages: [],
    error: null,
  });

  const nodesRef = useRef(new Map<string, MeshNode>());
  const positionsRef = useRef(new Map<string, MeshPosition>());
  const messagesRef = useRef<MeshMessage[]>([]);

  useEffect(() => {
    const unsubState = meshConnection.onStateChange((connState) => {
      setState((s) => ({ ...s, connectionState: connState }));
    });

    const unsubPacket = meshConnection.onPacket((packet: MeshPacket) => {
      switch (packet.type) {
        case "position": {
          const pos = packet.payload as MeshPosition;
          positionsRef.current.set(pos.nodeId, pos);
          setState((s) => ({
            ...s,
            positions: new Map(positionsRef.current),
          }));
          break;
        }
        case "text": {
          const msg = packet.payload as MeshMessage;
          messagesRef.current = [...messagesRef.current.slice(-99), msg];
          setState((s) => ({
            ...s,
            messages: [...messagesRef.current],
          }));
          break;
        }
        case "nodeinfo": {
          const node = packet.payload as MeshNode;
          nodesRef.current.set(node.id, node);
          setState((s) => ({
            ...s,
            nodes: new Map(nodesRef.current),
          }));
          break;
        }
      }
    });

    return () => {
      unsubState();
      unsubPacket();
    };
  }, []);

  const connectSerial = useCallback(async () => {
    try {
      setState((s) => ({ ...s, error: null }));
      await meshConnection.connectSerial();
    } catch (err) {
      setState((s) => ({
        ...s,
        error: err instanceof Error ? err.message : "Connection failed",
      }));
    }
  }, []);

  const connectBluetooth = useCallback(async () => {
    try {
      setState((s) => ({ ...s, error: null }));
      await meshConnection.connectBluetooth();
    } catch (err) {
      setState((s) => ({
        ...s,
        error: err instanceof Error ? err.message : "Connection failed",
      }));
    }
  }, []);

  const disconnect = useCallback(async () => {
    await meshConnection.disconnect();
  }, []);

  const sendMessage = useCallback(async (text: string) => {
    await meshConnection.sendText(text);
  }, []);

  const sendCheckIn = useCallback(async (key: CheckInMessageKey) => {
    await meshConnection.sendText(CHECKIN_MESSAGES[key]);
  }, []);

  return {
    ...state,
    connectSerial,
    connectBluetooth,
    disconnect,
    sendMessage,
    sendCheckIn,
  };
}
