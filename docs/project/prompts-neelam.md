# CAWASMA — Neelam's Claude Code Prompts

> Imported from the team PDF `CAWASMA — Neelam's Claude Code Prompts.pdf` (local copy in `pdf/`, not committed). Converted to Markdown on 2026-10-25; tables and lists are kept, page headers dropped.

Oct 23, 2026 · @Shoaib Younas

## How to use these prompts

Run one prompt per fresh Claude Code session, in order, and commit before moving to the next. Build against the mock from Sprint 1 so you never wait on the backend.

Team rules (same for all three of us):

- **Start after Atta's Prompt 1.** It creates the shared repo, `CLAUDE.md` and `docker-compose.yml`. Your app lives in `frontend/`.
- **One branch per prompt**, e.g. `neelam/p02-api-client`, merged by pull request. Never push straight to `main`.
- **Stay in your lane.** If Claude Code wants to change backend files, it must stop and tell you. You raise it with Atta.
- **Contracts change only by agreement.** `docs/api-contract.md` and `docs/openapi.json` are Atta's; if the frontend needs a field that isn't there, ask him rather than inventing it.
- **Shared DevOps:** you and Atta co-own `docker-compose.yml` and CI. Pair on Prompt 1 and tell him when you change either.
- **Use plan mode** (Shift+Tab) for Prompts 2, 6 and 7. Read the plan before letting it build.
- Text in `[square brackets]` is a placeholder to fill in before pasting.

## Run order

Pair with Atta on his Prompt 1, then start yours once it is merged; after that we all work in parallel. Thanks to mock mode, most of your prompts don't wait on anyone.

**What you wait for**

| Your prompt | Waits for | If it's late |
|---|---|---|
| 1 | Atta 1 (repo + compose slot) | — |
| 2 (API client) | Atta 3: API contract + openapi.json | Hand-write temporary types from the FINDING shape |
| 3–4 | Nothing | — |
| 5 (real API) | Atta 7: vertical slice | Keep building on the mock |
| 6–7 (results, drill-down) | Nothing (mock) | Re-check fields when Atta 8 updates the contract |
| 8 (live status, history) | Atta 9: Celery + live status | Build history first; polling still works |
| 9 (export, polish) | Atta 9: export endpoint | Do the polish and tests first |
| 10 (eval page, README) | Asim 10: final results CSVs | Build the page on sample CSVs |

**Who waits for you**

Nobody is blocked by your prompts, but the Sprint 2 milestone needs your Prompt 5: one scored finding visible on the dashboard. The final reproducibility check (your 10, Atta's 10) is done together.

Before every prompt, pull the latest `main`. Merge small pull requests often to avoid conflicts in `CLAUDE.md`, `docker-compose.yml` and CI.

## Sprint 1: scaffold, API client, design system, new-scan page

By the end of Sprint 1 the scan form and a results stub should work against mock data.

### Prompt 1: Next.js scaffold, Docker and CI

```text
I'm Neelam, frontend & shared-DevOps owner on CAWASMA, a context-aware web
security scanner (final-year project, team of 3). Read CLAUDE.md and docs/
first — they hold the team plan and the shared contracts.
Set up the frontend:
1. A Next.js app (App Router, TypeScript strict, Tailwind CSS, shadcn/ui)
in frontend/. ESLint + Prettier, Vitest + React Testing Library, and
Playwright for end-to-end tests.
2. Add a "Neelam — frontend" section to CLAUDE.md: files I own, how to run
the dev server and tests. Do not change the other sections.
3. A production Dockerfile (multi-stage, standalone output, non-root user).
4. Add a frontend service to docker-compose.yml in the slot Atta left, with
NEXT_PUBLIC_API_URL pointing at the api service. Change nothing else in
that file; tell me exactly what you added so I can show Atta.
5. Add a frontend job to the existing GitHub Actions CI: lint, type-check,
unit tests, build. Don't touch the backend jobs.
6. Confirm `docker compose up` brings up the frontend at localhost:3000
alongside the API.
```

### Prompt 2: Typed API client and mock mode

```text
Read CLAUDE.md and docs/api-contract.md. Build the API layer.
1. Generate TypeScript types from docs/openapi.json with openapi-typescript
(npm run gen:api). If openapi.json doesn't exist yet, write the types by
hand from docs/api-contract.md and the FINDING shape: id, endpoint_id,
check_id, owasp_map, cwe_map, cvss_vector, base_score, final_score,
severity_bucket, evidence — and mark them TEMPORARY in a comment.
2. A small typed client in frontend/lib/api.ts: createScan(),
getResults(id), getExportUrl(id, format). Consistent error handling
(network error, 4xx, 5xx) returned as typed results, not thrown strings.
3. Mock mode with MSW: when NEXT_PUBLIC_USE_MOCK=true, all calls are served
from fixtures copied from the examples in docs/api-contract.md. Mock a
scan
that moves queued -> running -> done over ~10 seconds, and include
findings of every severity, at least one with a chain and body signals.
4. TanStack Query for data fetching, set up with sensible defaults.
5. Tests for the client against the mocks.
```

### Prompt 3: App shell and severity design system

```text
Read CLAUDE.md. Build the app shell and the shared UI pieces.
1. Layout: top nav (New scan, History), page container, footer showing
the API mode (mock / live) so we never demo the mock by mistake.
2. Severity tokens in one place: Critical, High, Medium, Low, None, each
with a colour, icon and label. Never rely on colour alone (WCAG AA
contrast, readable for colour-blind users). Light and dark mode.
3. Shared components: SeverityBadge, ScoreDisplay (shows base -> final
score with an arrow when they differ), StatusPill (queued / running /
done / failed), EmptyState, ErrorState, LoadingSkeleton.
4. A /dev/components page showing every component in every state, so I can
check them in one place.
5. Component tests for SeverityBadge and ScoreDisplay.
```

### Prompt 4: New-scan page

```text
Read CLAUDE.md and docs/api-contract.md. Build the new-scan page at /.
1. Target URL input with validation (http/https only, shows a clear error).
2. Authorisation confirmation: a required checkbox "I own this target or
have written permission to test it." The Start button stays disabled until
it is ticked, and the flag is sent in the request body so the backend can
enforce it too. [match the exact field name in the API contract]
3. Advanced options (collapsed by default): crawl depth (1–2), use
wordlist (on/off), passive-only mode (on/off) with a one-line
explanation of each.
4. On submit: POST /api/scan, show a queued state, then redirect to
/scans/[id]. Handle errors inline (invalid URL, server down).
5. Tests: button disabled without authorisation, validation messages,
successful submit redirects (against the mock).
```

## Sprints 2–3: real API, results page, finding drill-down

Prompt 5 is your half of the Sprint 2 milestone: one URL produces one scored finding on the dashboard.

### Prompt 5: Wire to the real API (Sprint 2)

```text
Read CLAUDE.md. Atta's vertical slice is live: POST /api/scan and
GET /api/results/{id} return real data.
1. Regenerate the API types from the latest docs/openapi.json and fix
anything that no longer matches. Remove the TEMPORARY hand-written types.
List every difference between the real API and our mock fixtures, and
update the fixtures so mock and real stay identical in shape.
2. Build /scans/[id]: poll GET /api/results/{id} every 2 seconds while
status is queued/running, stop when done/failed. Show status, target,
and a basic list of findings (check_id, severity badge, final score,
endpoint).
3. Handle: scan not found (404), scan failed (show the error message),
API unreachable (retry with backoff, then a clear message).
4. A Playwright end-to-end test against the real stack: start a scan of
the test target Atta uses, wait for done, see the HSTS finding.
[ask Atta for the test target URL]
5. Tell me if any field the UI needs is missing from the API, so I can ask
Atta — don't change backend code.
```

### Prompt 6: Full results page (Sprint 3)

```text
Read CLAUDE.md and docs/api-contract.md. Build out /scans/[id].
1. Summary header: target, scan time, counts per severity, and how many
findings moved up a severity because of context (final vs base bucket).
2. Ranked findings list, ordered by final_score (context-adjusted), with
severity colour bands. A toggle "rank by base score" so the viewer can see
how the ranking changes — this shows the project's main idea.
3. Filters: severity (multi-select), category, OWASP id, "only findings in
chains", text search on endpoint. Filters live in the URL query so a
filtered view can be shared and reloaded.
4. Server-side pagination if the API supports it, otherwise virtualised
rendering so 500+ findings stay smooth.
5. Empty, loading and error states for each part.
6. Tests for filtering, sorting and the base/final toggle.
```

### Prompt 7: Finding drill-down — the score breakdown (Sprint 3)

```text
Read CLAUDE.md, docs/cvss-mapping.md and docs/chain-templates.md. Build the
expandable finding detail. This is the project's selling point: a viewer must
understand WHY a finding scored as it did in under 10 seconds.
For each finding show:
1. Score story: base score -> final score, with the reason in one line,
e.g. "Raised from 5.3 to 7.1 because the endpoint is classified as
Authentication and the response contains credentials."
2. CVSS vector breakdown: parse the vector string into a readable table of
base metrics and environmental metrics (CR/IR/AR), highlighting the
environmental ones that changed. Link to the FIRST CVSS v3.1 calculator
pre-filled with the vector so anyone can verify the score.
3. Context: sensitivity class (with a short definition), body signals
found (with redacted evidence), chain membership with links to the other
findings in the chain.
4. Standards: OWASP and CWE ids linking to their official pages.
5. Evidence: request/response snippet in a scrollable code block.
Keyboard accessible, works on a phone screen. Tests: vector parsing
(including a malformed vector), the score-story sentence, chain links.
```

## Sprints 4–6: live status, history, export, demo

These finish the product and get it demo-ready.

### Prompt 8: Live status and history page (Sprint 4)

```text
Read CLAUDE.md and docs/api-contract.md. Atta has moved scans to Celery and
added live status [SSE / WebSocket / status endpoint — check the contract].
1. Replace simple polling on /scans/[id] with the live status mechanism Atta
chose. Show stage progress (crawling -> checking -> scoring) with a
progress bar, elapsed time, and endpoints/findings found so far.
Fall back to polling automatically if the live connection drops.
2. A Cancel scan button if the API supports cancellation.
3. /history page: past scans in a table (timestamp, target, status,
counts per severity, duration), newest first, with search by target and
pagination. Clicking a row reopens the stored results.
4. Re-scan button on a past scan (pre-fills the new-scan form; the user
must tick the authorisation box again).
5. Tests: live updates, fallback to polling, history navigation.
```

### Prompt 9: Export UI, polish and end-to-end tests (Sprints 4–5)

```text
Read CLAUDE.md and docs/api-contract.md.
1. Export menu on the results page: PDF, JSON, HTML, CSV via
GET /api/results/{id}/export?format=... Show progress while a PDF is
generated, a clear error if it fails, and a sensible file name
(cawasma-<target>-<date>.<ext>). Disable export until the scan is done.
2. Usability pass on every page: consistent spacing, focus states, keyboard
navigation, screen-reader labels, responsive down to phone width. Run
axe accessibility checks in the Playwright tests and fix what they find.
3. Performance: check bundle size, lazy-load heavy parts (drill-down,
charts), and make sure the results page stays smooth with 500 findings.
4. Full Playwright suite: new scan -> live status -> results -> filter ->
drill-down -> export, for one real eval target. Add it to CI.
5. Give me a list of rough edges you noticed but didn't fix.
```

### Prompt 10: Evaluation view, README and demo (Sprints 5–6)

```text
Read CLAUDE.md and eval/results/final/ (Asim's evaluation output).
1. An /evaluation page for the demo, built from Asim's CSVs (copied in at
build time, not hand-typed):
- CAWASMA vs ZAP vs Nuclei: precision, recall, false-positive rate, scan
time (grouped bar charts)
- the before/after ranking experiment: the same findings ranked by base
score vs final score, side by side, with the movement highlighted
- classifier accuracy and confusion matrix
Each chart with a one-line takeaway. [confirm the CSV columns with Asim]
2. README (with the team): what CAWASMA is, the context-aware scoring idea
in 3 sentences, screenshots, one-command setup, how to run a scan, how
to run the evaluation, team and roles.
3. A Playwright script that records the demo flow as a video and captures
screenshots for the README and report, so they're easy to regenerate.
4. Reproducibility check with Atta: fresh clone -> docker compose up on a
clean machine -> run a scan in the UI. Fix any frontend issue found and
list any backend issue for Atta.
5. Final check against my definition of done: enter URL, confirm
authorisation, watch the scan run, read the ranked report, expand a
finding to see why it scored as it did, view history, export — against
the real backend. Report pass/fail per item.
```
