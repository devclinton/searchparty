# Contributing to SearchParty

Thank you for your interest in contributing to SearchParty! This guide will help you get started.

## Code of Conduct

Be respectful and constructive. SearchParty is a tool that helps save lives — collaboration matters.

## Getting Started

### Prerequisites

- Node.js 22+
- Python 3.12+
- Docker and Docker Compose
- Git

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/devclinton/searchparty.git
   cd searchparty
   ```

2. Start the database:
   ```bash
   make docker-up
   ```

3. Set up the backend:
   ```bash
   cd backend
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -e ".[dev]"
   ```

4. Run migrations:
   ```bash
   make migrate
   ```

5. Set up the frontend:
   ```bash
   cd frontend
   npm install
   ```

6. Install pre-commit hooks:
   ```bash
   pre-commit install
   ```

### Running Locally

```bash
# Terminal 1: Backend
make dev-backend

# Terminal 2: Frontend
make dev-frontend
```

## Development Workflow

1. **Find or create an issue** — Every change needs a GitHub issue.
2. **Create a branch** — Branch from `main` with a descriptive name (e.g., `feature/team-check-in`, `fix/gps-tracking-drift`).
3. **Write code and tests** — All new features require tests. All user-facing text must use the i18n framework.
4. **Run CI locally** — `make ci` runs lint and tests.
5. **Open a PR** — Reference the issue number. Keep PRs focused and reviewable.
6. **Address review feedback** — Push additional commits, don't force-push.

## Code Standards

### Python (Backend)
- Follow PEP 8. Enforced by `ruff`.
- No ORM — use raw parameterized SQL via `asyncpg`.
- All SQL must use parameterized queries (no string interpolation).
- Run `make lint-backend` and `make format-backend`.

### TypeScript (Frontend)
- Strict TypeScript mode enabled.
- ESLint + Prettier enforced.
- Run `make lint-frontend` and `make format-frontend`.

### Database
- All schema changes go through migration files in `backend/app/db/migrations/`.
- Never modify the database schema directly.
- Name migrations: `NNN_description.sql` (e.g., `002_add_search_segments.sql`).

### Internationalization
- All user-facing text must be translatable.
- Frontend: Use `next-intl` with messages in `frontend/src/i18n/messages/`.
- Backend: Use the `t()` function from `app.i18n` with messages in `backend/app/i18n/messages/`.
- 15 supported languages — add keys to `en.json` first, then copy to other locale files.

## Useful Commands

```bash
make help           # Show all available commands
make test           # Run all tests
make lint           # Lint all code
make format         # Format all code
make migrate        # Run database migrations
make seed           # Insert seed data
make docker-up      # Start Docker services
make docker-down    # Stop Docker services
make ci             # Run full CI pipeline locally
```
