# SearchParty - Claude Code Guidelines

## Project Overview
An open-source search and rescue (SAR) coordination tool for organizing searches in remote places. Combines offline mapping, real-time team tracking, probability modeling (Lost Person Behavior), Probability of Detection (POD) calculations, and ICS-structured team coordination in one package.

## Architecture
- **Frontend**: Next.js / React (PWA with offline support)
- **Mobile**: Capacitor for Android and iOS native apps
- **Backend**: Python FastAPI (no ORM - raw parameterized SQL for performance)
- **Database**: PostgreSQL (migrations only, optimize for minimal storage)
- **Local Dev**: Docker Compose for Postgres and services
- **Offline**: Service workers + IndexedDB for offline-first field operation, sync on reconnect

## Core Domain Concepts
- **ICS (Incident Command System)**: Role hierarchy used as the permission model — Incident Commander > Operations Chief > Division Supervisors > Team Leaders > Searchers
- **POD (Probability of Detection)**: POD = 1 - e^(-coverage) per grid cell, tracked cumulatively across passes
- **LPB (Lost Person Behavior)**: Statistical travel distance rings (25th/50th/75th/95th percentile) from Initial Planning Point based on subject profile
- **Search Types**: Hasty (Type I), Grid/Sweep (Type II), Line (Type III), Attraction/Sound
- **ESW (Effective Sweep Width)**: Metric for search thoroughness based on terrain and visibility

## Development Rules
- Every feature/fix MUST have a GitHub issue. Comment what was done and close when complete.
- All new features require tests, including security and edge case coverage.
- All user-facing text must be translatable (i18n for 15 languages).
- All DB changes happen through migrations (never modify schema directly).
- Develop documentation as you go — include operational considerations.
- Use the Makefile for all common tasks (test, lint, format, migrate, seed, etc).
- Commit often referencing the issue you are completing/working on.
- Do not mention Claude or AI tooling in commit messages.

## Code Style & Quality
- **Python**: Follow PEP 8. Use `ruff` for linting and formatting.
- **TypeScript/React**: Use ESLint + Prettier. Strict TypeScript.
- **Pre-commit hooks**: Linting and formatting run on commit via GitHub hooks.
- **CI**: GitHub Actions for testing, coverage, linting, and formatting.

## Common Commands
```bash
make test          # Run all tests
make lint          # Lint all code
make format        # Format all code
make migrate       # Run DB migrations
make seed          # Generate seed data for local testing
make docker-up     # Start local Docker environment
make docker-down   # Stop local Docker environment
make ci            # Run full CI pipeline locally
```

## Project Structure (Target)
```
searchparty/
  frontend/             # Next.js PWA app
    src/
      components/       # React components
      pages/            # Next.js pages/routes
      lib/              # Shared utilities
      i18n/             # Translation files (15 languages)
      styles/           # Global styles + dark mode
      maps/             # Map rendering, tile management, offline tiles
      hooks/            # React hooks (GPS, offline state, sync)
  mobile/               # Capacitor config for Android/iOS
  backend/
    app/
      api/              # FastAPI route handlers
      models/           # Pydantic models (request/response)
      db/               # Database queries, migrations, connection
      services/         # Business logic
      search/           # Search patterns, POD calculations, LPB modeling
      auth/             # Authentication
      incidents/        # Incident/operation management
      teams/            # Team and personnel management
    tests/              # pytest tests
  docs/                 # Project documentation
  docker/               # Docker and compose files
  Makefile
  CLAUDE.md
```

## Key Design Decisions
- **Offline-first**: All field-critical features must work without connectivity — map viewing, GPS tracking, team assignments, check-in logging, clue marking. Sync via opportunistic connectivity.
- **No ORM**: All database access uses raw parameterized SQL for performance.
- **ICS as permission model**: Role-based views — IC sees all teams, team leaders see their assignment, searchers see their track.
- **Map data**: Support MBTiles/GeoPackage for offline tiles. Sources include OpenStreetMap, USGS topo, SRTM elevation data.
- **Conflict resolution**: CRDTs or last-writer-wins with merge strategy for concurrent offline edits.

## Security Considerations
- Parameterized queries only (no string interpolation in SQL).
- Subject data (name, photo, medical conditions) is sensitive — encrypt at rest, role-based access.
- Auto-purge policy after case closure for subject personal data.
- GPS tracks may be discoverable in litigation — document retention policy.
- Rate limiting on all public endpoints.
- Input validation on all user-submitted data.

## Safety & Legal
- Prominent disclaimer: tool aids coordination, does not replace trained SAR leadership.
- No medical or rescue advice provided by the tool.
- Comply with relevant data privacy laws (HIPAA if medical info stored, GDPR, state privacy laws).

## Supported Languages (15)
English, Spanish, French, German, Portuguese, Chinese (Simplified), Chinese (Traditional), Japanese, Korean, Arabic, Hindi, Russian, Italian, Dutch, Turkish
