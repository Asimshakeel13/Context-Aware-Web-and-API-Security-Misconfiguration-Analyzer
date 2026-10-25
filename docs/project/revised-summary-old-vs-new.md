# CAWASMA — Revised Project Summary (old vs new)

> Imported from the team PDF `CAWASMA — Revised Project Summary (old vs new).pdf` (local copy in `pdf/`, not committed). Converted to Markdown on 2026-10-25; tables and lists are kept, page headers dropped.

Oct 14, 2026 · @Shoaib Younas

This restates CAWASMA with the review changes folded in. The table below carries the full idea, original against revised, so nothing is lost.

## Revised positioning

CAWASMA (Context-Aware Web and API Security Misconfiguration Analyzer) is a black-box HTTPS scanner for web apps and REST APIs that fixes the flat-severity problem of existing scanners: it infers each endpoint's sensitivity, reads what the response actually exposes, correlates findings into exploit chains, and folds all three into a single, standards-valid CVSS v3.1 environmental score — so the payment and auth endpoints rank above the brochure pages automatically. The honest contribution is being the first **open-source, zero-config, black-box** tool to combine these into a recomputable CVSS score and prove it against ground truth — not "the first tool to do any of this," since commercial API-security tools already do the parts. The severity maths now stays inside CVSS (no out-of-model multipliers), evaluation runs from Sprint 2 against known-vulnerable targets with a ZAP/Nuclei baseline, and the checks that can't be done reliably black-box are labelled as best-effort candidates rather than claimed as detections.

## Old vs new — the full idea

| Aspect | Original (old) | Revised (new) |
|---|---|---|
| Name / type | CAWASMA — black-box HTTPS misconfiguration scanner, BS-CS FYP, FAST-NUCES, 3 members | Unchanged |
| One-line pitch | Scans a URL, runs 58 checks, scores each finding with context-aware CVSS, produces a prioritised report | Unchanged — this is still the core and it's good |
| Core problem | Existing scanners score statically: missing HSTS on /public/about = missing HSTS on /api/payment/checkout; analysts get flat lists | Unchanged — real, well-stated, backed by Wunder et al. (68% CVSS inconsistency) |
| Contribution 1: NLP endpoint sensitivity | URL path → sentence-transformer embedding → cosine similarity → Critical/High/Medium/Low, zero human input | Kept, but reframed: novel as an open, zero-config approach, not "first ever" — Cequence/Traceable already classify endpoints from the URL with ML |
| Contribution 2: attack-chain correlation | 5 pre-defined chain templates; when members present → composite CVSS | Kept, renamed "template-based chain correlation"; each template now needs a documented justification; Escape/XBOW already do dynamic chaining, so claim the simpler template approach honestly |
| Contribution 3: response-body adjustment | Scan response for credentials/PII/financial/internal → add bonus to CVSS | Kept, but the "bonus" is replaced by CVSS environmental inputs (see scoring); Akto/Traceable already flag response PII |
| Novelty claim | "No existing public tool infers sensitivity, chains findings, or adjusts on response body" | "First open-source black-box tool to combine all three into a recomputable CVSS environmental score, evaluated against ground truth." Commercial prior art named |
| Scoring formula | Final = min(10, (Base × | Replaced. Context enters via CVSS v3.1 environmental metrics (Confidentiality/Integrity Requirement, modified impacts). Output stays a valid CVSS vector, score 0–10 by construction, recomputable by a third party |
|  |  | Replaced. C |
|  | Multiplier) + Bonus) ; multipliers ×2.0…×0.6; bonuses +3.5 etc.; pre-cap scores like 15.7 |  |
| Sensitivity → score link | Class multiplies the base (×2.0 Critical … ×0.6 Low) | Class maps to CVSS Security Requirement (High/Med/Low) — a defined CVSS input with a defined effect |
| Credential leak → score | "+3.5, force CRITICAL override" | Maps to environmental Confidentiality Requirement = High and/or a distinct sensitive-data-exposure finding |
| 58 checks | 58 checks across 7 categories, presented as the headline achievement | Freeze a realistic subset after Sprint 1; lead with measured accuracy, not count. Depth over breadth |
| BOLA / mass assignment / injection probe | Listed as detected API checks | Relabelled as heuristic candidates (e.g. "IDOR candidate: numeric id, no auth challenge") or moved to future work — can't be done reliably black-box without auth/payloads |
| GraphQL | "NOT targeted" in scope, but "GraphQL introspection enabled" is a listed check | Contradiction resolved: keep a single introspection probe, drop GraphQL from the API-coverage claim |
| Expect-CT | Flagged as a missing header (check #12) | Fixed: Expect-CT is deprecated (2022), ignored by browsers — flag it as present/deprecated, or drop. Flagging its absence is wrong |
| Comparison-table ★ claims | 4 features marked "not present in any existing public tool" | Qualified to "not in any open-source black-box tool" |
| Scope (passive black-box) | Passive, no state-modifying payloads, REST-only, HTTPS-only | Unchanged — defensible and correctly justified |
| Evaluation | Testing + evaluation experiments in Sprint 5 | Moved to Sprint 2. Juice Shop/DVWA/VAmPI/crAPI in Docker with ground truth; precision/recall/FPR logged continuously |
| NLP test set | Not mentioned | Added: hand-label 150–300 real endpoint paths so Contribution 1 has an accuracy number |
| Baseline comparison | Not mentioned | Added: compare against ZAP + Nuclei on the same targets; key metric is triage ordering, not count |
| Async (Celery + Redis) | Celery + Redis for background scanning | Keep only if it earns its place (concurrent multi-scan); else FastAPI BackgroundTasks — async is not the thesis |
| LLM executive summary | Optional OpenAI/Anthropic feature | Keep optional and off the critical path, or cut — reads as feature-padding |
| Tech stack | Next.js, FastAPI, PostgreSQL, httpx, Celery+Redis, sentence-transformers, spaCy, WeasyPrint | Unchanged (SSLyze recommended for the TLS checks instead of hand-rolling) |
| Engineering practices | Not specified | Added as deliverables: tests, CI, ruff / black , one-command docker compose , README with results table + demo GIF |
| Cited papers | Wunder 2024, Golmohammadi 2023, Ahmadi Mehri 2022, Molnár & Bilicki 2022 | First three verified and correct. Molnár & Bilicki 2022 unverified — produce the DOI or drop it |

## What stayed the same

Most of the project is kept as-is — the changes sharpen it, they don't rebuild it:

- The whole premise (context-aware severity for black-box misconfiguration scanning) and the three contributions as concepts.
- The passive, black-box, REST-only, HTTPS-only scope.
- The architecture (Next.js → FastAPI → scanner pipeline → PostgreSQL) and the 10-table schema.
- The tech stack and module layout ( `engine`, `crawler`, `checks`, `sensitivity`, `chains`, `body_classifier`, `cvss`, `reports`).
- The crawler's 4 discovery strategies.
- Agile Scrum, six 2-week sprints, 3-member team.

The net effect: same project, but the novelty claim is defensible, the scoring stays valid CVSS, and there are real numbers to show the jury.
