# 03 — Installation & Running

> A fuller, Roman-Urdu walkthrough (with troubleshooting) lives in
> [`../HOW-TO-RUN.md`](../HOW-TO-RUN.md). This file is the concise reference.

## Requirements

- **Docker path:** Docker Desktop (with WSL2 integration on Windows).
- **Manual path:** Python 3.11+, Node.js 18+, and optionally PostgreSQL + Redis.

## Option A — Docker (recommended, one command)

```bash
cd cawasma
cp .env.example .env
docker compose up --build        # db + redis + api + worker + frontend
```

| Service | URL |
|---------|-----|
| Frontend (UI) | http://localhost:5173 |
| API docs (Swagger) | http://localhost:8000/docs |
| Health | http://localhost:8000/api/health |

Stop: `Ctrl+C`, then `docker compose down` (add `-v` to wipe the database).

## Option B — Manual, no infrastructure (SQLite + inline)

The lightest way to run everything on a laptop — no PostgreSQL, Redis or Celery.

**Backend:**
```bash
cd cawasma
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt aiosqlite
export DATABASE_URL="sqlite+aiosqlite:///./cawasma.db"
export ALEMBIC_SQLALCHEMY_URL="sqlite:///./cawasma.db"
export RUN_SCANS_INLINE=true
alembic upgrade head
uvicorn app.main:app --reload            # http://localhost:8000
```
> Windows PowerShell: use `$env:NAME="value"` instead of `export NAME=value`.

**Frontend:**
```bash
cd frontend
npm install
npm run dev                              # http://localhost:5173
```

## Option C — Manual, production-like (Postgres + Redis + Celery)

```bash
cp .env.example .env            # point DATABASE_URL / REDIS_URL at your services
alembic upgrade head
uvicorn app.main:app --reload                                   # terminal 1
celery -A celery_worker.celery_app.celery_app worker --loglevel=info   # terminal 2
cd frontend && npm install && npm run dev                        # terminal 3
```

## Configuration (`.env`)

Key settings (full list in `app/config.py`, sample in `.env.example`):

| Variable | Purpose | Default |
|----------|---------|---------|
| `DATABASE_URL` | async DB URL | postgres (docker) |
| `REDIS_URL` | broker + pub/sub | `redis://redis:6379/0` |
| `FRONTEND_ORIGIN` | CORS allow-list (never `*`) | `http://localhost:5173` |
| `RUN_SCANS_INLINE` | run scans in-process (no Celery) | `false` |
| `REQUEST_TIMEOUT`, `MAX_RESPONSE_SIZE`, `MAX_ENDPOINTS`, `MAX_CRAWL_DEPTH`, `MAX_REDIRECTS`, `MAX_CONCURRENT_REQUESTS` | safety limits | see file |
| `LLM_ENABLED`, `LLM_PROVIDER`, `OPENAI_API_KEY`, `ANTHROPIC_API_KEY` | optional LLM for URL expansion | off |

Optional AI keys are **never required** for the core scanner to run.

## Optional: NLP embedding layer

```bash
pip install -r requirements-ml.txt     # ~200 MB, one time
```
Without it the classifier logs `embeddings unavailable, keyword-only` and still
works.

## Running the tests

```bash
source .venv/bin/activate
pip install pytest pytest-asyncio aiosqlite greenlet
python -m pytest -q          # expected: 88 passed
```

## Database migrations (Alembic)

```bash
alembic upgrade head                                   # apply
alembic revision --autogenerate -m "describe change"   # create a new migration
alembic downgrade -1                                   # roll back one
```
