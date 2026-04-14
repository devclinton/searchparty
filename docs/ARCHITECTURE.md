# Architecture Overview

## System Architecture

```
┌──────────────────────────────────────────────────────┐
│                    Client Devices                     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │
│  │  PWA (Web)  │  │  Android    │  │    iOS      │  │
│  │  Next.js    │  │  Capacitor  │  │  Capacitor  │  │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  │
│         │                │                │          │
│         └────────────────┼────────────────┘          │
│                          │                           │
│              ┌───────────┴───────────┐               │
│              │   Offline Storage     │               │
│              │   (IndexedDB/SQLite)  │               │
│              └───────────┬───────────┘               │
└──────────────────────────┼───────────────────────────┘
                           │ HTTP/WebSocket
                           │ (when online)
┌──────────────────────────┼───────────────────────────┐
│                   Backend Server                      │
│              ┌───────────┴───────────┐               │
│              │    FastAPI (Python)    │               │
│              │  ┌─────────────────┐  │               │
│              │  │   API Routes    │  │               │
│              │  │   Auth / RBAC   │  │               │
│              │  │   Services      │  │               │
│              │  │   POD / LPB     │  │               │
│              │  └─────────────────┘  │               │
│              └───────────┬───────────┘               │
│                          │                           │
│              ┌───────────┴───────────┐               │
│              │    PostgreSQL + GIS    │               │
│              └───────────────────────┘               │
└──────────────────────────────────────────────────────┘
```

## Key Architectural Decisions

### Offline-First
All field-critical features work without connectivity. The app stores data in IndexedDB (web) or SQLite (native) and syncs when connectivity is restored. This is non-negotiable for SAR operations in remote areas.

### ICS as Permission Model
The Incident Command System hierarchy maps directly to our authorization model:
- **Incident Commander**: Full access to all incident data
- **Operations Chief**: Manage teams and assignments
- **Division Supervisor**: Manage assigned teams
- **Team Leader**: View team assignment, update team status
- **Searcher**: View own assignment, record GPS track

### No ORM
All database queries use raw parameterized SQL via `asyncpg` for maximum performance and control. This avoids N+1 query problems and gives us direct control over query optimization.

### PostGIS for Spatial Data
PostgreSQL with PostGIS extension handles all geographic computations: distance calculations, polygon intersections, point-in-polygon checks, and spatial indexing.

## Data Flow

### Online Mode
1. Client sends request to FastAPI
2. FastAPI validates, checks permissions via ICS role
3. Service layer executes business logic
4. Raw SQL queries via asyncpg to PostgreSQL
5. Response returned to client
6. Client updates local IndexedDB cache

### Offline Mode
1. Client stores action in offline queue (IndexedDB)
2. GPS tracks continue recording locally
3. Check-ins logged locally with timestamps
4. When connectivity restored: queue replays to server
5. Conflict resolution applies (last-writer-wins with merge)

## Technology Stack

| Layer | Technology | Rationale |
|-------|-----------|-----------|
| Frontend | Next.js + React | SSR for SEO, PWA for offline |
| Mobile | Capacitor | Single codebase for Android + iOS |
| Backend | FastAPI (Python) | Async, fast, great typing |
| Database | PostgreSQL + PostGIS | Spatial queries, reliability |
| Maps | Leaflet or MapLibre GL | Open source, offline tile support |
| Offline | IndexedDB + Service Workers | Web standard, no dependencies |
| i18n | next-intl (FE) + JSON (BE) | 15 languages supported |
