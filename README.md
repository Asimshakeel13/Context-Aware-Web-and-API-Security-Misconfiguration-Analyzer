# CAWASMA — Context-Aware Web & API Security Misconfiguration Analyzer

Defensive, black-box, HTTPS-only security **misconfiguration** analyzer for web
applications and REST APIs. The backend exposes REST + WebSocket APIs for a
separate JavaScript frontend.

> **Scope & ethics.** CAWASMA performs only safe, non-destructive requests
> (primarily `GET`/`HEAD`/`OPTIONS`). It does not exploit, brute-force, or
> extract real data. Use only against systems you are authorized to test.

---

## Build status by phase

This repository is being built in phases (see the project spec). Current state:

- ✅ **Phase 1** — Architecture & requirements analysis
- ✅ **Phase 2** — Project setup: FastAPI skeleton, config, Docker, Celery, health endpoint
- ✅ **Phase 3** — Database: 10 SQLAlchemy models, relationships, cascades, Alembic migration (verified)
- ✅ **Phase 4** — REST API: scans/findings/endpoints/chains routes, pagination, error envelope
- ✅ **Phase 5** — Security foundation: URL validation, SSRF protection, redaction
- ✅ **Phase 6** — HTTP engine: async httpx, redirect + SSRF re-check, size caps, safe errors
- ✅ **Phase 7** — Crawler: 4 discovery strategies, same-origin + depth limits, dedup
- ✅ **Phase 8** — NLP endpoint classifier (Contribution 1): hybrid keyword + optional embeddings, explainable, model-optional
- ✅ **Phase 9** — Response body classifier (Contribution 3): credentials/PII/financial/internal-IP, redacted evidence
- ✅ **Phase 10** — 58 security checks across 7 categories, each with predefined CVSS v3.1 vector + honest limitations
- ✅ **Phase 11** — CVSS + CAWASMA context-aware scoring engine (base vs. final kept distinct)
- ✅ **Phase 12** — Attack-chain correlation (Contribution 2): 5 templates, fire only on real findings
- ✅ **Phase 13** — Scan pipeline: crawl → classify → probe → 58 checks → context-aware score → chains (database-free)
- ✅ **Phase 14** — Celery `run_scan` task + Redis progress publishing; `create_scan` dispatches to the worker
- ✅ **Phase 15** — WebSocket `/ws/scans/{id}`: DB snapshot + live progress forwarded from Redis
- ✅ **Phase 16** — Reports: JSON, CSV, HTML (Jinja2), PDF (WeasyPrint); all evidence pre-redacted
- ✅ **Phase 17** — Built-in executive insight (deterministic summary; no external LLM required)
- ✅ **Phase 18** — Full test suite: unit + API + end-to-end integration against a mock server
- ✅ **Phase 19** — Boot/route verification; Docker image + compose (api runs migrations, worker runs Celery)
- ✅ **Phase 20** — Consistency pass + documentation

**Tests:** 88 passing (`python -m pytest -q`). Pipeline, persistence, reports, scan-runner, TLS probe and classifier fallback all verified — the last two against live integration.

## Full stack: backend + frontend

The project ships a React (Vite) frontend in `frontend/`. `docker compose up --build`
now starts **five** services — db, redis, api, worker, and the frontend — so the whole
product runs with one command:

| Service   | URL                      | What it is                          |
|-----------|--------------------------|-------------------------------------|
| Frontend  | http://localhost:5173    | React dashboard (nginx-served build)|
| API       | http://localhost:8000    | FastAPI REST + WebSocket            |
| API docs  | http://localhost:8000/docs | Swagger UI                        |

```bash
cp .env.example .env
docker compose up --build        # db + redis + api + worker + frontend
# open http://localhost:5173
```

### Running without Docker

**Backend (two options):**

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Option A — with Celery + Redis (production-like):
#   run redis, then:  celery -A celery_worker.celery_app.celery_app worker &
# Option B — no Celery/Redis needed (sets scans to run in-process):
export RUN_SCANS_INLINE=true

alembic upgrade head
uvicorn app.main:app --reload            # http://localhost:8000
```

**Frontend:**

```bash
cd frontend
npm install
npm run dev                              # http://localhost:5173
```

The frontend reads the API base from `VITE_API_BASE` (default `http://localhost:8000`).
If the backend is unreachable it shows a clear banner and renders demo data so the UI
can still be demonstrated.

## Running a scan

1. Open the dashboard at http://localhost:5173 and click **New Scan**, or `POST /api/scans`
   with `{"target_url": "https://example.com"}` → returns a scan id (status `QUEUED`).
2. The UI shows live progress (WebSocket `ws://localhost:8000/ws/scans/{id}`); you can also
   poll `GET /api/scans/{id}/status`.
3. When `COMPLETED`, the UI shows findings (ranked by context-aware score), endpoints,
   attack chains, and report downloads — or read them directly:
   `GET /api/scans/{id}/findings`, `/endpoints`, `/chains`, and
   `GET /api/scans/{id}/report?format=json|csv|html|pdf`.

### Enabling the NLP embedding layer (optional)

The endpoint classifier works out of the box on its explainable keyword layer. To
also enable the semantic embedding layer, install the ML extras once:

```
pip install -r requirements-ml.txt
```

Without it, the classifier logs `embeddings unavailable, keyword-only` and keeps
working — so demos never depend on the model download.

### Enabling LLM URL-abbreviation expansion (optional)

The NLP classifier's first step expands URL abbreviations (`usr` → `user`,
`iam` → `identity access management`). By default this uses a built-in
abbreviation table. To have an LLM perform the expansion instead, set in `.env`:

```
LLM_ENABLED=true
LLM_PROVIDER=anthropic        # or openai
ANTHROPIC_API_KEY=sk-...      # or OPENAI_API_KEY for openai
# LLM_MODEL=                  # optional; blank uses a sensible default
```

If the LLM is disabled, has no key, or the API call fails, the classifier
silently falls back to the built-in table — the scan never breaks. Expansions
are cached per token, so repeated tokens across a scan cost nothing.

**Tests:** 47 passing (`pytest`) — validators, SSRF, redaction, engine, crawler, scan API.

---

## Architecture (process topology)

```
[JS Frontend] --REST--> FastAPI --enqueue--> Redis --> Celery worker
      ^  |                  ^                              |
      |  +----WebSocket-----+                              | runs scanner pipeline
      |                     |                              v
      +-- live progress <-- Redis pub/sub <-- publishes  PostgreSQL
```

The Celery worker runs in a **separate process** from FastAPI, so live scan
progress is delivered via a **Redis pub/sub bridge**: the worker publishes
events to `scan:{id}:events`; the FastAPI WebSocket endpoint subscribes and
forwards them to the browser.

## Tech stack

| Concern            | Choice                                  |
|--------------------|-----------------------------------------|
| API framework      | FastAPI + Uvicorn (async, auto docs)    |
| Validation/config  | Pydantic v2 / pydantic-settings         |
| Database           | PostgreSQL + SQLAlchemy (async, asyncpg)|
| Migrations         | Alembic                                 |
| Background tasks   | Celery + Redis                          |
| Live progress      | WebSocket + Redis pub/sub               |
| HTTP engine        | httpx (async)                           |
| NLP classifier     | sentence-transformers `all-MiniLM-L6-v2`|
| Response classifier| spaCy + regex                           |
| Reports            | JSON / CSV / HTML / PDF (WeasyPrint)     |

---

## Running with Docker (recommended)

```bash
cp .env.example .env          # adjust if needed
docker compose up --build
```

Then:

- API docs:   http://localhost:8000/docs
- Health:     http://localhost:8000/api/health

## Running locally (without Docker)

Requires local PostgreSQL and Redis, or expect `/api/health` to report
`degraded` (the endpoint degrades gracefully rather than crashing).

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# point DATABASE_URL / REDIS_URL at localhost in .env
python run.py
```

## Verifying Phase 2

```bash
source .venv/bin/activate
python -c "from fastapi.testclient import TestClient; from app.main import app; \
print(TestClient(app).get('/api/health').json())"
```

Expected: HTTP 200 with `status: ok` (all deps up) or `degraded` (db/redis down).

---

## Project layout

```
cawasma/
├── app/
│   ├── main.py            # FastAPI app factory, CORS, error envelope
│   ├── config.py          # Pydantic settings (single source of config)
│   ├── api/
│   │   ├── routes/        # health (+ scans/findings/reports/ws in later phases)
│   │   └── schemas/       # Pydantic request/response models
│   ├── database/          # base, async session (+ models in Phase 3)
│   ├── scanner/           # engine, crawler, checks, nlp, cvss, chains (later)
│   ├── services/          # persistence + orchestration (later)
│   ├── reports/           # json/csv/html/pdf generators (later)
│   └── utils/             # logging, security, redaction, validators
├── celery_worker/         # celery app + tasks
├── migrations/            # Alembic (Phase 3)
├── tests/                 # unit / integration / api / fixtures
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── run.py
```
