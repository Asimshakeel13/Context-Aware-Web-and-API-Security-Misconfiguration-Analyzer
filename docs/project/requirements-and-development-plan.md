# CAWASMA — Requirements Specification & Development Plan

> Imported from the team PDF `CAWASMA — Requirements Specification & Development Plan.pdf` (local copy in `pdf/`, not committed). Converted to Markdown on 2026-10-25; tables and lists are kept, page headers dropped.

Oct 14, 2026 · @Shoaib Younas

## Executive summary

CAWASMA is a solid, well-scoped FYP with a genuine integrating idea — context-aware severity for black-box misconfiguration scanning — but its three "novel" contributions are weaker than the summary claims, and the scoring maths as written produces indefensible numbers. The project is buildable by three people and demonstrates real, employable skills. The work now is to narrow the novelty claim to what is actually defensible, fix the CVSS formula, and plan the evaluation from sprint one rather than sprint five.

**FYP jury** — Real problem, clearly stated, and backed by three correctly-cited papers. But "no existing public tool does this" is false as stated: commercial API-security tools already classify endpoint sensitivity and adjust severity on response content. The contribution is the combination in one open black-box tool, not each part. Measurable results are possible but only if evaluation is designed in now.

**Supervisor** — Feasible for three students across six sprints on the chosen stack (FastAPI, Next.js, httpx, Celery). The main delivery risks are the ad-hoc scoring formula (not real CVSS, will not survive questioning), 58 checks being breadth over depth, and the NLP classifier having no labelled test set. Work divides cleanly into scanner / intelligence / platform.

**Recruiter** — Strong portfolio piece: black-box scanning, async Python, a real ML component, a typed API, a modern frontend. It will read as a real product only with tests, CI, Docker, a measured evaluation table in the README, and honest novelty claims. Containerised reproducible demo is the single highest-leverage recruiter signal.

**Top 5 actions**

1. **Fix the scoring formula.** The current `Base × Multiplier + Bonus` is not CVSS and produces pre-cap scores of 15.7; a jury will press on this. Move the context into CVSS v3.1 Environmental metrics (Confidentiality/Integrity Requirement) so the output stays a valid vector string and score. This is the project's technical heart — get it right.
2. **Rewrite the novelty claim.** Drop "no existing tool does this." Claim: "first open-source black-box tool to combine automatic URL-semantic sensitivity inference, response-body adjustment, and chain correlation into a single CVSS-environmental score, evaluated against ground truth." Name Traceable, Cequence, and Escape as the commercial prior art.
3. **Build the evaluation harness in Sprint 2, not Sprint 5.** Stand up OWASP Juice Shop, DVWA, VAmPI and crAPI in Docker with a ground-truth finding list, and measure precision/recall/false-positive rate continuously. Baseline against ZAP and Nuclei on the same targets.
4. **Label a test set for the NLP classifier.** Hand-label 150–300 real endpoint paths with sensitivity classes. Without it, Contribution 1 has no accuracy number and cannot be defended.
5. **Cut or de-risk the weakest checks.** Several of the 58 (mass assignment, BOLA/IDOR, injection probe, JWT misconfig) cannot be done reliably black-box without auth or payloads. Mark them clearly as heuristic/best-effort or move them to "Won't (this time)" rather than claiming detection.

## Three-lens inspection

Each lens below lists what is strong, what is weak, and what is missing. A consolidated, severity-ranked gap list closes the section.

### Lens 1 — FYP jury

**Strong.** The problem is real and well-posed: flat, context-blind severity lists are a genuine pain for anyone triaging scanner output. The three motivating papers are real and accurately summarised — Wunder et al. (IEEE S&P 2024, Distinguished Paper) did find 68% of evaluators changed their rating on the same vulnerability; Golmohammadi, Zhang & Arcuri (ACM TOSEM 2023) did survey 92 papers on REST API testing; Ahmadi Mehri et al. (ACVRM, Electronics 2022) does require a human-configured asset inventory, which CAWASMA replaces with automatic inference. The REST-only scope is defensible and the justification (OWASP API Top 10 is written for REST) is sound.

**Weak.** The novelty is overstated. "No existing public tool infers endpoint sensitivity, correlates chains, or adjusts on response body" does not survive a literature check (see Market context). Each of the three contributions exists commercially. The real contribution is combining them in one open black-box tool and tying the output to a

standard CVSS score — a reasonable FYP contribution, but a smaller one than claimed. The chain templates and body-signal bonuses are hand-tuned constants with no stated derivation, which a jury will read as arbitrary.

**Missing.** Any accuracy target or ground-truth plan. "58 checks" and "5 chains" describe effort, not results. Without precision/recall/FPR against known-vulnerable targets, the defence rests on "it runs," which is the weakest possible FYP outcome.

### Lens 2 — Supervisor

**Strong.** Scope fits three students and six two-week sprints. The stack is mainstream and the students evidently know it. Responsibilities divide cleanly: one owns the scanner engine and checks, one the intelligence layer (NLP, chains, CVSS), one the platform (FastAPI, Next.js, Celery, DB). The 10-table schema is thought through.

**Weak.** Three technical choices need justification the summary doesn't give. (a) The scoring formula is invented, not CVSS — multiplying a base score by 2.0 and adding 3.5 is not how CVSS works and breaks the 0–10 scale before the cap. (b) Celery + Redis is real infrastructure overhead for what may be single-user scans; justify it against a simpler background task or accept the ops cost. (c) 58 checks is breadth that risks every check being shallow; depth on 30 well-tested checks would defend better.

**Biggest delivery risks.** NLP classifier with no labelled evaluation set; black-box checks that genuinely can't be done without auth (BOLA, mass assignment) being claimed as working; evaluation deferred to Sprint 5, leaving no time to react to bad numbers.

**Depth for the degree.** Sufficient — the ML + scoring + async pipeline combination is clearly BS-CS level, provided the scoring is made rigorous rather than ad-hoc.

### Lens 3 — Job recruiter

**Strong.** The skill set on display is in demand: application security, black-box scanning, async Python (httpx, Celery), a typed REST API (FastAPI), sentence-transformers for a real ML use case, PostgreSQL + SQLAlchemy, a Next.js frontend. This is a far better portfolio piece than a CRUD app.

**Weak.** As described it could still read as a class assignment. What separates "real product" from "assignment" on GitHub: a measured evaluation table, tests, CI, a one-command Docker demo, and a README that states value in a sentence. None of these are in the summary. The optional LLM executive-summary feature adds little and risks looking like AI-feature padding.

**Under-a-minute value.** Right now, no — a recruiter would see "another scanner." With a README headline ("prioritises misconfiguration findings by endpoint sensitivity and exploit-chain context, evaluated at X% precision vs ZAP's Y%") and a demo GIF, yes.

### Contradictions in the summary

- **GraphQL.** Listed under "NOT targeted" (scope) but "GraphQL introspection enabled" is check #13 in the API category and appears in the API Top 10 table. Pick one: either a single introspection probe is in scope (fine) or GraphQL is out (then drop the check).
- **Expect-CT.** Listed as header check #12. This header has been deprecated since 2022 and is ignored by all browsers; sending it is now itself a minor finding. Flagging its absence is wrong. Reframe as "flag Expect-CT present (deprecated)" or drop it.
- **Novelty vs. the comparison table.** The comparison table marks four features as "not present in any existing public tool," which the research contradicts. The table needs an honest "open-source black-box" qualifier.

### Consolidated gap list (ranked by severity)

| # | Gap | Severity | Matters most to |
|---|---|---|---|
| 1 | Scoring formula is not valid CVSS; pre-cap scores exceed 10 and the output is no longer a CVSS vector | Critical | Jury, Supervisor |
| 2 | Novelty claim ("no public tool does this") is false as written | Critical | Jury |
| 3 | No ground-truth evaluation plan, no accuracy/FPR targets | Critical | Jury, Recruiter |
| 4 | NLP classifier has no labelled test set to measure against | High | Jury, Supervisor |
| 5 | Black-box checks that need auth/payloads (BOLA, mass assignment, injection) claimed as detected | High | Supervisor, Jury |
| 6 | No tests, CI, or containerised demo described | High | Recruiter |
| 7 | Chain templates and body bonuses are undocumented hand-tuned constants | Medium | Jury |
| 8 | GraphQL and Expect-CT contradictions in scope | Medium | Supervisor |
| 9 | Celery/Redis may be unjustified complexity | Low | Supervisor |
| 10 | Optional LLM summary adds little, risks feature-padding appearance | Low | Recruiter |

## Market context

Bottom line: the commodity parts of CAWASMA (header/cookie/TLS/CORS checks, endpoint discovery, CVSS output) are well-served by free tools, and the three "novel" parts each exist in commercial products. The defensible space is the open-source, black-box, automatic combination. Every claim below is sourced; items marked unverified could not be confirmed.

### Existing tools and what they already do well

| Tool | What it does well (don't rebuild) | Relevance to CAWASMA |
|---|---|---|
| ZAP by Checkmarx (was OWASP ZAP) | Mature black-box DAST; crawl + active/passive scan; left OWASP in 2023, now Checkmarx-maintained, v2.17.0 (Dec 2025) | Primary baseline to compare against |
| Nuclei (ProjectDiscovery) | Template-based scanning; community templates include hundreds of misconfiguration and exposure checks | Baseline; its templates are a ready check inventory |
| MDN HTTP Observatory | Scores HTTP security headers A+–F with a documented point system; runs as a library | Header-check logic and scoring is already solved and open |
| SSLyze | Python TLS/SSL scanning library — weak ciphers, TLS 1.0/1.1, cert issues | Use this library for the 8 TLS checks; don't hand-roll |
| Akto | Open-source API security; 100+ built-in sensitive-data types; flags PII/JWT/tokens in request and response payloads | Directly overlaps Contribution 3 (response-body sensitivity) |
| Escape | Business-logic DAST + AI exploit validation; chains multi-step attacks | Overlaps Contribution 2 (chaining); commercial |
| Burp Suite DAST | Market-standard; 2026 added Burp AI to auto-validate findings and reduce false positives | Context for "AI-assisted scanning" framing |
| Traceable, Cequence | ML classification of endpoints by URL/host/method; risk score from response-data sensitivity + endpoint labels | Directly overlaps Contributions 1 and 3; commercial |

### Where the novelty claims actually stand

- **Contribution 1 (NLP endpoint sensitivity).** Not new in industry. Cequence classifies endpoint type from the URI with ML; Traceable scores endpoints partly from path structure; a Microsoft patent and others cover URL-segment ML risk scoring. New-ish: doing it with an open sentence-transformer model, zero-config, in a free black-box tool. Claim that, not "first."
- **Contribution 2 (attack-chain correlation).** Escape and agentic tools like XBOW chain vulnerabilities; XBOW topped HackerOne's US leaderboard in 2025 doing exactly multi-step chaining. CAWASMA's version is simpler — five fixed templates matched against the finding set, not dynamic exploitation. That's fine and defensible; call it "template-based chain correlation," not novel exploit chaining.
- **Contribution 3 (response-body adjustment).** Akto and Traceable already raise severity when responses carry PII/credentials/financial data. Again: the open black-box packaging is the differentiator, not the idea.

### Realistic gaps CAWASMA can honestly address

1. **Open-source + zero-config + black-box, all three at once.** The tools that do context-aware scoring are commercial and need configuration or traffic capture. A free tool that takes just a URL and returns context-adjusted CVSS is a real, if modest, gap.
2. **Standards-anchored output.** Most context-aware tools emit a proprietary risk score. Emitting a valid CVSS v3.1 environmental vector string that a jury or engineer can recompute is a genuine, teachable differentiator — if the formula is fixed (gap #1).
3. **Reproducible evaluation on public targets.** Published, ground-truth precision/recall against Juice Shop/DVWA/VAmPI with a ZAP baseline is itself a contribution; the academic surveys note evaluation rigor is uneven.

### Relevant recent academic work (for the ML/research contribution)

- Wunder et al., Shedding Light on CVSS Scoring Inconsistencies, IEEE S&P 2024 — arXiv. Verified: 196 users, 68% follow-up inconsistency, Distinguished Paper.
- Golmohammadi, Zhang, Arcuri, Testing RESTful APIs: A Survey, ACM TOSEM 2023 — arXiv. Verified: 92 articles.
- Ahmadi Mehri, Arlos, Casalicchio, Automated Context-Aware Vulnerability Risk Management (ACVRM), Electronics 2022 — MDPI. Verified: requires human-configured asset inventory and criteria weighting.
- Newer prior art worth citing to show awareness: CoSA: Context-Aware Severity Assessment with LLMs (2026, arXiv) infers CVSS base metrics from repository context — close to CAWASMA's goal from the white-box side, so a good contrast point.
- **Molnár & Bilicki 2022** — could not verify a paper with this exact author/title claiming "11 scanners, none context-aware." A related 2022 scanner-comparison study exists (Albahar et al., A Comparative Study of Web Application Security Parameters, Applied Sciences 2022) but with different authors. Treat the Molnár & Bilicki citation as unverified until the team produces the DOI; do not rely on it in the report.

## Requirements — problem, scope, stakeholders

### Refined problem statement

Black-box web and API scanners report security misconfigurations with static, context-blind severity: the same missing header scores identically on a public marketing page and a payment endpoint. Analysts are left with long, flat finding lists and must triage by hand, which is slow and inconsistent (Wunder et al. found 68% rating inconsistency on identical

findings). CAWASMA scans an HTTPS target black-box, infers each endpoint's sensitivity from its URL and response content, correlates findings into known exploit chains, and adjusts severity accordingly — producing a prioritised report where the score reflects real-world risk, not just the raw defect.

### Objectives (each measurable)

1. Detect a defined set of web/API security misconfigurations black-box over HTTPS, at a measured detection rate ≥ 80% recall on a known-vulnerable target set, with false-positive rate ≤ 15%.
2. Automatically assign an endpoint sensitivity class (Critical/High/Medium/Low) with ≥ 80% agreement against a hand-labelled test set of ≥ 150 endpoints.
3. Produce, for every finding, a valid CVSS v3.1 vector string and environmental score in 0–10, recomputable by a third party.
4. Correlate findings into at least the defined chain templates and show the composite score exceeds any single member score.
5. Complete a scan of a reference target (≤ 100 endpoints) within a stated time budget (target: ≤ 10 minutes).
6. Demonstrate measured improvement in triage ordering vs. a flat-CVSS baseline on the same findings.

### In scope

- Black-box, passive scanning of web apps and REST APIs over HTTPS.
- Endpoint discovery via the 4-strategy crawler (HTML, JS source, wordlist, recursive depth-2).
- Misconfiguration checks across headers, cookies, CORS, TLS, REST-API surface, auth signals, and information disclosure.
- Automatic endpoint sensitivity classification (NLP) and response-body sensitivity signals.
- Template-based attack-chain correlation.
- CVSS v3.1 environmental scoring, results storage, dashboard, and PDF/JSON/HTML/CSV export.
- Scan history.

### Out of scope ("Won't — this time")

- Active/intrusive exploitation or any state-modifying payloads.
- SOAP, full GraphQL, gRPC, WebSocket, HTTP-only targets.
- Authenticated scanning and multi-user session testing (so BOLA/mass-assignment are best-effort heuristics only — see quality check).
- Multi-tenant accounts and RBAC (single analyst assumed unless justified).
- Runtime protection / WAF blocking.
- Dynamic, LLM-driven exploit generation.

### Assumptions, constraints, dependencies

- **Assumptions:** the analyst is authorised to scan the target; the target is reachable over HTTPS; most modern APIs under test are REST/JSON.
- **Constraints:** three-member team; six 2-week sprints; stack fixed as FastAPI / Next.js / httpx / Celery+Redis / PostgreSQL / sentence-transformers; 8GB-RAM server; must run black-box with no credentials.
- **Dependencies:** all-MiniLM-L6-v2 model (22MB, local); spaCy for PII; WeasyPrint for PDF; SSLyze recommended for TLS; legal vulnerable targets (Juice Shop, DVWA, VAmPI, crAPI) for evaluation; optional OpenAI/Anthropic key for the summary feature.

### Stakeholders and personas

**Stakeholders:** the three-student team (build + grade); the supervisor (feasibility, academic rigor); the FYP jury (novelty, results); future employers (portfolio signal); end users (analysts running scans). The university's FYP guidelines are a stakeholder artifact the team should attach — not provided here, listed as an open question.

**Personas** (supported by the tool's stated purpose):

1. **Security analyst / pentester** — scans a client site, needs findings ranked so the payment and auth endpoints surface above the brochure pages. Primary user; the whole context-aware premise serves this persona.
2. **Small-site developer/owner** — non-specialist, wants a plain prioritised report telling them what to fix first. Served by the dashboard, severity buckets, and plain-language report.
3. **Security student** — learning tool; wants to see why a finding scored as it did (the CVSS vector, the chain, the sensitivity class). Served by making the scoring transparent and recomputable.

## Functional requirements

Priority is MoSCoW. Acceptance criteria are abbreviated for the table; each should become a test. "Shall" statements are testable as written.

| ID | Requirement (The system shall…) | Rationale | Priority | Acceptance criteria |
|---|---|---|---|---|
| FR-01 | accept an HTTPS target URL and require the analyst to confirm they are authorised before scanning | Legal/ethical safeguard (Obj. in-scope) | Must | Scan refuses to start without an explicit authorisation checkbox/flag; non-HTTPS URLs rejected with a clear message |
| FR-02 | discover endpoints using HTML-link, JS-source, wordlist, and recursive (depth-2) strategies | Coverage beyond the seed URL | Must | On a seeded test app, discovers ≥ the known endpoint set; visited-set prevents re-crawl loops |
| FR-03 | run the defined misconfiguration checks on each discovered endpoint and record each failure as a finding | Core detection (Obj. 1) | Must | Each finding stores check id, endpoint, evidence, OWASP/CWE mapping |
| FR-04 | map each check to OWASP Top 10 / OWASP API Top 10 / CWE where applicable | Standards traceability | Must | Every check has a documented mapping or an explicit "none" |
| FR-05 | assign each endpoint a sensitivity class (Critical/High/Medium/Low) from its URL semantics, with no human input | Contribution 1 (Obj. 2) | Must | Class produced for every endpoint; ≥ 80% agreement vs. labelled test set |
| FR-06 | scan each response body for sensitivity signals (credentials, PII, financial, internal infra) and attach them to the finding | Contribution 3 | Must | Known signal strings in a test response are detected and recorded |
| FR-07 | compute, per finding, a CVSS v3.1 vector string and environmental score in 0–10 | Standards-anchored output (Obj. 3) | Must | Output is a parseable CVSS v3.1 vector; score recomputes to the same value in an independent calculator |
| FR-08 | derive context from sensitivity class and response signals via CVSS environmental metrics (not an out-of-range multiplier) | Fixes gap #1 | Must | No pre-cap score exceeds 10; the vector encodes the context (e.g. CR/IR) |
| FR-09 | correlate findings against the defined chain templates and emit a composite-scored chain when a template's members are all present | Contribution 2 | Must | A seeded finding set triggers the expected chain; composite > max member score |
| FR-10 | persist scans, endpoints, findings, headers, cookies, TLS info, and chains in PostgreSQL | Results storage, history | Must | Records survive restart; a scan is fully reconstructable from the DB |
| FR-11 | present a dashboard listing findings sorted by context-adjusted severity, filterable by severity and category | Triage value (Obj. 6), persona 1/2 | Must | Findings render newest/highest first; filters work |
| FR-12 | export the report as PDF, JSON, HTML, and CSV | Deliverable/sharing | Should | Each format generates and contains all findings + scores |
| FR-13 | show scan history and let the analyst re-open past scans | Persona 1 | Should | Past scans list with timestamp and target; re-open shows stored results |
| FR-14 | expose the scoring breakdown per finding (base vector, class, signals, chain) in the UI | Transparency, persona 3 | Should | Each finding can be expanded to show how its score was built |
| FR-15 | run scans asynchronously and let the dashboard poll live status | Responsiveness | Should | Submitting a scan returns immediately; status transitions queued→running→done are visible |
| FR-16 | record analyst false-positive corrections against findings | Future accuracy, evaluation | Could | A finding can be marked FP; stored in FEEDBACK table |
| FR-17 | generate an LLM executive summary when an API key is configured | Nice-to-have | Could | With key set, a summary is produced; with no key, scan still completes normally |
| FR-18 | let the analyst tune the wordlist / crawl depth per scan | Flexibility | Could | Settings accepted and applied; defaults used when unset |
| FR-19 | support authenticated scanning (session/token) | Would enable real BOLA/mass-assignment | Won't (this time) | — out of scope; documented as future work |

## Non-functional requirements

| ID | Requirement | Category | Priority | Acceptance criteria |
|---|---|---|---|---|
| NFR-01 | A scan of ≤ 100 endpoints shall complete within 10 minutes on the reference 8GB server | Performance | Must | Measured on reference target; time logged per scan |
| NFR-02 | The scanner shall fetch endpoints concurrently (async httpx) with a configurable concurrency cap | Performance | Should | Concurrency setting honoured; no unbounded fan-out |
| NFR-03 | Detection shall reach ≥ 80% recall and ≤ 15% false-positive rate on the ground-truth target set | Accuracy | Must | Measured precision/recall/FPR reported per target |
| NFR-04 | The tool shall validate and sanitise the target URL and refuse private/loopback/metadata addresses unless explicitly allowed (SSRF self-protection) | Security of the tool | Must | Requests to 169.254.169.254, localhost, RFC1918 blocked by default |
| NFR-05 | Stored findings and any captured response snippets shall be access-controlled and secrets (API keys, DB creds) kept in env/.env, never in code or logs | Security of the tool | Must | No secret in repo; .env.example only; captured credentials masked in storage |
| NFR-06 | The dashboard shall present findings understandable by a non-specialist (severity colour, plain description) | Usability | Should | Persona-2 user can identify top-3 fixes without help |
| NFR-07 | The scanner shall handle unreachable targets, timeouts, rate limits, and WAF blocks without crashing, recording the condition against the scan | Reliability | Must | Injected failures produce a graceful error state, not a crash |
| NFR-08 | New checks shall be addable without modifying the engine core (check registry/plugin pattern) | Maintainability | Should | A new check can be added in one file and auto-registered |
| NFR-09 | The whole system shall run via a single docker compose up for reproducible demo and grading | Portability/deploy | Must | Fresh machine → one command → working stack |
| NFR-10 | The tool shall scan only the authorised target and its in-scope hosts; it shall not follow off-host links into third-party domains | Legal/ethical | Must | Off-host URLs discovered but not scanned; logged as out-of-scope |
| NFR-11 | Scanning shall remain passive — no state-modifying requests (no POST/PUT/DELETE payloads that alter data) | Legal/ethical | Must | Request log shows only safe methods / non-mutating probes |
| NFR-12 | The codebase shall carry automated tests and run them in CI on every push | Maintainability/recruiter | Should | CI badge green; checks have unit tests |
| NFR-13 | Scan results for one target shall be reproducible run-to-run (deterministic checks; classifier stable) | Reliability | Should | Same target → same findings set (allowing for target changes) |

## Use cases and user stories

### Main use cases

**UC-1 — Run a context-aware scan**

- Actor: Security analyst. Precondition: authorised, target reachable over HTTPS.
- Main flow: analyst enters URL → confirms authorisation → submits → system discovers endpoints → classifies sensitivity → runs checks → scores with context → correlates chains → stores → dashboard shows ranked findings.
- Alternate/failure: non-HTTPS URL → rejected (FR-01). Target unreachable → scan ends in error state, partial results kept (NFR-07). Authorisation not confirmed → scan blocked.

**UC-2 — Review and triage findings**

- Actor: Analyst / developer. Precondition: a completed scan exists.
- Main flow: open scan → findings listed by context-adjusted severity → filter by severity/category → expand a finding to see CVSS vector, sensitivity class, response signals, and any chain.
- Alternate: mark a finding as false positive (FR-16) → recorded in FEEDBACK.

**UC-3 — Export a report**

- Actor: Analyst. Precondition: completed scan.
- Main flow: choose format (PDF/JSON/HTML/CSV) → system generates → analyst downloads.
- Failure: export generation error → message shown, other formats still available.

**UC-4 — Inspect an attack chain**

- Actor: Analyst / student. Precondition: a scan that triggered ≥ 1 chain.
- Main flow: open chain → see member findings, the template matched, and the composite score vs. individual scores.

**UC-5 — View scan history**

- Actor: Analyst. Main flow: open history → list of past scans → re-open one → stored results shown (FR-13).

### User stories (Must and Should)

| Story | Acceptance criteria |
|---|---|
| As an analyst, I want to enter a URL and confirm authorisation, so that I only scan targets I'm allowed to. | Scan blocked until authorisation confirmed; non-HTTPS rejected. |
| As an analyst, I want the tool to find endpoints I didn't list, so that coverage doesn't depend on my knowledge of the app. | Crawler finds endpoints beyond the seed, including JS-referenced API routes. |
| As an analyst, I want each endpoint's sensitivity judged automatically, so that payment/auth endpoints rank above public pages. | Every endpoint gets a class; ranking reflects it. |
| As an analyst, I want severity adjusted by what the response actually exposes, so that a leak of credentials outranks a cosmetic header gap. | Finding with credential signal scores higher than the same finding without. |
| As an analyst, I want a valid CVSS score per finding, so that I can defend the rating to a client. | Output is a recomputable CVSS v3.1 vector. |
| As an analyst, I want findings grouped into exploit chains, so that I see compound risk, not just isolated defects. | Chain shows its members and a composite score above any member. |
| As a developer, I want a prioritised, plain-language report, so that I know what to fix first without security expertise. | Report lists top fixes with clear descriptions and severity. |
| As an analyst, I want to export the report in common formats, so that I can share it with clients and teams. | PDF/JSON/HTML/CSV all generate with full content. |
| As a student, I want to see why a finding scored as it did, so that I learn the reasoning. | Expandable breakdown: base vector, class, signals, chain. |
| As an analyst, I want scans to run in the background with live status, so that I'm not blocked waiting. | Submit returns immediately; status updates visible. |
| As an analyst, I want past scans saved, so that I can compare or revisit. | History lists scans; re-open restores results. |

## Requirement quality check and traceability

### Flagged requirements from the original summary

| Original (from summary) | Problem | Corrected version |
|---|---|---|
| Final CVSS = (Base × | Not CVSS; produces 15.7 pre-cap; breaks the standard it claims to use | Encode context in CVSS v3.1 environmental metrics (CR/IR/AR, modified impact) so the vector stays valid and the score is 0–10 by construction (FR-07, FR-08) |
|  | Not CVSS; prod |  |
| Multiplier) + Bonus , cap 10 |  |  |
| "Context Multiplier: Critical ×2.0 … Low ×0.6" | Arbitrary constants, no derivation | Map sensitivity class → environmental Security Requirement (High/Medium/Low); these are defined CVSS inputs with defined effects |
| "Response Bonus: Credentials +3.5 (force CRITICAL)" | Additive fudge outside the model | Map a credential leak to an environmental Confidentiality Requirement = High (and/or a separate "sensitive data exposure" finding), not a flat +3.5 |
| "BOLA/IDOR", "Mass assignment", "Injection probe" as detected checks | Cannot be done reliably black-box without auth or state-changing payloads; conflicts with passive scope (NFR-11) | Relabel as heuristic/best-effort indicators (e.g. "IDOR candidate: numeric id in path, no auth challenge") or move to Won't-this-time |
| "GraphQL introspection" check vs. "GraphQL NOT targeted" | Direct contradiction | Keep a single introspection probe and note GraphQL is otherwise out of scope; remove from the API-coverage claim |
| "Expect-CT" absence as a header finding | Header deprecated since 2022, ignored by browsers | Flag Expect-CT present as a minor "deprecated header" finding, or drop |
| "58 security checks" headline | Breadth presented as the achievement | Keep the number but lead with measured accuracy; depth > count |
| Comparison table ★ "not in any existing public tool" | False (see Market context) | Qualify as "not in any open-source black-box tool" |

### Low-value / high-risk features

- **LLM executive summary (FR-17):** low value, reads as padding; keep strictly optional and off the critical path.
- **Token entropy / "OAuth2 open redirect" / "weak password reset token":** high false-positive risk black-box; keep only if a reliable signal exists, else demote.

### Traceability matrix

| Objective | Requirement IDs | Module/component | How tested |
|---|---|---|---|
| O1 Detect misconfigs (≥80% recall) | FR-02, FR-03, FR-04; NFR-03, NFR-07 | crawler.py, checks.py, engine.py | Ground-truth run on Juice Shop/DVWA/VAmPI/crAPI; precision/recall/FPR |
| O2 Auto sensitivity class (≥80%) | FR-05 | sensitivity.py | Agreement vs. hand-labelled endpoint set |
| O3 Valid CVSS v3.1 score | FR-07, FR-08, FR-14 | cvss.py | Vector parsed + recomputed in independent calculator |
| O4 Chain correlation, composite > member | FR-09 | chains.py | Seeded finding sets trigger expected chains; score comparison |
| O5 Scan time ≤ 10 min | NFR-01, NFR-02; FR-15 | engine.py, tasks.py (Celery) | Timed scans on reference target |
| O6 Better triage ordering vs flat CVSS | FR-05, FR-06, FR-08, FR-11 | sensitivity.py, body_classifier.py, cvss.py, frontend | Ranking comparison: context-adjusted vs base-only order on same findings |
| Legal/ethical safeguards | FR-01; NFR-04, NFR-05, NFR-10, NFR-11 | routes/scan.py, engine.py | Authorisation gate test; SSRF block test; off-host + passive-only checks |
| Reproducible demo | NFR-09, NFR-12 | docker-compose, CI | Fresh-machine one-command bring-up; CI run |

## Development plan — architecture and build order

The existing stack and module layout are kept; no rewrite is recommended. The one architectural change is where context enters scoring (into CVSS environmental metrics, not a bolt-on multiplier) — a change inside `cvss.py`, not to the architecture.

### Architecture review against requirements

The summary's layering (Next.js → FastAPI → Celery → scanner pipeline → PostgreSQL) is sound and maps cleanly to the requirements. Components and responsibilities:

- **Frontend (Next.js):** scan form, live-polling results, finding drill-down (FR-11, FR-14, FR-15).
- **API (FastAPI):** scan submit, results, history, export, optional AI chat (FR-01, FR-12, FR-13).
- **Task queue (Celery+Redis):** async scan orchestration (FR-15, NFR-01). Justify or simplify — see Open questions.
- **Scanner (pure Python):** engine (httpx), crawler, checks, sensitivity, chains, body_classifier, cvss, reports — the heart of FR-02–FR-09.
- **Database (PostgreSQL + SQLAlchemy):** the 10 tables (FR-10).

**Mismatches to fix:** (1) scoring lives in `cvss.py` but the formula must change to environmental-metric based (gap #1). (2) SSRF self-protection (NFR-04) has no home in the module list — add input validation at the engine boundary. (3) No test module/CI is shown (NFR-12) — add `tests/` and a CI config.

### Data model outline (entities, key fields)

- **SCAN** — id, target_url, status, started_at, finished_at, authorised_by/flag, settings.
- **ENDPOINT** — id, scan_id, url, method, sensitivity_class, discovery_strategy.
- **FINDING** — id, endpoint_id, check_id, owasp/cwe_map, cvss_vector, base_score, final_score, severity_bucket, evidence.
- **HEADER / COOKIE / TLS_INFO** — id, endpoint_id, captured attributes.
- **ATTACK_CHAIN** — id, scan_id, template_id, composite_score.
- **CHAIN_FINDING** — chain_id, finding_id (M:N junction).
- **AI_INSIGHT** — id, scan_id, summary_text.
- **FEEDBACK** — id, finding_id, is_false_positive, note (FR-16).

### Module build order

Build the thinnest thing that runs end-to-end first, then widen. Dependencies: engine → crawler → checks → (sensitivity, body_classifier) → cvss → chains; the platform (API, DB, frontend) can grow in parallel once the DB schema exists.

**Minimum working end-to-end slice (build this first, by end of Sprint 2):** one HTTPS URL in → engine fetches it → one check runs (missing HSTS) → one sensitivity class assigned → one CVSS environmental score computed → one finding stored in PostgreSQL → shown on the dashboard. Once this vertical slice works, every new check, signal, and chain is an increment on a proven path.

**Then widen, in this order:** (1) the full check set, grouped by category, each with a test; (2) response-body signals; (3) chain correlation; (4) export formats; (5) history, feedback, optional LLM summary. Evaluation harness is built alongside (1), not after.

### Can be built in parallel

- **Member A (scanner):** engine, crawler, checks — the critical path.
- **Member B (intelligence):** sensitivity classifier + labelled dataset, body_classifier, cvss environmental logic, chains. Depends on the FINDING shape, not on every check existing.
- **Member C (platform):** FastAPI routes, DB schema + SQLAlchemy models, Celery wiring, Next.js dashboard, Docker, CI. Can start on day one from the schema.

scan pipeline: 3 context steps feed one CVSS score The left column is the commodity scanning path; the dashed box is where CAWASMA's three contributions live, all feeding one CVSS environmental score rather than three separate out-of-model adjustments.

## Milestones and sprint plan

This keeps the team's six-sprint Scrum structure but moves evaluation forward and inserts the formula fix early. Owners are by role: **A** scanner, **B** intelligence, **C** platform. Effort is indicative for a 3-person team.

| Sprint | Milestone | Key tasks (owner) | Deliverable |
|---|---|---|---|
| 1 | Foundations + decisions locked | Lit review finalised, novelty claim rewritten, CVSS-environmental scoring designed on paper (B); architecture + 10-table schema (C); crawler skeleton + engine fetch (A); Docker + repo + CI skeleton (C) | Signed-off scope, schema, scoring design doc, repo scaffolding |
| 2 | End-to-end vertical slice + eval harness | 1 check (HSTS) → 1 class → 1 env score → stored → shown (A+B+C); Juice Shop/DVWA/VAmPI/crAPI in Docker with ground-truth list (A); hand-label 150+ endpoints (B) | Working thin scan; eval harness producing first precision/recall numbers |
| 3 | Full check set + context layer | Remaining checks by category, each with a unit test (A); sensitivity classifier trained + measured (B); body_classifier + chains + env-score integration (B); results API + dashboard list (C) | All checks running; classifier accuracy number; chain demo |
| 4 | Platform complete | Celery async + live status (C); drill-down UI showing score breakdown (C); export PDF/JSON/HTML/CSV (A/C); SSRF + passive-only guards (A) | Full app; one-command demo; reports export |
| 5 | Measured evaluation + hardening | Full precision/recall/FPR vs ZAP + Nuclei baselines on all targets (A+B); false-positive triage + fixes; feedback capture (C); ranking-improvement experiment vs flat CVSS (B) | Evaluation results table; bug fixes; metrics ready for the jury |
| 6 | Polish + buffer | README with results table + demo GIF (C); final bug fixes; reproducibility check on a clean machine (all) | Release-quality repo; measured, defensible demo |

(Report writing, slides, and viva prep are deliverables of Sprint 6 in the original plan but are out of scope for this document, as requested.)

**Definition of Done (per task):** code reviewed by one other member; unit test(s) written and passing; relevant docs/README updated; merged to main via PR with green CI. A check is not "done" until it has a test proving it fires on a known-vulnerable target and stays silent on a clean one.

## Testing and evaluation strategy

Evaluation is the single biggest differentiator between a passing FYP and a strong one here. It must run continuously from Sprint 2, not as a Sprint-5 afterthought.

### Unit and integration testing

- **Per check:** a pytest unit test with two fixtures — a response that should trigger the check and one that should not — asserting fire/no-fire. This is also the Definition-of-Done gate.
- **Scanner integration:** run the full pipeline against a locally-hosted deliberately-vulnerable app in CI and assert the finding set matches a stored expectation.
- **Scoring:** property tests that no final score exceeds 10 and every emitted CVSS vector parses and recomputes to the stored score.
- **Classifier:** evaluation (not a pass/fail test) reporting accuracy/confusion matrix against the labelled endpoint set.
- **API:** FastAPI route tests (submit, poll, results, export).

### Evaluation against legal vulnerable targets

Stand up these in Docker with a documented ground-truth finding list:

| Target | Why | What it exercises |
|---|---|---|
| OWASP Juice Shop | Modern JS app, rich misconfigs | Crawler JS strategy, headers, cookies, info disclosure |
| DVWA | Classic, well-understood | Baseline header/TLS/config checks |
| VAmPI | Deliberately vulnerable REST API | API checks, BOLA candidates, auth signals |
| crAPI | Realistic API with BOLA/mass-assignment | API Top 10 coverage, sensitivity classification |

For each: compute **precision, recall, and false-positive rate** against the ground truth. Report per-target and overall. This produces the numbers the jury needs (Objectives 1–2, NFR-03).

### Baseline comparison

Run **ZAP** (passive/baseline scan) and **Nuclei** (misconfiguration + exposure templates) against the same targets. Compare on: findings count, overlap with CAWASMA, false positives, and — the key differentiator — triage ordering. CAWASMA's claim isn't "finds more"; it's "ranks better." Show that a context-aware ordering surfaces the payment/auth findings above cosmetic ones where ZAP's flat list doesn't.

### What the jury needs to see (collect during development)

- A precision/recall/FPR table per target, CAWASMA vs ZAP vs Nuclei.
- Classifier accuracy + confusion matrix on the labelled set.
- A worked scoring example: same finding on a sensitive vs. public endpoint, showing the vector and score difference (the project's whole thesis in one slide).
- At least one triggered attack chain with composite vs. member scores.
- A before/after ranking comparison (context-aware vs flat CVSS) on one real target.

Log every scan's metrics to the DB from Sprint 2 so these tables build themselves over the project rather than being scrambled together at the end.

## Engineering practices and risk register

### Engineering practices (recruiter-visible)

Recommend only what fits a 3-person, 12-week effort. All of this is feasible and each is a recruiter signal:

- **Git + branching:** trunk-based with short-lived feature branches and PRs; protect `main`.
- **Code review:** one reviewer per PR; the DoD gate.
- **Linting/formatting:** `ruff` + `black` for Python, ESLint/Prettier for the frontend; run in CI.
- **Automated tests:** pytest for scanner/API, run on every push.
- **CI pipeline:** GitHub Actions — lint, test, build Docker image. A green badge in the README is worth a paragraph of claims.
- **Containerisation:** `docker compose` brings up frontend, API, worker, Redis, Postgres, and the vulnerable test targets. One command to demo = the top reproducibility signal (NFR-09).
- **README + setup docs:** value statement in the first line, the evaluation table, a demo GIF, architecture diagram, quickstart.
- **Clean structure:** the existing module layout is already clean; keep checks in a registry so adding one is a one-file change (NFR-08).

Don't over-invest in: Kubernetes, microservice splitting, multi-env deploy pipelines, or heavy observability — out of scope for an FYP and a time sink.

### Risk register

| Risk | Likelihood | Impact | Mitigation | Fallback |
|---|---|---|---|---|
| Scoring formula questioned / indefensible | High (as written) | High | Rebuild on CVSS v3.1 environmental metrics in Sprint 1 | Document it as a transparent heuristic clearly separate from the base CVSS, never as "CVSS" |
| NLP classifier underperforms (< target accuracy) | Medium | High | Hand-labelled set early; tune anchor phrases; fall back to a hybrid regex+embedding | Ship a rules-based classifier with embeddings as a documented enhancement; report honest accuracy |
| Black-box API checks (BOLA, mass assign) give false positives | High | Medium | Relabel as "candidates", require corroborating signals | Move to "Won't this time"; present as future work with auth |
| Evaluation left too late, bad numbers with no time to fix | Medium | High | Eval harness in Sprint 2, metrics logged continuously | Narrow target set to Juice Shop + VAmPI; report those thoroughly |
| Novelty claim challenged by jury | Medium | High | Rewrite to "open-source black-box combination"; cite commercial prior art | Lean on the reproducible-evaluation contribution, which stands on its own |
| Crawler misses JS-rendered routes (SPA) | Medium | Medium | JS-source regex strategy; document the SPA limitation | State coverage limits explicitly; test on a known endpoint list |
| Scope creep from 58 checks | Medium | Medium | Freeze the list after Sprint 1; depth over additions | Cut to ~30 well-tested checks; quality defends better than count |
| Celery/Redis integration eats time | Low–Med | Medium | Decide early (see Open questions) | Use FastAPI BackgroundTasks or a simple thread/queue; async is not the thesis |
| Team member availability (exams, etc.) | Medium | Medium | Parallelisable ownership; vertical slice de-risks integration | Buffer in Sprint 6; Could-items are first to drop |

## Open questions

Decisions the team or supervisor must make, each with a recommended option and why. Items 1–4 are also missing inputs that the original prompt asked for but the summary didn't provide.

1. **FYP stage and next deadline?** Not in the summary. Recommend: confirm which sprint you're in now — the whole plan's urgency (especially moving evaluation to Sprint 2) depends on time remaining. If past Sprint 3, prioritise the scoring fix and evaluation harness over new checks.
2. **Team skills split?** Three members named only as a count. Recommend: assign the scanner/intelligence/platform roles explicitly by who's strongest in Python-async vs ML vs full-stack; the parallel plan assumes this.
3. **Fixed constraints beyond the stack?** Supervisor requirements, hardware, department FYP rubric. Recommend: attach the department FYP guidelines — grading weight (the CLO2/CLO3 split suggests demo and implementation are 40% each) should shape where effort goes.
4. **Molnár & Bilicki 2022 citation — real?** Could not verify (see Market context). Recommend: produce the DOI or drop it; don't cite an unverifiable source in an FYP report. A verified substitute scanner-comparison paper exists if you need the "no scanner is context-aware" point.
5. **Scoring: CVSS v3.1 environmental vs v4.0?** The summary uses v3.1. v4.0 exists and has richer environmental metrics, but NVD still commonly publishes v3.1 and it's simpler. Recommend: **stay on v3.1 environmental** — fixing the formula within a standard you already chose is lower-risk than switching. Mention v4.0 awareness in the report.
6. **Async: Celery+Redis or simpler?** Recommend: **keep it only if** you can show it earns its place (concurrent multi-scan). For single-user scans, FastAPI BackgroundTasks is enough and removes two services from the demo. Decide in Sprint 1.
7. **Check count: 58 or fewer?** Recommend: **freeze a realistic subset** after Sprint 1. Keep the reliably-black-box checks (headers, cookies, CORS, TLS, info disclosure, versioning) at full depth; demote the auth-dependent ones to candidates. Better to defend 30 tested checks than claim 58 shallow ones.
8. **LLM executive-summary feature — keep?** Recommend: **keep optional and off the** **critical path**, or cut if time is tight. It adds little to the thesis and risks reading as feature-padding to a recruiter.
9. **Chain templates — how derived?** Five hand-written templates with fixed composite scores. Recommend: document the reasoning for each (why these findings chain, why that composite), or a jury will call them arbitrary. Even a short justification per template fixes this.
