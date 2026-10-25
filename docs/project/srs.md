# CAWASMA — Software Requirements Specification

> Imported from the team PDF `CAWASMA — Software Requirements Specification.pdf` (local copy in `pdf/`, not committed). Converted to Markdown on 2026-10-25; tables and lists are kept, page headers dropped.

Oct 14, 2026 · @Shoaib Younas

Context-Aware Web and API Security Misconfiguration Analyzer. Black-box HTTPS scanner for web apps and REST APIs, BS-CS Final Year Project, FAST-NUCES. This SRS reflects the revised scoring and scope decisions (CVSS v3.1 environmental scoring; best-effort labelling of auth-dependent checks).

## 1. Introduction

### 1.1 Purpose

This document specifies the requirements for CAWASMA, a black-box security misconfiguration scanner that produces context-aware, CVSS-anchored severity for web applications and REST APIs. It is the agreed basis for design, implementation, and evaluation of the FYP.

### 1.2 Product scope

CAWASMA takes an authorised HTTPS target, discovers its endpoints, runs a defined set of misconfiguration checks, infers each endpoint's sensitivity and what its responses expose, correlates findings into known exploit chains, and scores each finding as a valid CVSS v3.1 environmental vector. Results are stored, shown on a dashboard ranked by context-adjusted severity, and exportable. The goal is to replace flat, context-blind finding lists with a prioritised report where the score reflects real-world risk.

### 1.3 Definitions and acronyms

- **Black-box:** testing with no source access, no agent, no prior configuration — only the target URL.
- **CVSS v3.1:** Common Vulnerability Scoring System; a finding's severity is expressed as a vector string that recomputes to a 0–10 score.
- **Environmental metrics:** the CVSS metric group (Confidentiality/Integrity/Availability Requirement and modified base metrics) that lets a consumer adjust severity for their own context. CAWASMA encodes endpoint sensitivity and response signals here.
- **Sensitivity class:** Critical / High / Medium / Low, inferred per endpoint from its URL semantics.
- **Attack chain:** a set of findings that together enable an exploit path greater than any one of them.
- **FR / NFR:** functional / non-functional requirement.
- **OWASP API Top 10 / CWE:** reference taxonomies each check maps to.
- **FP / FPR:** false positive / false-positive rate.

### 1.4 References

- OWASP Top 10 (2025) — A02 Security Misconfiguration.
- OWASP API Security Top 10 (2023).
- FIRST CVSS v3.1 specification (environmental metric group).
- Wunder et al., Shedding Light on CVSS Scoring Inconsistencies, IEEE S&P 2024.
- Golmohammadi, Zhang, Arcuri, Testing RESTful APIs: A Survey, ACM TOSEM 2023.
- Ahmadi Mehri et al., ACVRM, Electronics 2022.
- Evaluation targets: OWASP Juice Shop, DVWA, VAmPI, crAPI.

### 1.5 Overview

Section 2 gives the overall description (perspective, functions, users, constraints). Sections 3–5 specify functional, non-functional, and interface requirements. Section 6 gives use cases and user stories; Section 7 the objective-to-requirement-to-test traceability matrix.

### 1.6 Measurable objectives

1. Detect the defined misconfigurations black-box at **≥ 80% recall** with **≤ 15% FPR** on the ground-truth target set.
2. Assign an endpoint sensitivity class with **≥ 80% agreement** against a hand-labelled set of **≥ 150 endpoints**.
3. Emit, per finding, a **valid CVSS v3.1 vector** and environmental score in 0–10, recomputable by a third party.
4. Correlate findings into the defined chains, with composite score **> any member** score.
5. Scan a reference target (≤ 100 endpoints) within a **≤ 10-minute** budget.
6. Show measurable improvement in **triage ordering** vs. a flat-CVSS baseline on the same findings.

## 2. Overall description

### 2.1 Product perspective

CAWASMA is a new, self-contained system, not a component of a larger product. It is a layered web application: a Next.js dashboard, a FastAPI backend, an asynchronous scan worker, a pure-Python scanner engine, and a PostgreSQL store. It calls out only to the scan target and, optionally, to an LLM API for an executive summary.

### 2.2 Product functions (summary)

- Accept and authorise an HTTPS target; discover endpoints.
- Run misconfiguration checks across headers, cookies, CORS, TLS, REST-API surface, auth signals, and information disclosure.
- Infer endpoint sensitivity (NLP) and response-body sensitivity signals.
- Correlate findings into attack chains.
- Score every finding as a CVSS v3.1 environmental vector.
- Store, rank, display, and export results; keep scan history.

### 2.3 User classes and personas

| User class | Description | Primary needs |
|---|---|---|
| Security analyst / pentester | Primary user; scans client targets | Findings ranked by real risk; defensible CVSS; exportable report |
| Developer / small-site owner | Non-specialist | Plain-language, prioritised "fix this first" report |
| Security student | Learner | Transparent scoring: see the vector, class, signals, and chain behind each score |

### 2.4 Operating environment

- Server: Ubuntu 22.04, Python 3.11, ≥ 8GB RAM.
- Runtime: Next.js (3000), FastAPI (8000), Celery worker + Redis (if retained), PostgreSQL.
- Delivered via `docker compose` for reproducible setup.
- Local ML model (all-MiniLM-L6-v2, ~22MB); no external ML calls required.

### 2.5 Design and implementation constraints

- Three-member team; six 2-week sprints.
- Fixed stack: Next.js / FastAPI / httpx / PostgreSQL + SQLAlchemy / sentence-transformers / spaCy / WeasyPrint (Celery+Redis conditional).
- Black-box only — no credentials, no source, no agent.
- Passive only — no state-modifying payloads.
- Severity must be expressed within CVSS v3.1 (no out-of-model scoring).

### 2.6 Assumptions and dependencies

- The analyst is authorised to scan the target (enforced at input).
- The target is reachable over HTTPS and is predominantly REST/JSON.
- Legal vulnerable targets (Juice Shop, DVWA, VAmPI, crAPI) are available for evaluation.
- A hand-labelled endpoint set exists for classifier evaluation.
- SSLyze (recommended) is available for TLS checks; WeasyPrint for PDF export.
- Optional: an LLM API key for the executive-summary feature.

## 3. Functional requirements

Priority is MoSCoW (Must / Should / Could / Won't this time). Each acceptance criterion should become a test.

| ID | Requirement (The system shall…) | Priority | Acceptance criteria |
|---|---|---|---|
| FR-01 | accept an HTTPS target URL and require explicit authorisation confirmation before any scan | Must | Scan refuses without authorisation; non-HTTPS URLs rejected with a clear message |
| FR-02 | discover endpoints via HTML-link, JS-source, wordlist, and recursive (depth-2) strategies | Must | Discovers ≥ the known endpoint set on a seeded app; visited-set prevents loops |
| FR-03 | run the defined misconfiguration checks on each endpoint and record each failure as a finding | Must | Each finding stores check id, endpoint, evidence, and taxonomy mapping |
| FR-04 | map each check to OWASP Top 10 / OWASP API Top 10 / CWE where applicable | Must | Every check has a documented mapping or explicit "none" |
| FR-05 | assign each endpoint a sensitivity class (Critical/High/Medium/Low) from URL semantics, no human input | Must | Class produced for every endpoint; ≥ 80% agreement vs. labelled set |
| FR-06 | scan each response body for sensitivity signals (credentials, PII, financial, internal infra) and attach them to the finding | Must | Known signal strings in a test response are detected and recorded |
| FR-07 | compute, per finding, a CVSS v3.1 vector string and environmental score in 0–10 | Must | Output is a parseable CVSS v3.1 vector; recomputes to the same score in an independent calculator |
| FR-08 | derive context (sensitivity class, response signals) through CVSS environmental metrics, not an out-of-range multiplier | Must | No pre-cap score exceeds 10; the vector encodes the context (e.g. CR/IR) |
| FR-09 | correlate findings against the defined chain templates and emit a composite-scored chain when all members are present | Must | A seeded finding set triggers the expected chain; composite > max member score |
| FR-10 | persist scans, endpoints, findings, headers, cookies, TLS info, and chains in PostgreSQL | Must | Records survive restart; a scan is fully reconstructable from the DB |
| FR-11 | present a dashboard listing findings sorted by context-adjusted severity, filterable by severity and category | Must | Findings render highest-first; filters work |
| FR-12 | export the report as PDF, JSON, HTML, and CSV | Should | Each format generates with all findings and scores |
| FR-13 | show scan history and allow re-opening past scans | Should | History lists scans with timestamp/target; re-open shows stored results |
| FR-14 | expose the scoring breakdown per finding (base vector, class, signals, chain) in the UI | Should | Each finding expands to show how its score was built |
| FR-15 | run scans asynchronously and let the dashboard poll live status | Should | Submit returns immediately; queued→running→done transitions visible |
| FR-16 | record analyst false-positive corrections against findings | Could | A finding can be marked FP; stored in the feedback table |
| FR-17 | generate an LLM executive summary when an API key is configured | Could | With key: summary produced; without key: scan still completes normally |
| FR-18 | allow per-scan tuning of wordlist and crawl depth | Could | Settings accepted and applied; defaults used when unset |
| FR-19 | support authenticated scanning (session/token) to enable true BOLA/mass-assignment detection | Won't (this time) | Out of scope; documented as future work |

## 4. Non-functional requirements

| ID | Requirement | Category | Priority | Acceptance criteria |
|---|---|---|---|---|
| NFR-01 | A scan of ≤ 100 endpoints completes within 10 minutes on the reference 8GB server | Performance | Must | Measured and logged per scan |
| NFR-02 | Endpoints are fetched concurrently (async httpx) with a configurable concurrency cap | Performance | Should | Concurrency setting honoured; no unbounded fan-out |
| NFR-03 | Detection reaches ≥ 80% recall and ≤ 15% FPR on the ground-truth target set | Accuracy | Must | Measured precision/recall/FPR reported per target |
| NFR-04 | The target URL is validated; private/loopback/metadata addresses are refused unless explicitly allowed (SSRF self-protection) | Security (tool) | Must | Requests to 169.254.169.254, localhost, RFC1918 blocked by default |
| NFR-05 | Secrets (API keys, DB creds) live in env/.env, never in code or logs; captured credentials are masked in storage | Security (tool) | Must | No secret in repo; .env.example only; captured creds masked |
| NFR-06 | The dashboard is understandable by a non-specialist (severity colour, plain description) | Usability | Should | A persona-2 user identifies top-3 fixes unaided |
| NFR-07 | The scanner handles unreachable targets, timeouts, rate limits, and WAF blocks without crashing | Reliability | Must | Injected failures produce a graceful error state, recorded against the scan |
| NFR-08 | New checks are addable without modifying the engine core (check registry pattern) | Maintainability | Should | A new check is added in one file and auto-registered |
| NFR-09 | The whole system runs via a single docker compose up | Portability | Must | Fresh machine → one command → working stack |
| NFR-10 | The tool scans only the authorised target/in-scope hosts; off-host links are not scanned | Legal/ethical | Must | Off-host URLs discovered but logged as out-of-scope, not scanned |
| NFR-11 | Scanning remains passive — no state-modifying requests | Legal/ethical | Must | Request log shows only safe methods / non-mutating probes |
| NFR-12 | The codebase carries automated tests run in CI on every push | Maintainability | Should | CI green; checks have unit tests |
| NFR-13 | Results for one target are reproducible run-to-run (deterministic checks; stable classifier) | Reliability | Should | Same target → same findings set (allowing for target changes) |

## 5. External interface requirements

### 5.1 User interface

- **New-scan page:** target URL field, authorisation confirmation, optional wordlist/crawl-depth settings.
- **Results page:** findings ranked by context-adjusted severity, filters (severity, category), per-finding drill-down showing the CVSS vector, sensitivity class, response signals, and chain membership.
- **History page:** list of past scans with timestamp and target; re-open restores results.
- Severity shown by colour and bucket (Critical/High/Medium/Low/Info).

### 5.2 Software (API) interface

- `POST /api/scan` — submit a target; returns a scan id and queued status.
- `GET /api/results/{id}` — scan status and findings (polled for live status).
- `GET /api/results/{id}/export?format=pdf|json|csv|html` — report export.
- `POST /api/ai/chat` — optional LLM executive summary (only when a key is configured).
- Internal: Celery task dispatch via Redis (if retained); SQLAlchemy to PostgreSQL.

### 5.3 Hardware interface

- No special hardware. Runs on the Ubuntu 22.04 reference server (≥ 8GB RAM); no GPU required for the local model.

### 5.4 Software dependencies

- httpx (HTTP/2, async), BeautifulSoup4 (HTML parsing), sentence-transformers + all-MiniLM-L6-v2 (classification), spaCy + regex (PII), SSLyze (TLS), WeasyPrint (PDF), SQLAlchemy + PostgreSQL, Next.js, FastAPI, Celery + Redis (conditional).

## 6. Use cases and user stories

### 6.1 Use cases

**UC-1 — Run a context-aware scan.** Actor: analyst. Pre: authorised, target reachable over HTTPS. Main: enter URL → confirm authorisation → submit → discover endpoints → classify sensitivity → run checks → score with context → correlate chains → store → show ranked findings. Alt/fail: non-HTTPS → rejected (FR-01); unreachable → error state, partial results kept (NFR-07); authorisation not confirmed → blocked.

**UC-2 — Review and triage findings.** Actor: analyst/developer. Pre: completed scan. Main: open scan → findings by adjusted severity → filter → expand to see CVSS vector, class, signals, chain. Alt: mark a finding false positive (FR-16).

**UC-3 — Export a report.** Actor: analyst. Main: choose PDF/JSON/HTML/CSV → generate → download. Fail: generation error → message; other formats still available.

**UC-4 — Inspect an attack chain.** Actor: analyst/student. Pre: a scan that triggered ≥ 1 chain. Main: open chain → members, template matched, composite vs. individual scores.

**UC-5 — View scan history.** Actor: analyst. Main: open history → past scans → re-open one → stored results.

### 6.2 User stories (Must and Should)

| Story | Acceptance criteria |
|---|---|
| As an analyst, I want to enter a URL and confirm authorisation, so that I only scan targets I'm allowed to. | Scan blocked until authorised; non-HTTPS rejected. |
| As an analyst, I want endpoints found that I didn't list, so that coverage doesn't depend on my knowledge of the app. | Crawler finds endpoints beyond the seed, including JS-referenced API routes. |
| As an analyst, I want each endpoint's sensitivity judged automatically, so that payment/auth endpoints rank above public pages. | Every endpoint gets a class; ranking reflects it. |
| As an analyst, I want severity adjusted by what the response exposes, so that a credential leak outranks a cosmetic header gap. | Finding with a credential signal scores higher than the same finding without. |
| As an analyst, I want a valid CVSS score per finding, so that I can defend the rating to a client. | Output is a recomputable CVSS v3.1 vector. |
| As an analyst, I want findings grouped into exploit chains, so that I see compound risk. | Chain shows members and a composite above any member. |
| As a developer, I want a prioritised, plain-language report, so that I know what to fix first. | Report lists top fixes with clear descriptions and severity. |
| As an analyst, I want to export the report in common formats, so that I can share it. | PDF/JSON/HTML/CSV all generate with full content. |
| As a student, I want to see why a finding scored as it did, so that I learn the reasoning. | Expandable breakdown: base vector, class, signals, chain. |
| As an analyst, I want scans to run in the background with live status, so that I'm not blocked waiting. | Submit returns immediately; status updates visible. |
| As an analyst, I want past scans saved, so that I can revisit them. | History lists scans; re-open restores results. |

## 7. Traceability matrix

| Objective | Requirement IDs | Module / component | How tested |
|---|---|---|---|
| O1 Detect misconfigs (≥80% recall, ≤15% FPR) | FR-02, FR-03, FR-04; NFR-03, NFR-07 | crawler.py, checks.py, engine.py | Ground-truth run on Juice Shop/DVWA/VAmPI/crAPI; precision/recall/FPR |
| O2 Auto sensitivity class (≥80%) | FR-05 | sensitivity.py | Agreement vs. hand-labelled endpoint set; confusion matrix |
| O3 Valid CVSS v3.1 score | FR-07, FR-08, FR-14 | cvss.py | Vector parsed and recomputed in an independent calculator |
| O4 Chain correlation, composite > member | FR-09 | chains.py | Seeded finding sets trigger expected chains; score comparison |
| O5 Scan time ≤ 10 min | NFR-01, NFR-02; FR-15 | engine.py, tasks.py | Timed scans on the reference target |
| O6 Better triage ordering vs. flat CVSS | FR-05, FR-06, FR-08, FR-11 | sensitivity.py, body_classifier.py, cvss.py, frontend | Ranking comparison: context-adjusted vs. base-only order on the same findings |
| Legal/ethical safeguards | FR-01; NFR-04, NFR-05, NFR-10, NFR-11 | routes/scan.py, engine.py | Authorisation-gate test; SSRF-block test; off-host + passive-only checks |
| Reproducible demo | NFR-09, NFR-12 | docker-compose, CI | Fresh-machine one-command bring-up; CI run |

Change log: this SRS supersedes the original project summary. Key changes — scoring moved to CVSS v3.1 environmental metrics (FR-07, FR-08); auth-dependent checks (BOLA, mass assignment, injection) relabelled best-effort or deferred (FR-19); accuracy and reproducibility made explicit requirements (NFR-03, NFR-09, NFR-12).
