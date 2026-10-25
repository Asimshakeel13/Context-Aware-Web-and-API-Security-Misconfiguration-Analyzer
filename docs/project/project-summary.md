# CAWASMA — Complete Project Summary (current)

> Imported from the team PDF `CAWASMA — Complete Project Summary (current).pdf` (local copy in `pdf/`, not committed). Converted to Markdown on 2026-10-25; tables and lists are kept, page headers dropped.

Oct 22, 2026 · @Shoaib Younas

Complete context document for CAWASMA, in the original format, updated to the current agreed state: CVSS v3.1 environmental scoring (not the old multiplier), honest novelty claims, auth-dependent checks marked best-effort, and the final three-person split. The last section lists exactly what changed from the first summary.

## Project identity

| Field | Value |
|---|---|
| Name | CAWASMA |
| Full name | Context-Aware Web and API Security Misconfiguration Analyzer |
| Type | Final Year Project — BS Computer Science |
| University | FAST-NUCES Islamabad, Pakistan |
| Team | 3 members — Atta Ur Rehman, Neelam, Asim |
| Developer (repo) | Asim Shakeel — github.com/Asimshakeel13 |
| Status | In development |
| Methodology | Agile Scrum, six 2-week sprints across 2 FYP iterations |

## What is this

A black-box HTTPS security-misconfiguration scanner for web applications and REST APIs. An analyst enters an HTTPS URL; the tool crawls the target, runs its security checks, infers how sensitive each endpoint is and what its responses expose, correlates findings into exploit chains, and scores every finding with a context-aware CVSS v3.1

environmental vector — producing a report prioritised by real-world risk, not raw defect. No source-code access, no agent installation, no prior asset configuration: pure passive black-box testing over HTTPS.

## The core problem

Every existing scanner (OWASP ZAP, Nikto, SecurityHeaders.com, Burp) shares one flaw: **static scoring**. Missing HSTS on `/public/about` gets the same CVSS 7.4 as missing HSTS on `/api/payment/checkout`. Same score, completely different real-world risk. The result is that security teams receive flat lists of 80 equally-scored findings with no guidance on what to fix first. Manual triage is slow, inconsistent, and misses chained exploits.

**Academic proof of the problem (all three verified):**

- **Wunder et al., 2024** — 68% inconsistency in manual CVSS scoring of identical misconfiguration findings. Shedding Light on CVSS Scoring Inconsistencies, IEEE S&P 2024 (Distinguished Paper); 196 evaluators, 59-person follow-up.
- **Golmohammadi, Zhang & Arcuri, 2023** — surveyed 92 API-security papers; named context-aware scoring among the open research problems. Testing RESTful APIs: A Survey, ACM TOSEM 2023.
- **Ahmadi Mehri et al., 2022** — ACVRM is the closest prior work but requires a human-configured asset inventory. CAWASMA does the equivalent automatically via NLP. Automated Context-Aware Vulnerability Risk Management, Electronics 2022.

The gap in one sentence: no existing **open-source, black-box, zero-config** scanner automatically infers endpoint sensitivity from URL semantics, correlates findings into exploit chains with a composite score, and adjusts severity on response-body content — all expressed as a standards-valid CVSS score.

## The three contributions

Each is novel as an open-source, zero-config, black-box capability tied to a standard CVSS score — **not** as "the first tool ever to do this." Commercial API-security tools already do versions of each (named in Comparison and Research gap). The contribution is combining all three in one free tool and proving it against ground truth.

### Contribution 1 — NLP endpoint-sensitivity classification

URL path → tokenised → abbreviations expanded → Sentence-Transformer embedding → cosine similarity against 4 class anchors → sensitivity class assigned automatically, with zero human input.

- Model: `all-MiniLM-L6-v2` (HuggingFace, ~22 MB, runs locally)
- File: `scanner/sensitivity.py`
- Classes: CRITICAL / HIGH / MEDIUM / LOW

What regex rules miss but NLP catches:

```text
/svc/iam/priv/escalate       -> CRITICAL  (privilege escalation)
/ms/billing/stripe/webhook   -> CRITICAL  (financial transaction)
/api/v2/usr/auth/mfa/verify  -> HIGH      (authentication)
/api/rec/fin/txn/init        -> CRITICAL  (financial init)
/public/about                -> LOW       (public content)
```

### Contribution 2 — Attack-chain correlation (template-based)

All findings are cross-referenced against 5 pre-defined chain templates. When a template's required findings are all present, the chain triggers and a composite CVSS is computed (always higher than any individual member). File: `scanner/chains.py`. Each template carries a documented justification (why these findings chain).

```text
C001: XSS -> Cookie Theft -> Account Takeover         -> 9.4 CRITICAL
C002: Info Disclosure -> Targeted Exploit             -> 8.2 HIGH
C003: CORS -> CSRF -> Privilege Escalation            -> 9.6 CRITICAL
C004: Unauthenticated Exposure + BOLA -> Data Breach  -> 9.1 CRITICAL
C005: .env Exposed + Version Leak -> Full Compromise   -> 9.8 CRITICAL
```

### Contribution 3 — Response-body-aware severity adjustment

Every endpoint response body is scanned for sensitivity signals; detected signals feed the CVSS environmental metrics (they raise the Confidentiality/Integrity Requirement rather than adding an out-of-model bonus — see Scoring). File: `scanner/body_classifier.py`.

```text
Credentials in response  -> forces CRITICAL (Confidentiality Requirement
High)
PII detected             -> raises Confidentiality Requirement
Financial data           -> raises Confidentiality/Integrity Requirement
Internal IP / infra      -> raises severity
```

## CVSS scoring (corrected method)

**This replaces the original** `Base × Multiplier + Bonus` **formula**, which was not valid CVSS and produced pre-cap scores above 10. Context now enters through the CVSS v3.1 **environmental** metric group, so the output stays a valid CVSS vector, recomputable by a third party, bounded 0–10 by construction.

**Standard:** CVSS v3.1 (same as NIST NVD). Every finding emits a full vector string plus its environmental score.

### How context is applied

- **Base vector** — pre-mapped per check. All checks have fixed CVSS v3.1 vector strings in `scanner/cvss.py`. No human scoring.
- **Endpoint sensitivity class** (Contribution 1) → mapped to the CVSS **Security** **Requirement** metrics (Confidentiality/Integrity/Availability Requirement = High / Medium / Low). A payment endpoint gets CR = High; a public page gets CR = Low.
- **Response-body signals** (Contribution 3) → raise the Confidentiality/Integrity Requirement (e.g. a credential leak → CR High), not a flat additive bonus.
- **Chain membership** (Contribution 2) → composite score computed from the chain template, always above any single member.

Because these are defined inputs to the standard CVSS formula, the final score is always a valid 0–10 CVSS environmental score and a recomputable vector — no cap hack, no arbitrary constants.

### Severity buckets (official CVSS v3.1)

```text
9.0 - 10.0  ->  CRITICAL
7.0 - 8.9   ->  HIGH
4.0 - 6.9   ->  MEDIUM
0.1 - 3.9   ->  LOW
0.0         ->  INFO
```

### Worked example (the thesis in one example)

Missing X-Frame-Options, base ≈ 6.1.

```text
On /api/payment/checkout (sensitivity CRITICAL, PII+financial in response):
base 6.1 + environmental CR/IR = High  ->  ~9.x  ->  CRITICAL
On /public/about (sensitivity LOW, nothing in response):
base 6.1 + environmental CR = Low       ->  ~3.7  ->  LOW
```

Same defect, same base vector — the endpoint context moves it from LOW to CRITICAL, inside the standard. (Environmental scoring compresses the range versus the old multiplier, but the ranking the project depends on — sensitive endpoint scores higher — holds, and now holds defensibly.)

## What we scan

```text
Targets:      Web applications + REST APIs over HTTPS only
NOT targeted: SOAP, full GraphQL, HTTP-only, gRPC, WebSocket
Mode:         Pure black-box, passive, no state-modifying payloads
API scope:    REST only (JSON over HTTP, standard methods)
```

**Why REST only:**

- **SOAP** — XML + WSDL, different protocol, legacy.
- **GraphQL** — single endpoint, query language, separate tooling. (One introspection probe is kept; GraphQL is otherwise out of scope — see the note in What changed.)
- **gRPC** — binary Protobuf, httpx cannot probe it.
- **WebSocket** — persistent connection, not request-response.
- **REST** — JSON/HTTP, maps perfectly to the probe structure; the OWASP API Top 10 is written for REST; ~90% of modern APIs are REST.

Scanning is **passive**: no state-modifying payloads, only safe/non-mutating probes. The tool scans only the authorised target and its in-scope hosts; off-host links are discovered but not followed.

## The 58 security checks — 7 categories

Checks live in `scanner/checks.py` as a registry (one function per check, auto-registered — adding one is a one-file change). Checks marked ⚠ **best-effort** cannot be done reliably black-box without auth or state-changing payloads; they are reported as candidates, not confirmed detections. Final check count will be frozen after Sprint 1 (depth over breadth).

### HEADERS (12)

HSTS, CSP, X-Frame-Options, X-Content-Type-Options, Referrer-Policy, Permissions-Policy, Server version leak, X-Powered-By leak, COOP, CORP, Cache-Control, Expect-CT (flag as **present/deprecated**, not missing — the header is dead since 2022).

### COOKIES (6)

HttpOnly flag, Secure flag, SameSite attribute, Session token in URL, Cookie scope too broad, Token entropy.

### CORS (5)

Wildcard origin, Origin reflection, Credentials + wildcard, Unsafe methods cross-origin, Missing max-age.

### TLS (8)

TLS 1.0/1.1 active, Weak cipher suite, Certificate expiry, Self-signed cert, No HTTP→HTTPS redirect, Mixed content, HSTS preload missing, Hostname mismatch. (Implemented with the SSLyze library rather than hand-rolled.)

### API — REST only (14)

Rate limiting absent, TRACE method enabled, Unauthenticated data exposure, Verbose errors/stack traces, Mass assignment ⚠, BOLA/IDOR ⚠, Missing API versioning, Deprecated API active, OPTIONS excessive methods, JWT misconfiguration ⚠, API overfetching, GraphQL introspection enabled (single probe), Secrets in response, Injection probe ⚠.

### AUTH (7)

Basic Auth scheme, Broken Function Level Auth ⚠, Weak password-reset token ⚠, Token not invalidated on logout ⚠, Bad auth handling, Default credentials, OAuth2 open redirect.

### INFO DISCLOSURE (6)

Internal IP in response, Directory listing, .env file exposed, .git repo exposed, Backup files exposed, Swagger/API docs public.

### OWASP API Top 10 2023 coverage

```text
API1  BOLA/IDOR              -> covered (best-effort black-box)
API2  Broken Authentication  -> covered
API3  Mass Assignment        -> covered (best-effort)
API4  Rate Limiting          -> covered
API5  Function Level Auth     -> partial
API6  Business Flow          -> not covered (needs logic knowledge)
API7  SSRF                   -> not covered (needs DNS callback infra)
API8  Misconfiguration       -> core coverage
API9  Inventory Management   -> partial
API10 Unsafe Consumption     -> not covered (needs 3rd-party knowledge)
```

## Crawler — own Python tool (no ffuf/gobuster)

Four strategies using httpx + BeautifulSoup, in `scanner/crawler.py`:

1. **HTML link extraction** — parse `<a href>`, `<form action>`, `<script src>` from HTML.
2. **JS source scanning** — download `.js` files, regex for `fetch('/api/...')`, `axios.get(...)`, `baseURL` patterns. Finds React/Vue hidden API routes that Gobuster cannot.
3. **Wordlist probing** (what Gobuster does, built in) — a ~200-entry custom wordlist: `/admin`, `/api/v1`, `/api/v2`, `/.env`, `/.git/HEAD`, `/swagger-ui.html`, `/graphql`, `/login`, `/api/users`, ... GET each; non-404 → add to the endpoint list.
4. **Recursive crawl** — follow links on discovered pages up to depth 2; a visited-set prevents infinite loops. Off-host links are logged but not followed.

## Tech stack

```text
Frontend:     Next.js         (dashboard, results, scan form)
Backend API:  Python FastAPI   (scan management, results, AI chat)
Database:     PostgreSQL       (scan history, findings, chains)
Scanner:      Python 3.11 + httpx (HTTP/2, async)
HTML parser:  BeautifulSoup4
Task queue:   Celery + Redis   (async background scanning; conditional)
NLP model:    sentence-transformers (all-MiniLM-L6-v2, ~22 MB)
PII detection: spaCy + regex
TLS scanning: SSLyze
PDF export:   WeasyPrint
LLM summary:  OpenAI / Anthropic API (optional, off the critical path)
ORM:          SQLAlchemy + Alembic migrations
Server:       Ubuntu 22.04, Python 3.11, 8GB RAM minimum
```

**Architecture:**

```text
Next.js (port 3000)
| fetch/axios
FastAPI (port 8000)
| dispatches
Celery worker (or FastAPI BackgroundTasks)
| runs
Scanner pipeline  ->  PostgreSQL
```

Added to the original: **URL validation / SSRF self-protection** at the engine boundary (block private/loopback/metadata addresses), and the whole stack brought up with one `docker compose up`.

Note on Celery+Redis: kept only if it earns its place (concurrent multi-scan); otherwise FastAPI BackgroundTasks is the simpler fallback — decided in Sprint 1.

## Project file structure

```text
cawasma/
|
|-- frontend/                 <- Next.js
|   |-- app/
|   |   |-- page.tsx          <- dashboard home
|   |   |-- scan/new/page.tsx <- new scan form
|   |   |-- scan/[id]/page.tsx<- results page
|   |-- components/
|   |-- package.json
|
|-- backend/                  <- FastAPI
|   |-- main.py               <- FastAPI entry point
|   |-- models.py             <- SQLAlchemy + PostgreSQL models
|   |-- database.py           <- DB connection
|   |-- routes/
|   |   |-- scan.py           <- POST /api/scan
|   |   |-- results.py        <- GET /api/results/{id}
|   |   |-- ai.py             <- POST /api/ai/chat
|   |-- tasks.py              <- Celery scan orchestrator
|
|-- scanner/                  <- Core engine (pure Python)
|   |-- engine.py             <- httpx HTTPS engine + SSRF guard
|   |-- crawler.py            <- 4-strategy endpoint discovery
|   |-- checks.py             <- all check functions (registry)
|   |-- sensitivity.py        <- NLP classifier (Contribution 1)
|   |-- chains.py             <- attack-chain correlator (Contribution 2)
|   |-- body_classifier.py    <- response-body scanner (Contribution 3)
|   |-- cvss.py               <- CVSS v3.1 environmental scoring
|   |-- reports.py            <- PDF/JSON/HTML/CSV export
|
|-- tests/                    <- pytest (per-check + API)
|-- eval/                     <- ground-truth lists, baselines
|-- config.py                 <- all settings via .env
|-- requirements.txt
|-- .env.example
|-- docker-compose.yml
|-- docker-compose.eval.yml    <- vulnerable targets, separate
|-- .gitignore
```

## Database — 10 tables (PostgreSQL)

| Table | One row per | Key fields |
|---|---|---|
| SCAN | scan job | id, target_url, status, started_at, finished_at, authorised, settings |
| ENDPOINT | discovered URL | id, scan_id, url, method, sensitivity_class, discovery_strategy |
| FINDING | failed check | id, endpoint_id, check_id, owasp_map, cwe_map, cvss_vector, base_score, final_score, severity_bucket, evidence |
| HEADER | captured header | id, endpoint_id, name, value |
| COOKIE | captured cookie | id, endpoint_id, name, flags (HttpOnly/Secure/SameSite), scope |
| TLS_INFO | TLS handshake per endpoint | id, endpoint_id, protocol_versions, weak_ciphers, cert_expiry, issues |
| ATTACK_CHAIN | triggered chain | id, scan_id, template_id, composite_score |
| CHAIN_FINDING | chain-finding link (M:N) | chain_id, finding_id |
| AI_INSIGHT | LLM summary | id, scan_id, summary_text |
| FEEDBACK | analyst FP correction | id, finding_id, is_false_positive, note |

Schema is versioned with Alembic migrations — never edited by hand, so the team and the demo machine stay in sync.

## End-to-end scan flow

```text
1.  Analyst submits https://target.com via the Next.js dashboard
and confirms authorisation (scan blocked without it)
2.  Next.js -> POST /api/scan -> FastAPI
3.  FastAPI creates a Scan record in PostgreSQL (status: queued)
4.  FastAPI dispatches a Celery task via Redis (or BackgroundTasks)
5.  Worker picks up -> starts the async Python pipeline
6.  httpx engine validates the URL (SSRF guard) and opens HTTPS/TLS
7.  Crawler runs 4 strategies -> builds the endpoint list
8.  For each endpoint:
a. NLP classifier -> assigns CRITICAL/HIGH/MEDIUM/LOW
b. GET -> captures all headers + body
c. check functions run on captured data
d. extra probes: CORS, OPTIONS, burst, TRACE, path probes
e. body classifier -> scans for PII/credentials/financial
9.  Chain correlator checks the 5 templates against the finding set
10. CVSS engine: base vector + environmental (class + signals) = final score
+ vector
11. FastAPI stores all findings in PostgreSQL
12. LLM generates an executive summary (only if an API key is set)
13. Reports generated: PDF + JSON + HTML + CSV
14. Next.js results page polls FastAPI -> displays ranked results live
```

## Comparison with existing tools

| Feature | ZAP | Nikto | SecurityHeaders | CAWASMA |
|---|---|---|---|---|
| Detects misconfigurations | yes | yes | yes | yes |
| CVSS v3.1 scoring | partial | no | no | yes |
| Context-aware scoring | no | no | no | yes ★ |
| NLP endpoint classification | no | no | no | yes ★ |
| Attack-chain correlation | no | no | no | yes ★ |
| Response-body score adjustment | no | no | no | yes ★ |
| REST API checks (BOLA etc.) | partial | no | no | yes (best-effort) |
| Black-box, zero config | yes | yes | yes | yes |
| Structured PDF/JSON report | yes | partial | no | yes |
| Modern frontend (Next.js) | no | no | no | yes |

★ = novel among **open-source black-box** tools. These capabilities exist in commercial API-security products (Traceable, Cequence, Akto, Escape) — see Research gap — so the ★ claim is scoped to the open-source black-box space, not "no tool anywhere."

## Research gap and honest novelty

**Verified prior work:**

- **Golmohammadi, Zhang & Arcuri, 2023** — 92 papers surveyed; context-aware scoring noted among open problems. arXiv:2212.14604
- **Wunder et al., 2024** — 68% inconsistency in manual CVSS scoring of the same findings. arXiv:2308.15259
- **Ahmadi Mehri et al., 2022 (ACVRM)** — closest prior work but requires a human-configured asset inventory; CAWASMA does it automatically via NLP. MDPI Electronics 11(21):3580

**Commercial prior art (name these, don't claim "first ever"):**

- Cequence and Traceable already classify endpoints from the URL with ML and score risk from response-data sensitivity — overlaps Contributions 1 and 3.
- Akto (open-source API security) already flags PII/credentials/tokens in response payloads — overlaps Contribution 3.
- Escape chains multi-step attacks with AI exploit validation — overlaps Contribution 2 (CAWASMA's version is simpler, template-based).

**Honest gap statement:** No existing **open-source, black-box, zero-config** scanner combines automatic URL-semantic sensitivity inference, response-body adjustment, and template-based chain correlation into a single, recomputable CVSS v3.1 environmental score, evaluated against ground truth with an open-source baseline. That combination — plus a reproducible evaluation — is the defensible contribution.

**Unverified citation:** Molnár & Bilicki 2022 ("11 scanners, none context-aware") could not be verified and should be dropped or replaced with a verified source (e.g. Albahar et al., Applied Sciences 2022) before it goes in the report.

## Team and responsibilities

Asim specifies the security logic and Atta codes it; Docker/CI is shared between Atta and Neelam. Three people work in parallel because five interface contracts are fixed in Sprint 1 (check-spec format, FINDING schema, API contract, the CVSS mapping, shared DevOps).

| Partner | Role | Owns |
|---|---|---|
| Atta Ur Rehman (A) | Backend & scanner engine | engine.py, crawler.py, checks.py (implementation), cvss.py, FastAPI backend, Celery/async, DB + Alembic, reports.py; half of Docker/CI |
| Neelam (B) | Frontend & shared DevOps | Next.js dashboard, scan form, results + drill-down, history, export UI; half of Docker/CI |
| Asim (C) | Security, ML/NLP & evaluation | check specifications, CVSS environmental mapping, chain templates, sensitivity.py, body_classifier.py, ground-truth datasets, evaluation + ZAP/Nuclei baselines |

## Project management

Methodology: Agile Scrum, 2-week sprints, 6 sprints across 2 FYP iterations, 3 members. **Evaluation is pulled forward to Sprint 2** (not Sprint 5), and the scoring fix is designed in Sprint 1.

| Sprint | Goal | Owners |
|---|---|---|
| 1 | Foundations + decisions locked: lit review, novelty rewritten, CVSS-environmental mapping designed, architecture + schema + Alembic, repo + Docker + CI, engine + SSRF + crawler skeleton, API contract + scan form on mock | Asim (mapping/specs), Atta (backend/infra), Neelam (frontend) |
| 2 | Vertical slice + eval harness: 1 check → class → env score → store → show; vulnerable targets in Docker + ground-truth; hand-label 150+ endpoints; build sensitivity.py | All three |
| 3 | Full check set + context layer: checks + tests; classifier measured; body_classifier + chains; results API + full results page + drill-down | Atta, Asim, Neelam |
| 4 | Platform complete: Celery/async, export, guards; live status, history, export UI; run evaluation + tool security review | Atta, Neelam, Asim |
| 5 | Measured evaluation + hardening: precision/recall/FPR vs ZAP + Nuclei, ranking experiment; FP triage; usability polish | Asim, Atta, Neelam |
| 6 | Polish + buffer: README + demo GIF, final fixes, reproducibility check | Neelam + all |

**Course learning outcomes:** CLO2 Design + Implementation (40%), CLO3 Working Demo (40%), CLO4 Project Management, CLO5 Teamwork.

**Definition of Done (per task):** reviewed by one other member; unit test(s) passing; docs/README updated; merged to `main` via PR with green CI. A check is done only when a test proves it fires on a known-vulnerable target and stays silent on a clean one.

(Report writing, slides, and viva prep are intentionally excluded from this plan, as scoped.)

## UML diagrams produced

```text
Use Case Diagram      -> draw.io XML (20 use cases, 3 actors)
Activity Diagram      -> PlantUML   (swim lanes, parallel fork/join)
Flow Diagram          -> Mermaid    (data flow module to module)
System Architecture   -> PlantUML   (6-layer component diagram)
Deployment Diagram    -> PlantUML   (physical node topology)
Class Diagram         -> PlantUML   (22 classes)
Component Diagram     -> PlantUML   (named interfaces)
ER Diagram            -> Mermaid    (10 tables, full cardinality)
State Machine         -> PlantUML   (ScanJob states)
Sequence Diagrams     -> PlantUML   (3 SSDs)
```

## What changed from the original summary

| Aspect | Original | This version |
|---|---|---|
| Scoring | Final = (Base × | CVSS v3.1 environmental metrics (class → CR/IR; signals → raise CR); always a valid 0–10 vector |
|  |  | CVSS v3 |
|  | Multiplier) + Bonus , cap 10; pre-cap scores like 15.7 |  |
| Novelty claim | "No existing public tool does this" | "First open-source black-box tool to combine these into a recomputable CVSS score"; commercial prior art named |
| BOLA / mass assignment / injection / JWT | listed as detected | marked ⚠ best-effort candidates (can't be done reliably black-box without auth) |
| Expect-CT | flagged as a missing header | flagged as present/deprecated (header dead since 2022) |
| GraphQL | contradiction (out of scope + a check) | single introspection probe; otherwise out of scope |
| Comparison ★ | "not in any existing public tool" | scoped to "open-source black-box" |
| Evaluation | Sprint 5 | Sprint 2, with ground truth + ZAP/Nuclei baseline + a labelled endpoint set |
| Team | "3 members" (count) | Atta (backend), Neelam (frontend), Asim (security + ML + eval); Asim specs, Atta codes |
| Added | — | SSRF self-protection, tests + CI, one-command Docker, Alembic migrations, SSLyze for TLS |
| Molnár & Bilicki 2022 citation | cited | unverified — get the DOI or drop it |

Everything else from the original (the three contributions as concepts, the passive black-box REST-only scope, the architecture, the 10-table schema, the module layout, the crawler's 4 strategies, the stack) is unchanged — the revisions sharpen the project, they

don't rebuild it.
