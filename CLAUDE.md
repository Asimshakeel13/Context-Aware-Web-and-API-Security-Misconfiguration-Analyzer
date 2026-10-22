# CAWASMA — Context-Aware Web & API Security Misconfiguration Analyzer

Final-year project. Defensive, black-box, HTTPS-only scanner for web apps and
REST APIs. The point is **prioritisation, not detection**: the same
misconfiguration is scored differently depending on where it occurs and what
the endpoint returns. Background and design are in `docs/` (start with
`docs/README.md`); `docs/06-scoring-model.md` and `docs/08-database-schema.md`
are the data and scoring references.

## Project goal: context-aware CVSS v3.1 scoring

1. Each of the 58 checks carries a fixed **CVSS v3.1 base vector** and base score
   (`backend/app/core/checks/catalog.py`). These are never invented per scan.
2. Each endpoint gets a **sensitivity class** (CRITICAL/HIGH/MEDIUM/LOW) from NLP
   over its URL path (`core/sensitivity.py`, optional LLM abbreviation expansion
   in `services/llm.py`).
3. Each response body is scanned for **sensitive-data signals**: credentials, PII,
   financial data, internal IPs (`core/body_classifier.py`, redacted evidence).
4. The base score is **recomputed through CVSS v3.1 environmental metrics**
   (CR/IR/AR security requirements and modified base metrics), driven by (2) and
   (3), giving the context-aware score and severity.
5. Findings are correlated into attack chains (`core/chains.py`), which are stored
   as separate records with their own composite score.

> **Current state vs goal:** `core/cvss.py` currently implements the simpler
> formula in `docs/06-scoring-model.md`:
> `min(10, base × context_multiplier + response_bonus)`. The environmental
> metric recomputation in (4) is **not implemented yet**. When it is, keep the
> official base score and the context-aware score in separate columns, as the
> `findings` table does today, and update docs/06 to match.

## Team

| Who | Area | Owns |
|-----|------|------|
| **Atta** | Backend & scanner engine | everything under `backend/` except `app/ml/` (see below) |
| **Neelam** | Frontend (Next.js) | `frontend/` and the `frontend` service in `docker-compose.yml` |
| **Asim** | Security specs, ML, evaluation | `backend/app/ml/`, `docker-compose.eval.yml`, check specs/CVSS vectors (reviewed with Atta) |

Atta's files:

- `backend/app/core/engine.py`: async httpx engine (limits, redirects, SSRF re-check per hop)
- `backend/app/core/crawler.py`: endpoint discovery (seed, HTML, JS, wordlist, recursive)
- `backend/app/core/checks/`: the 58 checks (a package; one module per category, plus `catalog.py`)
- `backend/app/core/cvss.py`: scoring
- `backend/app/core/reports.py`: JSON/CSV/HTML/PDF renderers (DB-free); data assembly in `services/report_service.py`
- FastAPI app: `backend/app/main.py`, `backend/app/api/`
- Celery: `backend/app/workers/`
- DB: `backend/app/db/` (models, session, seed), `backend/migrations/`

The current frontend in `frontend/` is a React + Vite SPA. Neelam's Next.js app
replaces it in the same compose slot.

## Layout

```
backend/app/
  core/      DB-free scanner logic: engine, crawler, checks/, cvss, reports,
             sensitivity + body classifiers, chains, tls, pipeline
  api/       routes/ + schemas/ (Pydantic). Never return ORM objects.
  db/        base, session, models/, seed.py
  workers/   celery_app.py, tasks.py (cawasma.run_scan)
  ml/        Protocols (interfaces.py) + stubs for Asim's classifiers
  services/  orchestration + persistence (scan_runner, result_service, ...)
  utils/     validators, security (SSRF), redaction, logging
backend/migrations/   Alembic
backend/tests/        unit/ integration/ api/ fixtures/
```

## Conventions

- Python 3.12. Every module starts with a docstring and `from __future__ import annotations`.
- **`core/` stays database-free.** A check is a pure function
  `detect(ctx: CheckContext) -> RawFinding | None` registered with `@rule`. It
  reads only from `CheckContext`. Adding a check means a catalog entry, the
  function, and a unit test. Keep the catalog count check (58) in sync.
- Configuration comes only from `app.config.settings`; never read `os.environ` elsewhere.
- Safety rules are not negotiable: HTTPS-only targets; SSRF guard on the
  *resolved IP* for every hop (`utils/security.py`); bounded requests. Only
  GET/HEAD/OPTIONS unless a check needs a safe, non-destructive alternative.
  `allow_private` is for tests and the eval harness only.
- Redact secrets (`utils/redaction.py`) before anything is logged, stored or reported.
  Cookies store metadata, never values.
- Schema changes go through Alembic (`alembic revision --autogenerate`); never
  create tables by hand. Models must stay portable (SQLite tests, Postgres prod).
- ML code plugs in through `app/ml/interfaces.py`; the engine must keep working
  with the built-in classifiers when ML deps are absent.
- API errors use the envelope `{"success": false, "error": {"code", "message"}}`.
- Lint: ruff (config in `backend/pyproject.toml`, line length 100). Types: mypy must pass.
  Use a narrow `# noqa: <code> - reason` rather than disabling rules broadly.

## Commands

From the repo root:

```bash
make up        # build + start api, worker, postgres, redis; waits for healthchecks
make down      # stop (keeps DB volume)
make test      # pytest on the host (SQLite)
make lint      # ruff + mypy
make migrate   # alembic upgrade head in the api container
make seed      # idempotent demo scan
make reset     # wipe DB volume, up, migrate, seed
make install   # pip install -e "backend[dev]" into .venv
```

- Health: `curl localhost:8000/health` (also `/api/health`); Swagger at `/docs`.
- Tests against Postgres (as CI does):
  `TEST_DATABASE_URL=postgresql+asyncpg://cawasma:cawasma@localhost:5446/cawasma_test make test`
  (create the `cawasma_test` database first).
- Single test: `cd backend && ../.venv/bin/python -m pytest tests/unit/test_cvss.py -q`
- Faster image without the NLP stack: `INSTALL_ML=false make up`.
- Frontend: `docker compose --profile frontend up -d --build`.
- Eval targets: `docker compose -f docker-compose.eval.yml up -d` (isolated `cawasma-eval` network).

CI (`.github/workflows/ci.yml`) runs ruff, mypy, Alembic upgrade/downgrade, and
pytest against a Postgres 16 service container.
