# CAWASMA — Atta Ur Rehman

> Imported from the team PDF `CAWASMA_plan_atta.pdf` (local copy in `pdf/`, not committed). Converted to Markdown on 2026-10-25; tables and lists are kept, page headers dropped.

Backend & scanner engine (+ shared DevOps) Per-Person Development Plan · 22 October 2026 · Shoaib Younas

## Your place in the team

| Partner | Role | Owns |
|---|---|---|
| Atta Ur Rehman (A) | Backend & scanner engine | engine, crawler, checks (implementation), cvss, FastAPI, Celery/async, DB; half of Docker/CI |
| Neelam (B) | Frontend & shared DevOps | Next.js dashboard, API integration, export UI; half of Docker/CI |
| Asim (C) | Security & ML/NLP & evaluation | Check specs, CVSS mapping, chain templates, NLP classifier, body classifier, evaluation |

Asim specifies the security logic and Atta codes it; Docker/CI is shared between Atta and Neelam. Three people work in parallel only if the interfaces between them are fixed early — agree the contracts below in Sprint 1. **How scoring works (one line).** Final severity = the check's base CVSS v3.1 vector recomputed through the environmental metrics, where the NLP-derived endpoint sensitivity class and response-body signals raise the Confidentiality/Integrity Requirement — one standards-valid 0–10 score that reflects what is exposed and where. This is the context-aware scoring Burp/ZAP/Nikto lack.

## Shared contracts (agree in Sprint 1)

1. **Check specification (Asim → Atta).** One spec per check in a `checks.yaml`: `check_id`, category, what it detects, the exact HTTP condition, OWASP/CWE map, base CVSS v3.1 vector. Asim writes it; Atta implements the function + its fire/no-fire test.
2. **FINDING schema (shared).** `id, endpoint_id, check_id, owasp_map, cwe_map, cvss_vector, base_score, final_score, severity_bucket,` `evidence`. Atta produces it, Asim's scoring fills the vector/score, Neelam renders it.
3. **API contract (Atta → Neelam).** Freeze endpoints + example JSON in Sprint 1 so Neelam builds against a mock: `POST /api/scan`, `GET /api/results/{id}`, `GET /api/results/{id}/export?format=...`.
4. **Classifier + signals (Asim → cvss).** `sensitivity.py` returns a class; `body_classifier.py` returns signal flags. Asim designs the class/signals → CVSS environmental (CR/IR) mapping; Atta's `cvss.py` applies it.
5. **Shared DevOps (Atta + Neelam).** Co-own `docker-compose.yml` and CI; pair on Phase 0. Asim's evaluation targets live in a separate `docker-compose.eval.yml`.

## Your plan — Backend & scanner engine

You are the critical path: most of the Python and the whole scan pipeline run through you. Everything else plugs into what you build, so your Sprint-1 and Sprint-2 work unblocks the team.

### What you own

`engine.py`, `crawler.py`, the **implementation** of `checks.py` (from Asim's specs), `cvss.py`, the FastAPI backend and routes, Celery/async orchestration, the PostgreSQL schema + SQLAlchemy models + Alembic migrations, `reports.py`, and half of Docker/CI.

### Task breakdown

- **Database & models.** 10 SQLAlchemy models from the data model; Alembic; first migration; a seed/reset script. Do this first — Neelam and Asim build on it.
- **engine.py.** Async httpx (HTTP/2), configurable concurrency + timeout, and the **SSRF guard** (block private/loopback/metadata addresses). Normalise the response object the pipeline consumes.
- **crawler.py.** The 4 strategies (HTML links, JS-source regex, wordlist probe, recursive depth-2) with a visited-set; off-host links logged, not followed.
- **checks.py.** A **check registry** (one function per check, auto-registered) so adding one is a one-file change. Implement each from Asim's spec; reuse SSLyze for TLS and Observatory-style logic for headers. Each check ships with a fire/no-fire test.
- **cvss.py (the technical heart).** Base CVSS vector per check; take Asim's class + signals and apply the class → Security Requirement mapping via a CVSS library (don't re-implement the formula); output the full vector + 0–10 score + bucket.
- **FastAPI backend.** Routes per the API contract; dispatch scans to Celery (or BackgroundTasks); persist via SQLAlchemy; status queued→running→done.
- **reports.py.** JSON/CSV direct from the DB; HTML template; PDF via WeasyPrint.

### Your sprint-by-sprint

| Sprint | Your tasks |
|---|---|
| 1 | DB schema + models + Alembic; engine + SSRF guard; crawler skeleton; agree API contract (Neelam) + check-spec format (Asim); pair on Docker/CI |
| 2 | Vertical slice: engine → 1 check (HSTS) → classify → env score → store → GET /api/results |
| 3 | Full check set from specs (+ tests); integrate body + chains into cvss; results API complete |
| 4 | Celery/async + live status; reports export (PDF/JSON/HTML/CSV); passive + off-host guards |
| 5 | Fix false positives Asim finds; performance tuning to the 10-min budget |
| 6 | Backend polish; reproducibility check on a clean machine with Neelam |

### What to learn

A CVSS v3.1 library and the environmental metric group; httpx async patterns; WeasyPrint. All within reach for a backend dev.

### Your dependencies

- **You need from Asim:** check specs, base CVSS vectors, the class→CR/IR mapping (Sprint 1), and the classifier/body/chains outputs to call.
- **Others need from you:** the DB schema (everyone), the API contract + example JSON (Neelam, Sprint 1), the FINDING shape.

### Your definition of done

A scan runs end-to-end through your pipeline, every finding carries a valid recomputable CVSS vector, the API serves ranked results, and the backend comes up with one Docker command. Every check you implement has a passing fire/no-fire test.

## The two moments the whole team must sync

1. **End of Sprint 1 — contracts frozen.** API contract, FINDING shape, check-spec format, and the CVSS mapping all agreed and written down.
2. **End of Sprint 2 — vertical slice works.** One URL produces one scored finding on the dashboard, with the eval harness live. If this slips, everything after compresses — protect it.
