# CAWASMA — Neelam

> Imported from the team PDF `CAWASMA_plan_neelam.pdf` (local copy in `pdf/`, not committed). Converted to Markdown on 2026-10-25; tables and lists are kept, page headers dropped.

Frontend (+ shared DevOps) Per-Person Development Plan · 22 October 2026 · Shoaib Younas

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

## Your plan — Frontend & shared DevOps

You build the whole user-facing product and co-own the infra. The key move: build against the **API contract and a mock** from Sprint 1, so you're never idle waiting for the backend.

### What you own

The Next.js app — new-scan page, results page (ranked list + filters + finding drill-down), history page, export-download UI — plus half of Docker/CI (co-owned with Atta).

### Task breakdown

- **New-scan page.** URL input, the **authorisation confirmation** (scan can't start without it), optional wordlist/crawl-depth settings. On submit → `POST /api/scan` → show queued status.
- **Results page.** Poll `GET /api/results/{id}` for live status. Render findings **ranked by context-adjusted severity**, with filters (severity, category) and colour-coded buckets. Each finding expands to a **drill-down** showing the CVSS vector, sensitivity class, response signals, and chain membership — this makes the scoring transparent (the project's selling point, so make it clear).
- **History page.** List past scans (timestamp, target); re-open restores stored results.
- **Export UI.** Buttons to download PDF/JSON/HTML/CSV from the export endpoint.
- **Shared DevOps.** Pair with Atta on `docker-compose.yml` and CI in Phase 0; keep the `frontend` service entry current; ensure one-command bring-up works on a clean machine.

### Your sprint-by-sprint

| Sprint | Your tasks |
|---|---|
| 1 | Next.js scaffold; agree the API contract with Atta; build the scan form + results stub against a mock JSON; pair on Docker/CI |
| 2 | Wire the new-scan form and a basic results list to the real vertical-slice API |
| 3 | Full results page: ranked list, filters, the finding drill-down (score breakdown) |
| 4 | Live polling/status; history page; export-download UI |
| 5 | Usability polish; a view that presents the evaluation / before-vs-after ranking for the demo (help Asim show the numbers) |
| 6 | README + demo GIF (with the team); final UI polish; reproducibility check with Atta |

### What to learn

A polling or lightweight real-time pattern for live scan status; rendering a clear severity-ranked list and an expandable breakdown. All standard frontend work.

### Your dependencies

- **You need from Atta:** the API contract + example JSON (Sprint 1) and the running endpoints (Sprint 2+).
- **From Asim (via the data):** the sensitivity class, signals, and chain info shown in the drill-down — they arrive in the finding JSON, so no direct blocking.
- **Others need from you:** a working UI to demo the pipeline, and your half of a reliable one-command Docker setup.

### Your definition of done

A user can enter a URL, confirm authorisation, watch the scan run, read a severity-ranked report, expand any finding to see why it scored as it did, view history, and export — all against the real backend, brought up with one Docker command.

## The two moments the whole team must sync

1. **End of Sprint 1 — contracts frozen.** API contract, FINDING shape, check-spec format, and the CVSS mapping all agreed and written down.
2. **End of Sprint 2 — vertical slice works.** One URL produces one scored finding on the dashboard, with the eval harness live. If this slips, everything after compresses — protect it.
