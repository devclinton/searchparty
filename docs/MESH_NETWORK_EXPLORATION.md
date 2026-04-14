# Mesh Network Support Exploration

## Overview
In remote SAR operations, cellular and WiFi connectivity is often unavailable. Mesh networking devices can provide team-to-team communication for data sync without infrastructure.

## Evaluated Technologies

### Meshtastic
- **Protocol**: LoRa-based, open source
- **Range**: 1-10+ km depending on terrain and antenna
- **Data rate**: Very low (~200 bps effective)
- **Hardware**: ~$30 per device (Heltec, TTGO, RAK)
- **Integration**: Bluetooth serial API from mobile devices
- **Best for**: GPS position sharing, short messages, check-in pings
- **Limitations**: Too slow for syncing full incident data; best for lightweight telemetry

### goTenna
- **Protocol**: Proprietary mesh
- **Range**: 1-6 km
- **Data rate**: Low
- **Hardware**: ~$180 per device
- **Integration**: SDK available (iOS/Android)
- **Best for**: Text messaging, GPS sharing
- **Limitations**: Proprietary, higher cost, limited SDK availability

## Recommended Approach

### Phase 1: Position Sharing via Meshtastic
1. Pair Meshtastic device via Bluetooth to mobile app
2. Broadcast compressed GPS position packets (lat, lon, user_id, timestamp)
3. Receive other team positions and display on map
4. This enables team position awareness without cellular connectivity

### Phase 2: Check-in Sync
1. Broadcast check-in confirmations as short messages
2. Relay overdue alerts across mesh
3. Emergency distress signals with priority routing

### Phase 3: Data Sync (Future)
1. For full data sync, use the export/import file transfer system
2. Or explore store-and-forward of compressed data chunks over mesh
3. This is bandwidth-limited and complex — defer to Phase 3

## Integration Architecture
```
Mobile App <-> Bluetooth <-> Meshtastic Device <-> LoRa Mesh <-> Other Devices
     |                                                                |
     v                                                                v
Local IndexedDB                                              Other Mobile Apps
```

## Status
- Research complete
- Implementation deferred to post-launch
- The offline action queue and file export/import systems provide the foundation
  that mesh networking would build upon
