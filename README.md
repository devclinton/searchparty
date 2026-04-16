# SearchParty

**Open-source search and rescue coordination tool for organizing searches in remote places.**

> **BETA SOFTWARE** - SearchParty is under active development and not yet recommended for operational SAR use. Features may be incomplete, APIs may change, and bugs should be expected. Always defer to trained SAR leadership and established procedures.

> **DISCLAIMER** - This tool aids coordination and does not replace trained search and rescue leadership. No medical or rescue advice is provided. Use at your own risk. See [LICENSE](LICENSE) for full terms.

---

## What is SearchParty?

SearchParty is the first open-source tool that combines **offline mapping**, **real-time team tracking**, **Probability of Detection (POD) calculations**, **Lost Person Behavior modeling**, **drone search pattern generation**, and **ICS-structured team coordination** in a single package.

No existing open-source tool covers all of these together. SearchParty fills that gap.

### Key Features

**Incident Management**
- Create and manage search operations with full subject profiles
- ICS role-based access control (Incident Commander, Operations Chief, Division Supervisor, Team Leader, Searcher, Safety Officer)
- Incident status workflow: Planning > Active > Suspended > Closed
- Digital accountability board tracking all personnel

**Mapping & GPS**
- OpenStreetMap and topographic map layers via MapLibre GL
- Offline tile storage with area pre-download for field use
- GPS breadcrumb tracking with local storage and server sync
- Real-time team member positions on map
- Coordinate display in DD, DMS, UTM, and MGRS formats
- Compass and bearing measurement tools

**Search Operations**
- Define search segments as map polygons with auto area calculation
- POD tracking: `POD = 1 - e^(-coverage)` with cumulative multi-pass support
- Effective Sweep Width (ESW) based coverage calculation
- POD heatmap overlay showing probability across all segments
- Clue and evidence marking with GPS, photos, and type classification
- Coverage statistics dashboard

**Lost Person Behavior (LPB)**
- 15 subject profiles based on Koester's research (children by age, adults, hikers, hunters, dementia, despondent, and more)
- Auto-generated probability distance rings from the Initial Planning Point
- Travel behavior annotations per profile
- Terrain-adjusted probability modeling

**Safety**
- Hazard zone creation with geofence alerts
- One-tap emergency distress button with GPS coordinates
- Timed check-in system with overdue team detection
- Safety briefing checklists per team
- Safety officer dashboard
- Turnaround time enforcement

**Drone Integration**
- 4 search pattern generators: parallel track, expanding square, sector search, creeping line
- Camera FOV calculator with 8 drone model presets (DJI, Autel, Skydio, Parrot)
- Flight plan export: DJI WPML, MAVLink, KML, Litchi CSV
- Obstacle avoidance configuration per mission
- DJI SRT video telemetry import (per-frame GPS without hosting video)
- Drone fleet management

**GPS Data Import**
- 7 file formats: GPX, KML/KMZ, GeoJSON, Garmin FIT, Google Takeout, CSV
- Garmin inReach MapShare live feed integration
- Import preview with map display before committing

**Known Trails**
- OpenStreetMap trail data via Overpass API
- USFS/BLM/NPS shapefile import
- Trail junction detection for hasty search prioritization
- Custom trail drawing

**Mesh Networking**
- Meshtastic LoRa mesh integration via Web Serial and Web Bluetooth
- Off-grid position sharing and check-in messaging
- Emergency alert relay across mesh network
- MQTT bridge for server-side data ingestion

**Offline-First**
- Full PWA with service worker caching
- IndexedDB local data store for all field-critical data
- Offline action queue with automatic replay on reconnect
- Data export/import via JSON files for USB transfer

**Mobile**
- Capacitor-based Android and iOS apps from the same codebase
- Native GPS, camera, and compass integration
- Battery-optimized for extended field operations

**Internationalization**
- 15 languages: English, Spanish, French, German, Portuguese, Chinese (Simplified & Traditional), Japanese, Korean, Arabic, Hindi, Russian, Italian, Dutch, Turkish

---

## Screenshots

> Screenshots will be added as the UI is finalized. The project is currently backend-complete with frontend components ready for assembly into full pages.

<!--
![Map View](docs/screenshots/map.png)
![Incident Dashboard](docs/screenshots/dashboard.png)
![POD Heatmap](docs/screenshots/pod-heatmap.png)
![Team Status Board](docs/screenshots/teams.png)
-->

---

## Quick Start

### Prerequisites

- [Node.js](https://nodejs.org/) 22+
- [Python](https://www.python.org/) 3.12+
- [Docker](https://www.docker.com/) and Docker Compose
- [Git](https://git-scm.com/)

### Setup

```bash
# Clone the repository
git clone https://github.com/devclinton/searchparty.git
cd searchparty

# Start the database
make docker-up

# Set up the backend
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cd ..

# Run database migrations
make migrate

# Set up the frontend
cd frontend
npm install
cd ..

# Install pre-commit hooks
pre-commit install
```

### Running Locally

```bash
# Terminal 1: Start the backend API server
make dev-backend

# Terminal 2: Start the frontend dev server
make dev-frontend
```

The API will be available at `http://localhost:8000` and the frontend at `http://localhost:3000`.

### Running Tests

```bash
make test          # Run all tests
make lint          # Lint all code
make ci            # Full CI pipeline (lint + test)
```

---

## Architecture

```
Frontend (Next.js/React PWA)
  |
  |-- Capacitor (Android/iOS)
  |-- MapLibre GL (maps)
  |-- IndexedDB (offline store)
  |-- Service Worker (offline cache)
  |-- Meshtastic (mesh networking)
  |
  v
Backend (Python FastAPI)
  |
  |-- 16 API routers
  |-- Raw parameterized SQL (no ORM)
  |-- JWT authentication
  |-- ICS role-based access control
  |
  v
PostgreSQL + PostGIS
  |
  |-- 7 migrations
  |-- Spatial indexes for GPS/segments/hazards
```

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for a detailed overview.

---

## Project Status

| Component | Status |
|---|---|
| Backend API | Feature-complete (16 routers, 139 tests) |
| Database | 7 migrations, PostGIS spatial support |
| Frontend Components | Built, need page assembly and UI polish |
| PWA / Offline | Core infrastructure complete |
| Mobile (Capacitor) | Configured, native hooks built |
| Mesh Networking | Connection manager and dashboard built |
| Drone Integration | Patterns, exporters, SRT parser complete |
| Documentation | Architecture, deployment, security, contributing guides |
| Tests | 139 backend tests passing |
| i18n | 15 languages (English base, stubs for translation) |

### Known Limitations

- Translations are English stubs in non-English locales (community translations needed)
- Frontend pages need to be assembled from the built components
- No production deployment yet (Docker production compose pending)
- Apple Sign In OAuth not yet implemented (Google and GitHub work)
- Mesh networking requires physical Meshtastic hardware for testing
- Drone integration is export-only (no real-time telemetry ingestion yet)

---

## Contributing

We welcome contributions! SearchParty is a tool that helps save lives - every improvement matters.

See [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md) for setup instructions and guidelines.

### Ways to Help

- **Translations**: Help translate to the 15 supported languages
- **Frontend**: Build out pages from the existing components
- **Testing**: Test on mobile devices, report bugs
- **SAR Expertise**: Review features against real-world SAR operations
- **Drone Pilots**: Test flight plan exports with actual hardware
- **Documentation**: Improve user guides and tutorials

---

## Documentation

| Document | Description |
|---|---|
| [CONTRIBUTING.md](docs/CONTRIBUTING.md) | How to contribute |
| [ARCHITECTURE.md](docs/ARCHITECTURE.md) | System architecture overview |
| [DEPLOYMENT.md](docs/DEPLOYMENT.md) | Self-hosted deployment guide |
| [SECURITY.md](docs/SECURITY.md) | Security audit and considerations |
| [ACCESSIBILITY.md](docs/ACCESSIBILITY.md) | WCAG 2.1 AA accessibility checklist |
| [MOBILE_BUILD.md](docs/MOBILE_BUILD.md) | Mobile app build pipeline |
| [MESH_NETWORK_EXPLORATION.md](docs/MESH_NETWORK_EXPLORATION.md) | Meshtastic/goTenna research |
| [ROADMAP.md](docs/ROADMAP.md) | Full project roadmap |

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js, React, TypeScript, Tailwind CSS |
| Maps | MapLibre GL JS |
| Mobile | Capacitor (Android + iOS) |
| Backend | Python, FastAPI, asyncpg |
| Database | PostgreSQL + PostGIS |
| Offline | Service Workers, IndexedDB |
| Mesh | Meshtastic (LoRa) |
| CI | GitHub Actions |
| Linting | ruff (Python), ESLint + Prettier (TypeScript) |

---

## License

[MIT License](LICENSE) with SAR disclaimer.

This software is a coordination tool and does not replace trained search and rescue leadership. No medical or rescue advice is provided.

---

## Acknowledgments

- [Robert Koester](https://www.dbs-sar.com/) for Lost Person Behavior research
- [OpenStreetMap](https://www.openstreetmap.org/) contributors for map and trail data
- [OpenTopoMap](https://opentopomap.org/) for topographic tiles
- [Meshtastic](https://meshtastic.org/) for open-source mesh networking
- [MapLibre](https://maplibre.org/) for open-source map rendering
- The global search and rescue volunteer community
