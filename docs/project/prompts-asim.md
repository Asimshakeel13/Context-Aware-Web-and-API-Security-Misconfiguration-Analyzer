# CAWASMA — Asim's Claude Code Prompts

> Imported from the team PDF `CAWASMA — Asim's Claude Code Prompts.pdf` (local copy in `pdf/`, not committed). Converted to Markdown on 2026-10-25; tables and lists are kept, page headers dropped.

Oct 23, 2026 · @Shoaib Younas

## How to use these prompts

Run one prompt per fresh Claude Code session, in order, and commit before moving to the next. Prompts 2–4 block Atta, so finish them in Sprint 1.

Team rules (same for all three of us):

- **Start after Atta's Prompt 1.** It creates the shared repo and `CLAUDE.md`. Your files live in `backend/app/ml/`, `config/`, `checks.yaml`, `eval/` and `docs/`.
- **One branch per prompt**, e.g. `asim/p02-check-specs`, merged by pull request. Never push straight to `main`.
- **Stay in your lane.** If Claude Code wants to change Atta's or Neelam's files, it must stop and tell you. You raise it with them.
- **Contracts change only by agreement.** Anything in `docs/api-contract.md`, `docs/check-spec-format.md` or `docs/cvss-mapping-contract.md` is changed only after all three agree.
- **Use plan mode** (Shift+Tab) for Prompts 2, 3, 6 and 8. Read the plan before letting it build.
- **You own the security judgement.** Claude Code drafts specs, vectors and mappings; you check every one before it is committed. The jury will ask you to defend them.
- Text in `[square brackets]` is a placeholder to fill in before pasting.

## Run order

Start your Prompt 1 once Atta's Prompt 1 is merged; after that we all work in parallel. Your Prompts 2–4 are what Atta needs most, so finish them in Sprint 1.

**What you wait for**

| Your prompt | Waits for | If it's late |
|---|---|---|
| 1 | Atta 1 (repo exists) | — |
| 2 (check specs) | Atta 3: check-spec format + validator | Draft the specs now; validate once it lands |
| 3 (CVSS mapping) | Atta 3: mapping contract | Design the table now; fit the file format later |
| 4 (chains) | Your own 2 and 3 | — |
| 5 (eval targets) | Atta 4: ALLOWED_INTERNAL_HOSTS | Stand up the targets and ground truth anyway |
| 6–7 (classifiers) | Your own 5 (labelled endpoints, sample responses) | — |
| 8 (evaluation) | Atta 7, ideally Atta 8 | Build the ZAP/Nuclei baselines first |
| 9 (security review) | Atta 9 | Review the SSRF guard (Atta 4) first |
| 10 (final results) | Your own 8 and 9 | — |

**Who waits for you**

| Your prompt | Unblocks |
|---|---|
| 2, 3, 4, 6, 7 | Atta 8 (full checks + ML) |
| 8, 9 | Atta 10 (fixes) |
| 10 | Neelam 10 (evaluation page) |

Before every prompt, pull the latest `main`. Merge small pull requests often to avoid conflicts in `CLAUDE.md`, `docker-compose.yml` and CI.

## Sprint 1: setup, check specs, CVSS mapping, chains

These four unblock Atta. Prompts 2 and 3 are the most urgent work on the whole team this sprint.

### Prompt 1: Workspace setup

```text
I'm Asim, security / ML-NLP / evaluation owner on CAWASMA, a context-aware
web
security scanner (final-year project, team of 3). Read CLAUDE.md and docs/
first — they hold the team plan and the shared contracts.
Set up my part of the repo:
1. Add an "Asim — security, ML, evaluation" section to CLAUDE.md listing the
files I own: checks.yaml, config/cvss_mapping.yaml, config/chains.yaml,
backend/app/ml/sensitivity.py, backend/app/ml/body_classifier.py,
eval/ (targets, ground truth, labelled data, harness, results).
Do not change the other sections.
2. Create eval/ with subfolders: targets/, ground_truth/, labels/,
harness/, results/, notebooks/. Add a README in each saying what goes
there.
3. Add the ML dependencies (sentence-transformers, spaCy + en_core_web_sm,
scikit-learn, pandas, matplotlib) as an optional "ml" dependency group,
so the main backend image stays light. Make sure the model downloads are
cached in Docker, not fetched on every start.
4. Create docs/lit-review.md with a structure for my notes: CVSS v3.1
environmental metrics, OWASP Top 10 2021 / ASVS, context-aware
vulnerability scoring papers, Burp/ZAP/Nikto/Nuclei scoring and their
limits. Headings and short prompts only — I'll write the content.
5. Confirm `pip install -e ".[ml]"` works and a 3-line test loads
all-MiniLM-L6-v2 and spaCy successfully.
```

### Prompt 2: Check specifications

```text
Read CLAUDE.md and docs/check-spec-format.md. Help me draft the full
checks.yaml. I will review every entry myself before committing.
Scope: passive and safe active checks a web scanner can run from HTTP
responses — no exploitation. Cover at least:
- Transport: HTTPS missing/redirect, HSTS missing/weak, TLS 1.0/1.1 enabled,
weak ciphers, invalid/expired certificate
- Security headers: CSP missing/unsafe-inline, X-Frame-Options /
frame-ancestors, X-Content-Type-Options, Referrer-Policy,
Permissions-Policy
- Cookies: missing Secure / HttpOnly / SameSite on session cookies
- CORS: wildcard with credentials, reflected Origin
- Information disclosure: server/framework version banners, stack traces,
directory listing, exposed .git/.env/backup files, verbose errors
- API: unauthenticated access to sensitive-looking endpoints, missing
rate-limit headers on auth endpoints
[add or remove checks to match our proposal]
For each check write: check_id, category, description, http_condition
(precise enough that Atta can code it with no guessing), owasp (2021
Top 10 id), cwe, base_cvss_vector (full CVSS:3.1/AV:..., scope included),
and a one-line rationale for the vector as a YAML comment.
Then:
- Validate the file with Atta's checks.yaml validator.
- Produce docs/check-specs-review.md: one table, check_id | base score |
severity | rationale, sorted by score, so I can review them fast.
- Flag any check where the vector is debatable, and say what the
alternative vector would be.
```

### Prompt 3: CVSS environmental mapping

```text
Read CLAUDE.md and docs/cvss-mapping-contract.md. Help me design the mapping
from endpoint context to CVSS v3.1 environmental metrics. I own its
correctness, so explain your reasoning.
1. Sensitivity classes (4): propose names and definitions, e.g. public,
user, authentication, admin/financial. [replace with our 4 classes if
already agreed]
2. Body signals: credential, pii, financial, internal_ip, secret_key,
stack_trace [adjust].
3. Write config/cvss_mapping.yaml: each class -> CR / IR / AR
(Low/Medium/High), each signal -> the requirement(s) it raises.
Rule: signals only raise requirements, never lower them; take the max.
Do NOT use modified base metrics (MAV, MAC...) — only the Security
Requirements, so the score stays standards-valid and explainable.
4. Write docs/cvss-mapping.md: the table, a one-line justification per row
grounded in the CVSS v3.1 spec, and 5 worked examples (same finding on a
public page vs an admin endpoint) showing base vs final score using the
`cvss` Python library.
5. A small script eval/harness/mapping_demo.py that prints those examples,
so we can paste the numbers into the report.
6. Check: does any combination make the score go DOWN versus base? If so,
explain why that is or isn't acceptable and propose a fix.
```

### Prompt 4: Chain templates

```text
Read CLAUDE.md, checks.yaml and docs/cvss-mapping.md. Help me define the
5 vulnerability chain templates.
For each chain write, in config/chains.yaml:
- chain_id, name, the check_ids that must co-occur, and the scope rule
(same endpoint / same host / any endpoint on the target)
- the composite CVSS v3.1 vector for the chain, so the chain score is still
standards-valid (not a made-up multiplier)
- a one-line justification of why these findings combine
Suggested starting points (change if better ones exist):
1. Missing HttpOnly cookie + CSP missing/unsafe-inline -> session theft via
XSS
2. CORS reflected origin with credentials + sensitive API endpoint -> data
theft
3. Exposed .git/.env + secret in body -> credential compromise
4. Missing HSTS + login endpoint without HTTPS redirect -> credential
interception
5. Verbose errors/stack traces + version banner -> targeted exploitation
Also write docs/chain-templates.md for Atta: the trigger logic in plain
pseudo-code per chain (inputs, condition, output), and how a chain should
appear in a finding's evidence. Then list any chain that is weak or hard to
defend in front of a jury.
```

## Sprints 2–3: targets, ground truth, classifiers

Prompt 5 must be done by the end of Sprint 2: the plan says the eval harness is live when the vertical slice is.

### Prompt 5: Vulnerable targets, ground truth, labelling tools (Sprint 2)

```text
Read CLAUDE.md. Set up the evaluation targets and the data I will label.
1. docker-compose.eval.yml with OWASP Juice Shop, DVWA, VAmPI and crAPI
on an isolated Docker network with no internet egress. Pin image
versions (results must be reproducible). Healthchecks, and Makefile
targets eval-up / eval-down / eval-reset. Configure CAWASMA's
ALLOWED_INTERNAL_HOSTS for these hosts in the eval profile ONLY.
2. Ground-truth format, eval/ground_truth/<target>.yaml: one entry per known
issue -> target, endpoint, check_id (from checks.yaml), expected
(present/absent), source (official docs / my manual verification), notes.
Fill in a starter list per target from each project's official
challenge/vulnerability docs, marked "unverified" until I check it by
hand.
Also list which checks.yaml checks should NOT fire on each target — we
need true negatives to compute false-positive rate.
3. Endpoint collection: a script that gathers endpoint paths from all four
targets (their OpenAPI specs where they exist, plus a crawl) and writes
eval/labels/endpoints_raw.csv (target, method, path). Aim for 150–300
unique paths; de-duplicate ID variants like /users/1 and /users/2.
4. A small labelling CLI, eval/labels/label.py: shows one path at a time,
I press 1–4 for the sensitivity class (or s to skip), it saves to
endpoints_labelled.csv and can resume where I stopped.
5. Write docs/labelling-guide.md: the definition of each class with 3
examples, so labels stay consistent (and so a second person could label
a sample for inter-rater agreement).
```

### Prompt 6: Sensitivity classifier (Sprint 2–3)

```text
Read CLAUDE.md, docs/cvss-mapping-contract.md and docs/labelling-guide.md.
Build backend/app/ml/sensitivity.py, replacing Atta's stub. Keep the exact
interface from the contract: classify(endpoint) -> SensitivityClass.
1. Load all-MiniLM-L6-v2 once (module-level / cached), not per call.
2. Preprocess paths into text: split on / - _ . and camelCase, drop numeric
IDs and UUIDs, expand common abbreviations (usr, pwd, acct, admin...),
include the HTTP method.
3. Each class has an anchor SET (several short phrases) in
config/sensitivity_anchors.yaml. Embed anchors once; score a path by
cosine similarity to each class (max over its anchors); pick the best.
Below a confidence threshold, return the safest default class and log it.
4. Evaluation script eval/harness/eval_sensitivity.py using
eval/labels/endpoints_labelled.csv:
- split into a tuning set and a held-out test set (stratified, fixed seed)
BEFORE any tuning, so I don't overfit the anchors to the test data
- report accuracy, per-class precision/recall/F1, and a confusion-matrix
PNG to eval/results/
- compare against a simple keyword-rules baseline (the old stub)
5. Unit tests: interface contract, determinism, speed (<50 ms per path
after warm-up on CPU).
6. Tell me which classes get confused and suggest anchor changes. Tune
only on the tuning split; report the final number on the test split once.
```

### Prompt 7: Body classifier (Sprint 3)

```text
Read CLAUDE.md and docs/cvss-mapping-contract.md. Build
backend/app/ml/body_classifier.py, replacing the stub. Keep the interface:
analyze(response) -> set[BodySignal].
Detect, with regex first and spaCy only where regex can't:
- credential: password fields in JSON/HTML, Basic auth, connection strings
- secret_key: AWS keys, private-key PEM blocks, JWTs, generic API keys
(pattern + entropy check to cut false positives)
- pii: emails, phone numbers, national ID formats [e.g. Pakistan CNIC],
person names next to personal fields (spaCy NER)
- financial: card numbers that pass the Luhn check, IBANs
- internal_ip: RFC1918 / loopback / link-local addresses
- stack_trace: Python/Java/PHP/.NET/Node trace patterns
Requirements:
- Only scan text-like content types; cap body size; must be fast.
- Evidence must be REDACTED (e.g. AKIA****WXYZ) — CAWASMA must never store
or show a full secret in the DB, logs or reports.
- Ignore obvious placeholders (example.com, test@test.com, 4111... test
cards in docs pages) and explain the rule.
- Tests: for every signal, a fixture that fires and a near-miss fixture
that must NOT fire. Keep fixtures in tests/fixtures/bodies/.
- Run it over the responses from our eval targets and give me a table:
signal | hits | how many look like false positives, so I can tune.
```

## Sprints 4–6: evaluation, security review, final results

These produce the numbers the project is judged on.

### Prompt 8: Evaluation harness and baselines (Sprint 4)

```text
Read CLAUDE.md and eval/README files. Build the evaluation harness.
1. eval/harness/run_all.py: for each target in docker-compose.eval.yml,
run (a) CAWASMA through its API, (b) OWASP ZAP baseline/API scan,
(c) Nuclei with a fixed template set and version. Save raw outputs to
eval/results/raw/<tool>/<target>/ with the tool version and timestamp.
2. Normalisers: map ZAP alerts and Nuclei findings onto our check_ids
(eval/harness/tool_mapping.yaml). Findings with no mapping are kept
and reported as "out of scope", not silently dropped.
3. Matching against eval/ground_truth/: a finding is a true positive if
target + endpoint + check_id match; document the endpoint-matching rule
(path normalisation, ID segments).
4. Metrics per tool and per target: TP, FP, FN, TN, precision, recall,
false-positive rate, plus scan time. Write eval/results/metrics.csv and
a markdown table to eval/results/comparison.md.
5. Make the whole run one command (make eval) and reproducible: fixed
versions, fixed seeds, targets reset before each run.
6. Do a first full run and list every false positive and false negative
for CAWASMA, grouped by check_id, in eval/results/errors.md. I'll send
the false positives to Atta.
```

### Prompt 9: Tool security review (Sprint 4)

```text
Read CLAUDE.md. Do a security review of CAWASMA itself. Do not fix Atta's
or Neelam's code: write failing tests and a findings report I can hand them.
Review and test:
1. SSRF guard: tests that try private ranges, 127.0.0.1 variants (decimal,
octal, hex, IPv6 ::1, IPv4-mapped IPv6), 169.254.169.254, DNS names
resolving to private IPs, redirects to internal hosts, DNS rebinding.
Use a local DNS stub or monkeypatched resolver, never real internal hosts.
2. Passive-only mode: run a passive scan through a logging proxy and assert
only GET/HEAD requests went out, with no wordlist probing or payloads.
3. Authorisation gate: a scan cannot start through the API without the
authorisation confirmation flag, even when the frontend is bypassed.
4. Secret leakage: grep the DB, logs and every export format after a scan
of a target that serves fake secrets; nothing unredacted may appear.
5. Scope: no request ever leaves the target host (check proxy logs).
6. Basic API hygiene: input validation on the URL, rate limiting on
POST /api/scan, no stack traces in API error responses.
Output docs/security-review.md: one table, issue | severity | evidence |
owner (Atta/Neelam) | status, plus the test files under
tests/security/. Mark which tests currently fail.
```

### Prompt 10: Ranking experiment, tuning, final tables (Sprints 5–6)

```text
Read CLAUDE.md, eval/results/comparison.md and errors.md. Final evaluation.
1. Before/after ranking experiment: for each target, rank CAWASMA findings
by base CVSS score (before) and by final environmental score (after).
Compare both rankings against my ground-truth priority order
[eval/ground_truth/priority_<target>.yaml — create the template if
missing] using NDCG@10 and "rank of the first critical finding".
Report per target and averaged, with a short statistical note on the
sample size (no overclaiming).
2. Tuning pass: using errors.md, propose anchor and regex changes to cut
false positives. Re-run the evaluation and show before/after
precision/recall/FPR. Never tune on the held-out test labels.
3. Final tables for the report in eval/results/final/: CAWASMA vs ZAP vs
Nuclei (precision, recall, FPR, scan time), classifier accuracy +
confusion matrix, the ranking experiment, and the mapping examples.
Each as a CSV, a markdown table and a clean PNG chart.
4. docs/evaluation-method.md: targets and versions, ground-truth process,
matching rules, metrics definitions, threats to validity.
5. Security sign-off: re-run tests/security/ and update
docs/security-review.md with the final status of every issue.
```
