.PHONY: help test test-backend test-frontend lint lint-backend lint-frontend format format-backend format-frontend migrate seed docker-up docker-down ci dev-backend dev-frontend

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# Docker
docker-up: ## Start local Docker environment
	docker compose up -d

docker-down: ## Stop local Docker environment
	docker compose down

docker-reset: ## Reset Docker volumes and restart
	docker compose down -v
	docker compose up -d

# Backend
dev-backend: ## Start backend dev server
	cd backend && source .venv/bin/activate && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

test-backend: ## Run backend tests
	cd backend && source .venv/bin/activate && pytest tests/ -v --cov=app --cov-report=term-missing

lint-backend: ## Lint backend code
	cd backend && source .venv/bin/activate && ruff check app/ tests/

format-backend: ## Format backend code
	cd backend && source .venv/bin/activate && ruff format app/ tests/ && ruff check --fix app/ tests/

# Frontend
dev-frontend: ## Start frontend dev server
	cd frontend && npm run dev

test-frontend: ## Run frontend tests
	cd frontend && npm test

lint-frontend: ## Lint frontend code
	cd frontend && npx eslint src/

format-frontend: ## Format frontend code
	cd frontend && npx prettier --write "src/**/*.{ts,tsx,js,jsx,css,json}"

# Combined
test: test-backend test-frontend ## Run all tests

lint: lint-backend lint-frontend ## Lint all code

format: format-backend format-frontend ## Format all code

# Database
migrate: ## Run database migrations
	cd backend && source .venv/bin/activate && python -m app.db.migrate

seed: ## Generate seed data for local testing
	cd backend && source .venv/bin/activate && python -m app.db.seed

# CI
ci: lint test ## Run full CI pipeline locally
