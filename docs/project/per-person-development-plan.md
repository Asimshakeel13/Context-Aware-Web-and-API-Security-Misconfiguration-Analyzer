# CAWASMA — Per-Person Development Plan (3 partners)

> Imported from the team PDF `CAWASMA — Per-Person Development Plan (3 partners).pdf` (local copy in `pdf/`, not committed). Converted to Markdown on 2026-10-25; tables and lists are kept, page headers dropped.

Oct 14, 2026 · @Shoaib Younas

A detailed, per-person build plan. **Atta Ur Rehman (A)** owns backend + scanner implementation + shared DevOps; **Neelam (B)** owns frontend + shared DevOps; **Asim (C)** owns security + ML/NLP + evaluation. Asim specifies the security logic and Atta codes it; Docker/CI is shared between Atta and Neelam. Each person's section has what they own, a task breakdown, a sprint-by-sprint plan, what to learn, their dependencies, and their definition of done. Each person's section is written to its owner as "you."

## Team split at a glance

| Partner | Role | Owns | Key skills used | Learns |
|---|---|---|---|---|
| Atta Ur Rehman (A) | Backend & scanner engine | engine.py, crawler.py, checks.py (implementation), cvss.py, FastAPI backend, Celery/async, DB + migrations, reports.py; half of Docker/CI | Python, FastAPI, async, SQL, DevOps | CVSS library, httpx async, WeasyPrint |
| Neelam (B) | Frontend & shared DevOps | Next.js dashboard (scan form, results, drill-down, history), API integration, export UI; half of Docker/CI | Next.js/React, TypeScript, DevOps | Polling patterns, chart/report display |
| Asim (C) | Security & ML/NLP & evaluation | Check specifications, CVSS environmental mapping, chain templates, sensitivity.py (NLP), body_classifier.py, ground-truth datasets, evaluation + baselines | Security domain, OWASP/CWE, CVSS, ZAP/Nuclei | Light Python (sentence-transformers, spaCy), DevOps (studying) |

**How the split works in practice:** Asim is the security brain and owns the ML/NLP, but doesn't carry the heavy integration Python. Asim specifies each check (the exact condition to test, the OWASP/CWE map, the base CVSS vector); Atta implements it. Asim builds the self-contained ML pieces (classifier, body scanner) where the Python is light and library-driven, and owns all evaluation (ground truth, ZAP/Nuclei baselines — tools, not code). Neelam builds the whole UI against an agreed API contract so she's never blocked waiting for the backend. Atta and Neelam split Docker/CI and pair on the Phase 0 setup.

## Shared contracts (agree these in Sprint 1)

Three people working in parallel only works if the interfaces between them are fixed early. Agree and write these down before anyone builds features — they are the seams along which the work divides.

### Contract 1 — Check specification (C → A)

C writes one spec per check; A implements it. Keep them in a `checks.yaml` or a table in the repo so both own one source of truth:

| Field | Example |
|---|---|
| check_id | HDR-HSTS-01 |
| category | Headers |
| detects | Missing Strict-Transport-Security header |
| condition | Response has no Strict-Transport-Security header |
| owasp / cwe | A02:2025 / CWE-319 |
| base_cvss | CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:L/I:N/A:N |
| severity notes | raise with endpoint sensitivity |

When C writes a new spec, A implements the function and its fire/no-fire test. No check is "done" without both.

### Contract 2 — FINDING schema (shared)

Everyone reads/writes findings, so freeze the shape early (it's the DB record from the data model): `id, endpoint_id, check_id, owasp_map, cwe_map, cvss_vector,` `base_score, final_score, severity_bucket, evidence`. A produces it, C's scoring fills the vector/score fields, B renders it.

### Contract 3 — API contract (A → B)

Freeze the endpoints and JSON response shapes in Sprint 1 so B builds the UI against a **mock** without waiting for the backend: `POST /api/scan`, `GET /api/results/{id}` (status + findings), `GET /api/results/{id}/export?format=...`. Write an example response JSON and commit it; B's dashboard consumes exactly that.

### Contract 4 — Classifier + signals interface (C → A's cvss.py)

C's `sensitivity.py` returns a class (Critical/High/Medium/Low) per endpoint; `body_classifier.py` returns signal flags. C designs the mapping class/signals → CVSS environmental metrics (CR/IR); A's `cvss.py` consumes the class + flags and applies that mapping. Agree the exact mapping table in Sprint 1 (it's the scoring spec).

### Contract 5 — Shared DevOps (A + B)

Atta and Neelam co-own `docker-compose.yml` and the CI workflow. Pair on Phase 0, then whoever touches a service keeps its compose entry current. C's evaluation targets live in a separate `docker-compose.eval.yml` that C maintains.

## Partner A — Atta Ur Rehman (Backend & scanner engine)

You are the critical path: most of the Python and the whole scan pipeline run through you. Everything else plugs into what you build, so your Sprint-1 and Sprint-2 work unblocks the team.

### What you own

`engine.py`, `crawler.py`, the **implementation** of `checks.py` (from C's specs), `cvss.py`, the FastAPI backend and routes, Celery/async orchestration, the PostgreSQL schema + SQLAlchemy models + Alembic migrations, `reports.py`, and half of Docker/CI.

### Task breakdown

**Database & models.** Define the 10 SQLAlchemy models from the data model; set up Alembic; write the first migration; a seed/reset script. This is the foundation B and C build on, so do it first.

**engine.py.** Async httpx client (HTTP/2), configurable concurrency + timeout, and the **SSRF guard** — validate the URL and block private/loopback/metadata addresses (169.254.169.254, localhost, RFC1918). Normalise a response object the rest of the pipeline consumes.

**crawler.py.** The 4 strategies (HTML links, JS-source regex, wordlist probe, recursive depth-2) with a visited-set; off-host links logged but not followed.

**checks.py.** Build a **check registry** (one function per check, auto-registered) so adding one is a one-file change. Implement each check from C's spec; reuse SSLyze for TLS and Observatory-style logic for headers. Each check ships with a fire/no-fire test.

**cvss.py.** Store a base CVSS vector per check (from C's specs); take C's sensitivity class + body signals and apply C's class → Security Requirement mapping via a CVSS library (don't re-implement the formula); output the full vector + 0–10 score + severity bucket. This is the project's technical heart — get the environmental maths right.

**FastAPI backend.** Routes per the API contract; dispatch scans to Celery (or BackgroundTasks); persist via SQLAlchemy; status transitions queued→running→done.

**reports.py.** JSON/CSV direct from the DB; HTML template; PDF via WeasyPrint.

### Your sprint-by-sprint

| Sprint | Your tasks |
|---|---|
| 1 | DB schema + models + Alembic; engine.py fetch + SSRF guard; crawler skeleton; agree API contract with B and check-spec format with C; pair with B on Docker/CI |
| 2 | Vertical slice: engine fetch → 1 check (HSTS, from C's spec) → call C's classifier → cvss.py env scoring (from C's mapping) → store finding → expose via GET /api/results |
| 3 | Implement the full frozen check set from C's specs (each with a test); integrate body_classifier + chains outputs into cvss.py ; results API complete |
| 4 | Celery/async + live status; reports.py export (PDF/JSON/HTML/CSV); passive-only + off-host guards |
| 5 | Support evaluation: fix false positives C finds in checks; performance tuning to hit the 10-min budget |
| 6 | Backend polish; verify reproducibility on a clean machine with B |

### What to learn

- A CVSS v3.1 library (so you don't hand-roll the formula) and the environmental metric group.
- httpx async patterns and WeasyPrint for PDF. All within reach for a backend dev.

### Your dependencies

- **You need from C:** check specs, the base CVSS vectors, and the class→CR/IR mapping (Sprint 1), plus `sensitivity.py` / `body_classifier.py` / `chains.py` outputs to call.
- **Others need from you:** the DB schema (everyone), the API contract + example JSON (B, Sprint 1), and the FINDING shape (C's scoring, B's rendering).

### Your definition of done

A scan runs end-to-end through your pipeline, every finding carries a valid recomputable CVSS vector, the API serves ranked results, and the backend comes up with one Docker command. Every check you implement has a passing fire/no-fire test.

## Partner B — Neelam (Frontend & shared DevOps)

B builds the whole user-facing product and co-owns the infra. The key move: build against the **API contract and a mock** from Sprint 1, so B is never idle waiting for the backend.

### What you own

The Next.js app — new-scan page, results page (ranked list + filters + finding drill-down), history page, export-download UI — plus half of Docker/CI (co-owned with A).

### Task breakdown

**New-scan page.** URL input, the **authorisation confirmation** (scan can't start without it), optional wordlist/crawl-depth settings. On submit → `POST /api/scan` → show queued status.

**Results page.** Poll `GET /api/results/{id}` for live status (queued→running→done). Render findings **ranked by context-adjusted severity**, with filters (severity, category) and colour-coded severity buckets. Each finding expands to a **drill-down** showing the CVSS vector, sensitivity class, response signals, and chain membership — this makes the scoring transparent (a graded requirement and the project's selling point, so make it clear).

**History page.** List past scans (timestamp, target); re-open restores stored results.

**Export UI.** Buttons to download the PDF/JSON/HTML/CSV from the export endpoint.

**Shared DevOps.** Pair with A on `docker-compose.yml` and the CI workflow in Phase 0; keep the `frontend` service entry current; help ensure one-command bring-up works on a clean machine.

### Your sprint-by-sprint

| Sprint | Your tasks |
|---|---|
| 1 | Next.js scaffold; agree the API contract with A; build the scan form + a results stub against a mock JSON; pair with A on Docker/CI |
| 2 | Wire the new-scan form and a basic results list to the real vertical-slice API |
| 3 | Full results page: ranked list, filters, the finding drill-down (score breakdown) |
| 4 | Live polling/status; history page; export-download UI |
| 5 | Usability polish; a view that presents the evaluation / before-vs-after ranking for the demo (help C show the numbers) |
| 6 | README + demo GIF (with the team); final UI polish; reproducibility check with A |

### What to learn

- A polling or lightweight real-time pattern for live scan status.
- Rendering a clear severity-ranked list and an expandable breakdown. All standard frontend work.

### Your dependencies

- **You need from A:** the API contract + example JSON (Sprint 1) and the running endpoints (Sprint 2+).
- **You need from C (indirectly, via the data):** the sensitivity class, signals, and chain info that appear in the drill-down — they arrive in the finding JSON, so no direct blocking.
- **Others need from you:** a working UI to demo the pipeline, and your half of a reliable one-command Docker setup.

### Your definition of done

A user can enter a URL, confirm authorisation, watch the scan run, read a severity-ranked report, expand any finding to see why it scored as it did, view history, and export — all against the real backend, brought up with one Docker command.

## Partner C — Asim (Security, ML/NLP & evaluation)

C is the security brain of the project and owns the parts that make CAWASMA novel and defensible — the scoring logic, the chains, and the evaluation that produces the jury's numbers. The Python here is light and library-driven; the heavy lifting is security knowledge and careful data work. Pair with A whenever Python glue is needed.

### What you own

Check **specifications**, the CVSS environmental mapping, the chain templates, `sensitivity.py` (NLP classifier), `body_classifier.py` (PII/secrets detection), the hand-labelled endpoint dataset, the ground-truth finding lists, and the full evaluation (precision/recall/FPR + ZAP/Nuclei baselines). You also maintain the vulnerable-target Docker file.

### Task breakdown

**Check specifications (biggest early task).** For each check in the frozen set, write the spec A implements (Contract 1): what it detects, the exact HTTP condition, the OWASP/API-Top-10/CWE mapping, and the base CVSS v3.1 vector. This is pure security knowledge and it's the gate on A's check work, so front-load it in Sprint 1.

**CVSS environmental mapping.** Design how sensitivity class and response signals map to CVSS environmental metrics (class → Confidentiality/Integrity Requirement; credential leak → CR High). A codes it in `cvss.py`; you own its correctness. This replaces the old out-of-model multiplier and is what makes the score defensible.

**Chain templates.** Define the five templates — which findings chain, why, and the composite score — each with a one-line justification (so they're not arbitrary). A codes the trigger logic; you supply the security reasoning.

**sensitivity.py (ML/NLP).** Load all-MiniLM-L6-v2 (sentence-transformers), define 4 class anchors, embed the endpoint path, cosine-similarity to the nearest anchor. The Python is short and library-driven — a good on-ramp. The real work is tuning the anchors and **hand-** **labelling 150–300 endpoint paths** to measure accuracy (+ confusion matrix).

**body_classifier.py.** spaCy + regex patterns to detect credentials, PII, financial data, internal IPs in response bodies. Again mostly pattern/domain work.

**Evaluation (your headline deliverable).** Stand up Juice Shop/DVWA/VAmPI/crAPI in Docker; write ground-truth finding lists; compute precision/recall/FPR; run ZAP and Nuclei as baselines on the same targets; produce the comparison tables and the before/after ranking experiment. These are security tools you already know — no heavy coding.

**Tool security review.** Check CAWASMA's own safety: SSRF guard works, passive-only holds, authorisation gate enforced, secrets not leaked. A natural fit for your background.

### Your sprint-by-sprint

| Sprint | Your tasks |
|---|---|
| 1 | Lit review; write the check specs (full set); design the CVSS environmental mapping and the 5 chain templates + justifications |
| 2 | Stand up vulnerable targets in Docker; write ground-truth lists; start hand-labelling endpoints; build sensitivity.py (pair with A on the Python) |
| 3 | Finish + measure the classifier (accuracy, confusion matrix); build body_classifier.py ; define chain-trigger logic for A; validate check outputs vs ground truth |
| 4 | Run evaluation on all targets; tool security review (SSRF, passive-only, auth gate) |
| 5 | Full precision/recall/FPR vs ZAP + Nuclei; before/after ranking experiment; tune anchors/patterns to cut false positives |
| 6 | Final results tables; security sign-off; help with the demo |

### What to learn

- **Light Python** for the ML pieces: how to load a sentence-transformer, encode text, and compute cosine similarity, plus basic spaCy/regex. These are ~10–20 line patterns — lean on A for setup, then it's mostly your domain tuning.
- The CVSS environmental metric group (plays to your security background).
- DevOps you're already studying helps with the vulnerable-target Docker file.

### Your dependencies

- **You need from A:** help wiring the ML scripts into the pipeline and the Python scaffolding for `sensitivity.py` / `body_classifier.py`; the FINDING shape to validate against.
- **Others need from you:** the check specs + base CVSS vectors + class→CR/IR mapping (A, Sprint 1 — this blocks A, so it's urgent); the classifier/body/chain outputs (A, Sprint 3); the evaluation numbers (the whole team, for the demo and report).

### Your definition of done

Every check has a spec and a ground-truth expectation; the classifier has a measured accuracy; the scoring mapping is designed and validated; chains are justified; and there's a precision/recall/FPR table comparing CAWASMA to ZAP and Nuclei, plus a before/after ranking result. Those numbers are what the project is judged on — they're yours.

## Sprint grid — who does what, when

Read each row as one 2-week sprint; each column is one person. The bolded Sprint 2 cells are the shared vertical slice — the one moment all three must sync.

| Sprint | A — Atta (Backend) | B — Neelam (Frontend) | C — Asim (Security & ML) |
|---|---|---|---|
| 1 | DB schema + models + Alembic; engine + SSRF guard; crawler skeleton; set API contract + Docker/CI | Next.js scaffold; build scan form + results stub on mock; Docker/CI with A | Check specs (full set); CVSS env mapping; 5 chain templates + justifications; lit review |
| 2 | Vertical slice: engine → 1 check → classify → env score → store → API | Wire scan form + basic results to the slice API | Vulnerable targets in Docker; ground-truth lists; start labelling; build sensitivity.py (with A) |
| 3 | Full check set from specs (+ tests); integrate body + chains into cvss; results API | Full results page: ranked list, filters, drill-down | Finish + measure classifier; body_classifier; chain-trigger logic; validate vs ground truth |
| 4 | Celery/async + status; reports export; passive + off-host guards | Live polling/status; history page; export UI | Run evaluation on all targets; tool security review |
| 5 | Fix false positives; performance tuning to 10-min budget | Usability polish; evaluation/before-after view for demo | Precision/recall/FPR vs ZAP + Nuclei; ranking experiment; tune |
| 6 | Backend polish; reproducibility check | README + demo GIF; final UI polish | Final results tables; security sign-off; demo support |

### The two moments the whole team must sync

1. **End of Sprint 1 — contracts frozen.** API contract, FINDING shape, check-spec format, and the CVSS mapping are all agreed and written down. Everything parallel depends on this.
2. **End of Sprint 2 — vertical slice works.** One URL produces one scored finding on the dashboard, with the eval harness live. If this slips, everything after it compresses — protect it.

### Load balance note

Atta (A) carries the most Python and sit on the critical path, so keep your Sprint 1–2 scope tight and resist adding checks before the slice works. C's Sprint-1 spec work is the hidden critical path — if the check specs and CVSS mapping are late, your Sprint-2/3 check work stalls. B is the most independent once the contract exists, so B can help with Docker/CI and demo prep when ahead.
