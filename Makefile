# CAWASMA developer commands. Run from the repo root.
#   make up | down | test | lint | migrate | seed | reset

COMPOSE ?= docker compose
# Host-side Python for test/lint; defaults to the repo venv when present.
PYTHON ?= $(if $(wildcard .venv/bin/python),$(CURDIR)/.venv/bin/python,python3)
BACKEND := backend

.DEFAULT_GOAL := help
.PHONY: help up down test lint typecheck migrate seed reset logs install env \
	validate-checks validate-config openapi

help: ## List targets
	@grep -E '^[a-z-]+:.*## ' $(MAKEFILE_LIST) | awk -F':.*## ' '{printf "  %-10s %s\n", $$1, $$2}'

env:
	@test -f .env || (cp .env.example .env && echo "created .env from .env.example")

up: env ## Build and start api, worker, postgres, redis (waits until healthy)
	$(COMPOSE) up -d --build --wait
	@echo "API: http://localhost:$${API_HOST_PORT:-8000}/health  docs: /docs"

down: ## Stop the stack (keeps the database volume)
	$(COMPOSE) down

logs: ## Follow logs of all services
	$(COMPOSE) logs -f

install: ## Install backend + dev tools into $(PYTHON)'s environment
	"$(PYTHON)" -m pip install -e "$(BACKEND)[dev]"

test: ## Run the test suite on the host (SQLite; set TEST_DATABASE_URL for Postgres)
	cd $(BACKEND) && "$(PYTHON)" -m pytest -q

lint: ## ruff + mypy
	cd $(BACKEND) && "$(PYTHON)" -m ruff check . && "$(PYTHON)" -m mypy

validate-checks: ## Validate config/checks.yaml (specs + CVSS vectors)
	cd $(BACKEND) && "$(PYTHON)" scripts/validate_specs.py checks

validate-config: ## Validate checks, cvss_mapping and chains YAML; report catalog score drift
	cd $(BACKEND) && "$(PYTHON)" scripts/validate_specs.py all

openapi: ## Regenerate docs/openapi.json from the code (commit the result)
	cd $(BACKEND) && "$(PYTHON)" scripts/export_openapi.py

typecheck: ## mypy only
	cd $(BACKEND) && "$(PYTHON)" -m mypy

migrate: ## Apply Alembic migrations inside the api container
	$(COMPOSE) run --rm --no-deps api alembic upgrade head

seed: ## Insert sample data: 1 target, 2 scans, 10 endpoints, 16 findings (idempotent)
	$(COMPOSE) run --rm --no-deps api python scripts/seed.py

reset: ## Drop everything in the database, re-run migrations, seed (ALL DATA LOST)
	$(COMPOSE) run --rm --no-deps api python scripts/reset.py --yes --seed
