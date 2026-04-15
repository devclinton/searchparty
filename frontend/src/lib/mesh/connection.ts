/**
 * Meshtastic device connection manager.
 *
 * Supports Web Serial API (USB) and Web Bluetooth API.
 * Communicates with the Meshtastic device using its serial protocol
 * which sends protobuf-encoded packets prefixed with a 4-byte header.
 *
 * Protocol: [0x94 0xc3 MSB LSB] [protobuf payload]
 * The protobuf payload is a FromRadio message.
 */

import type {
  MeshConnectionState,
  MeshNode,
  MeshPacket,
  MeshPosition,
  MeshMessage,
} from "./types";

type PacketHandler = (packet: MeshPacket) => void;
type StateHandler = (state: MeshConnectionState) => void;

const SERIAL_BAUD = 115200;
const HEADER_MAGIC = [0x94, 0xc3];

class MeshtasticConnection {
  private port: SerialPort | null = null;
  private reader: ReadableStreamDefaultReader<Uint8Array> | null = null;
  private writer: WritableStreamDefaultWriter<Uint8Array> | null = null;
  private state: MeshConnectionState = "disconnected";
  private packetHandlers: Set<PacketHandler> = new Set();
  private stateHandlers: Set<StateHandler> = new Set();
  private readLoop: Promise<void> | null = null;
  private buffer: Uint8Array = new Uint8Array(0);

  getState(): MeshConnectionState {
    return this.state;
  }

  onPacket(handler: PacketHandler): () => void {
    this.packetHandlers.add(handler);
    return () => this.packetHandlers.delete(handler);
  }

  onStateChange(handler: StateHandler): () => void {
    this.stateHandlers.add(handler);
    return () => this.stateHandlers.delete(handler);
  }

  private setState(state: MeshConnectionState): void {
    this.state = state;
    for (const handler of this.stateHandlers) {
      handler(state);
    }
  }

  private emitPacket(packet: MeshPacket): void {
    for (const handler of this.packetHandlers) {
      handler(packet);
    }
  }

  /**
   * Connect via Web Serial API (USB connection).
   */
  async connectSerial(): Promise<void> {
    if (!("serial" in navigator)) {
      throw new Error("Web Serial API not supported in this browser");
    }

    this.setState("connecting");

    try {
      this.port = await navigator.serial.requestPort();
      await this.port.open({ baudRate: SERIAL_BAUD });

      if (this.port.readable) {
        this.reader = this.port.readable.getReader();
      }
      if (this.port.writable) {
        this.writer = this.port.writable.getWriter();
      }

      this.setState("connected");
      this.readLoop = this.startReadLoop();
    } catch (err) {
      this.setState("error");
      throw err;
    }
  }

  /**
   * Connect via Web Bluetooth API.
   */
  async connectBluetooth(): Promise<void> {
    if (!("bluetooth" in navigator)) {
      throw new Error("Web Bluetooth API not supported in this browser");
    }

    this.setState("connecting");

    try {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const bt = (navigator as any).bluetooth;
      const device = await bt.requestDevice({
        filters: [{ services: ["6e400001-b5a3-f393-e0a9-e50e24dcca9e"] }],
      });

      const server = await device.gatt.connect();
      const service = await server.getPrimaryService(
        "6e400001-b5a3-f393-e0a9-e50e24dcca9e",
      );

      // TX characteristic (device -> phone): notifications
      const txChar = await service.getCharacteristic(
        "6e400003-b5a3-f393-e0a9-e50e24dcca9e",
      );
      await txChar.startNotifications();
      txChar.addEventListener(
        "characteristicvaluechanged",
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        (event: any) => {
          if (event.target?.value) {
            const data = new Uint8Array(event.target.value.buffer);
            this.processIncomingData(data);
          }
        },
      );

      // RX characteristic (phone -> device): write
      const rxChar = await service.getCharacteristic(
        "6e400002-b5a3-f393-e0a9-e50e24dcca9e",
      );
      // Store for sending
      (this as Record<string, unknown>)._btRxChar = rxChar;

      this.setState("connected");
    } catch (err) {
      this.setState("error");
      throw err;
    }
  }

  /**
   * Disconnect from the device.
   */
  async disconnect(): Promise<void> {
    try {
      if (this.reader) {
        await this.reader.cancel();
        this.reader = null;
      }
      if (this.writer) {
        await this.writer.close();
        this.writer = null;
      }
      if (this.port) {
        await this.port.close();
        this.port = null;
      }
    } catch {
      // Ignore errors during cleanup
    }
    this.setState("disconnected");
  }

  /**
   * Send a text message over the mesh.
   */
  async sendText(text: string, to: string = "broadcast"): Promise<void> {
    // Build a ToRadio packet with a MeshPacket containing a text payload
    // This is a simplified version — full implementation would use protobuf encoding
    const payload = new TextEncoder().encode(text);
    await this.sendRaw(payload);
  }

  /**
   * Send raw bytes to the device.
   */
  private async sendRaw(data: Uint8Array): Promise<void> {
    if (this.writer) {
      // Serial: prepend header
      const header = new Uint8Array([
        ...HEADER_MAGIC,
        (data.length >> 8) & 0xff,
        data.length & 0xff,
      ]);
      await this.writer.write(new Uint8Array([...header, ...data]));
    }
  }

  /**
   * Continuous read loop for serial connection.
   */
  private async startReadLoop(): Promise<void> {
    if (!this.reader) return;

    try {
      while (true) {
        const { value, done } = await this.reader.read();
        if (done) break;
        if (value) {
          this.processIncomingData(value);
        }
      }
    } catch {
      // Connection lost
      this.setState("disconnected");
    }
  }

  /**
   * Process incoming raw bytes, buffer them, and extract packets.
   */
  private processIncomingData(data: Uint8Array): void {
    // Append to buffer
    const newBuf = new Uint8Array(this.buffer.length + data.length);
    newBuf.set(this.buffer);
    newBuf.set(data, this.buffer.length);
    this.buffer = newBuf;

    // Try to extract packets
    while (this.buffer.length >= 4) {
      // Look for magic header
      if (
        this.buffer[0] !== HEADER_MAGIC[0] ||
        this.buffer[1] !== HEADER_MAGIC[1]
      ) {
        // Skip byte and try again
        this.buffer = this.buffer.slice(1);
        continue;
      }

      const payloadLen = (this.buffer[2]! << 8) | this.buffer[3]!;
      if (this.buffer.length < 4 + payloadLen) {
        break; // Need more data
      }

      const payload = this.buffer.slice(4, 4 + payloadLen);
      this.buffer = this.buffer.slice(4 + payloadLen);

      // Decode the protobuf payload
      const packet = this.decodePacket(payload);
      if (packet) {
        this.emitPacket(packet);
      }
    }
  }

  /**
   * Decode a protobuf FromRadio message into our MeshPacket type.
   *
   * This is a simplified decoder that handles the most common packet types.
   * A full implementation would use the Meshtastic protobuf definitions.
   */
  private decodePacket(payload: Uint8Array): MeshPacket | null {
    // Simplified: try to parse as JSON if the device is in JSON mode
    // Many Meshtastic serial implementations can be configured for JSON output
    try {
      const text = new TextDecoder().decode(payload);
      if (text.startsWith("{")) {
        const json = JSON.parse(text);
        return this.parseJsonPacket(json);
      }
    } catch {
      // Not JSON — would need full protobuf decoder
    }

    return null;
  }

  private parseJsonPacket(json: Record<string, unknown>): MeshPacket | null {
    const packet = json.packet as Record<string, unknown> | undefined;
    if (!packet) return null;

    const from = String(packet.from || "");
    const to = String(packet.to || "");
    const rxTime = Number(packet.rxTime || Date.now() / 1000);
    const rxSnr = Number(packet.rxSnr || 0);
    const hopLimit = Number(packet.hopLimit || 0);

    const decoded = packet.decoded as Record<string, unknown> | undefined;
    if (!decoded) return null;

    const portnum = decoded.portnum as string | undefined;

    if (portnum === "POSITION_APP" || portnum === "3") {
      const pos = decoded.position as Record<string, unknown> | undefined;
      if (pos) {
        const position: MeshPosition = {
          nodeId: from,
          latitude: Number(pos.latitudeI || 0) / 1e7,
          longitude: Number(pos.longitudeI || 0) / 1e7,
          altitude: pos.altitude ? Number(pos.altitude) : null,
          satsInView: Number(pos.satsInView || 0),
          precisionBits: Number(pos.precisionBits || 0),
          timestamp: rxTime,
        };
        return {
          type: "position",
          from,
          to,
          payload: position,
          rxTime,
          rxSnr,
          hopLimit,
        };
      }
    }

    if (portnum === "TEXT_MESSAGE_APP" || portnum === "1") {
      const text = String(decoded.text || decoded.payload || "");
      const message: MeshMessage = {
        id: `${from}-${rxTime}`,
        from,
        to,
        channel: Number(packet.channel || 0),
        text,
        timestamp: rxTime,
        hopLimit,
        rxSnr,
      };
      return {
        type: "text",
        from,
        to,
        payload: message,
        rxTime,
        rxSnr,
        hopLimit,
      };
    }

    if (portnum === "NODEINFO_APP" || portnum === "4") {
      const user = decoded.user as Record<string, unknown> | undefined;
      if (user) {
        const node: MeshNode = {
          id: from,
          longName: String(user.longName || ""),
          shortName: String(user.shortName || ""),
          macaddr: String(user.macaddr || ""),
          hwModel: String(user.hwModel || ""),
          role: String(user.role || "CLIENT"),
          lastHeard: rxTime,
          snr: rxSnr,
          batteryLevel: 0,
          voltage: 0,
          channelUtilization: 0,
          airUtilTx: 0,
        };
        return {
          type: "nodeinfo",
          from,
          to,
          payload: node,
          rxTime,
          rxSnr,
          hopLimit,
        };
      }
    }

    return {
      type: "unknown",
      from,
      to,
      payload: decoded,
      rxTime,
      rxSnr,
      hopLimit,
    };
  }
}

// Singleton
export const meshConnection = new MeshtasticConnection();
