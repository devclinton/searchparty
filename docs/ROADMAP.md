# SearchParty Roadmap

## Milestone 1: Project Foundation
Set up the development environment, CI/CD, and core project scaffolding.

- [ ] Initialize Next.js frontend with TypeScript strict mode
- [ ] Initialize FastAPI backend with project structure
- [ ] Set up Docker Compose for local PostgreSQL
- [ ] Create Makefile with standard commands (test, lint, format, migrate, seed, docker-up/down, ci)
- [ ] Set up GitHub Actions CI (test, lint, format, coverage)
- [ ] Set up pre-commit hooks (ruff, eslint, prettier)
- [ ] Set up i18n framework (frontend and backend) with 15 languages
- [ ] Create initial database migrations (users, incidents, teams tables)
- [ ] Set up PWA configuration (service worker, manifest)
- [ ] Add project documentation (contributing guide, dev setup)

## Milestone 2: Authentication & User Management
Basic user management with role-based access following ICS hierarchy.

- [ ] Implement user registration and login (email/password)
- [ ] Add OAuth provider support (Google, Apple, GitHub)
- [ ] Implement ICS role system (Incident Commander, Operations Chief, Division Supervisor, Team Leader, Searcher)
- [ ] Role-based API permissions middleware
- [ ] User profile management
- [ ] Implement JWT token handling with refresh tokens
- [ ] Add rate limiting on auth endpoints
- [ ] Write auth tests (unit + integration)
- [ ] Translate all auth-related user-facing text

## Milestone 3: Incident & Team Management
Core incident lifecycle and team organization.

- [ ] Create incident (search operation) with metadata (subject profile, IPP, date/time, terrain type)
- [ ] Incident status workflow (planning, active, suspended, closed)
- [ ] Team creation and member assignment within an incident
- [ ] Assignment dispatch — assign sectors/tasks to teams
- [ ] Team status board (deployed, returning, overdue, stood down)
- [ ] Check-in schedule system with configurable intervals (default 30 min)
- [ ] Overdue team alerts (visual + push notification)
- [ ] Digital accountability board (sign-in/sign-out tracking)
- [ ] Subject profile input (age category, activity, condition) for LPB modeling
- [ ] Incident data auto-purge after configurable retention period
- [ ] Tests for all incident/team endpoints
- [ ] Translate all incident/team user-facing text

## Milestone 4: Mapping & GPS Core
Map display with offline tile support and GPS tracking.

- [ ] Integrate map library (Leaflet or MapLibre GL) with OpenStreetMap tiles
- [ ] Topographic overlay with contour lines (USGS topo tiles)
- [ ] Offline tile storage and management (MBTiles/GeoPackage via IndexedDB)
- [ ] Tile pre-download for selected area before going to field
- [ ] GPS position tracking with breadcrumb trail recording
- [ ] GPS track storage (local + sync to server)
- [ ] Display team member positions on map (when online)
- [ ] Terrain classification overlays (forest, open, water, cliff)
- [ ] Elevation profile for selected routes/areas
- [ ] Compass and bearing tools
- [ ] Map coordinate display (lat/lon, UTM, MGRS)
- [ ] Tests for GPS and map data handling
- [ ] Translate map UI elements

## Milestone 5: Search Operations & POD
Search pattern tools and probability tracking.

- [ ] Search segment definition — draw polygons on map to define search areas
- [ ] Grid overlay generation with configurable spacing
- [ ] Track search progress per grid cell (searched/not searched)
- [ ] POD calculation per segment: POD = 1 - e^(-coverage)
- [ ] Cumulative POD tracking across multiple passes
- [ ] Effective Sweep Width (ESW) input based on terrain/visibility
- [ ] Search type selection per assignment (Hasty, Grid, Line, Attraction)
- [ ] Clue/evidence marking with GPS coordinates, photo, and notes
- [ ] Percent-area-covered calculations per segment and overall
- [ ] Visual POD heatmap overlay on map
- [ ] Tests for POD calculations and search operations
- [ ] Translate search operation UI text

## Milestone 6: Lost Person Behavior (LPB) Modeling
Statistical probability modeling based on Koester's research.

- [ ] Subject profile categories (child age groups, adult, elderly, hiker, hunter, dementia, despondent, etc.)
- [ ] Statistical distance database (25th, 50th, 75th, 95th percentile by category and terrain)
- [ ] Auto-generate probability rings from IPP based on subject profile
- [ ] Probability density overlay on map
- [ ] Travel behavior annotations (trail following, downhill tendency, shelter seeking, etc.)
- [ ] Integration with search segment priority — suggest high-priority search areas
- [ ] Terrain-adjusted probability (factor in barriers like rivers, cliffs, dense vegetation)
- [ ] Tests for LPB calculations
- [ ] Translate LPB UI text

## Milestone 7: Safety & Hazard Management
Searcher safety features and danger zone management.

- [ ] Hazard zone creation — mark dangerous areas on map (cliffs, mines, avalanche terrain, flood zones)
- [ ] Geofence alerts when searcher approaches flagged hazard
- [ ] Emergency/distress button — one-tap with last known coordinates
- [ ] Turnaround time enforcement (based on daylight, weather, fitness)
- [ ] Weather data integration (current conditions + forecast)
- [ ] Safety briefing checklist per team before deployment
- [ ] Incident safety officer role and dashboard
- [ ] Tests for geofencing and alert systems
- [ ] Translate safety UI text

## Milestone 8: Offline & Sync
Full offline-first architecture with reliable sync.

- [ ] Service worker for full PWA offline support
- [ ] IndexedDB local data store for all field-critical data
- [ ] Background sync when connectivity is restored
- [ ] Conflict resolution strategy (CRDT or operational transform for concurrent edits)
- [ ] Offline queue for actions taken without connectivity
- [ ] Sync status indicator (online/offline/syncing)
- [ ] Data export for offline handoff (USB/file transfer)
- [ ] Mesh network support exploration (Meshtastic/GoTenna)
- [ ] Tests for offline scenarios and sync conflict resolution
- [ ] Translate sync status UI text

## Milestone 9: Mobile Apps (Capacitor)
Native Android and iOS apps built from the PWA.

- [ ] Capacitor project setup and configuration
- [ ] Native GPS integration (background tracking)
- [ ] Native push notification support
- [ ] Native camera integration for clue photos
- [ ] Offline tile storage using native filesystem
- [ ] App store build and signing pipeline
- [ ] Battery optimization for extended field use
- [ ] Native compass integration
- [ ] Test on physical devices (Android + iOS)
- [ ] Translate mobile-specific UI text

## Milestone 10: Reporting & Analytics
Post-operation reporting and data analysis.

- [ ] Operation summary report generation (timeline, area covered, resources used)
- [ ] Export search data (GPX tracks, KML segments, CSV clue logs)
- [ ] POD summary by segment with visual map export
- [ ] Team performance metrics (area covered, time in field)
- [ ] Printable incident action plan (IAP) generation
- [ ] Historical operation archive and search
- [ ] Data visualization dashboards for operation review
- [ ] Tests for report generation
- [ ] Translate report UI text

## Milestone 11: Polish & Launch Preparation
Final hardening, accessibility, documentation, and launch.

- [ ] Accessibility audit (WCAG 2.1 AA compliance)
- [ ] Dark mode support
- [ ] Performance optimization and load testing
- [ ] Security audit (OWASP top 10)
- [ ] Complete translation review for all 15 languages
- [ ] User documentation and help system
- [ ] Deployment documentation (self-hosted guide)
- [ ] Legal disclaimers and terms of service
- [ ] Privacy policy with data retention details
- [ ] Landing page and project website
- [ ] Open source community setup (contributing guide, issue templates, code of conduct)
