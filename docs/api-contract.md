# CAWASMA API contract v1.0.0

The API the frontend builds against. **Frozen at the end of Sprint 1.**
Machine-readable version: [`openapi.json`](openapi.json) (generate a typed
client from it). The source of truth is
`backend/app/api/schemas/contract.py`; this document and `openapi.json` are
checked against it in CI.

| | |
|---|---|
| Base URL (dev) | `http://localhost:8000` |
| Format | JSON, UTF-8. Timestamps are ISO 8601 in UTC (`2026-10-20T09:00:02Z`). Ids are UUIDs. |
| Version header | every response carries `X-Contract-Version: 1.0.0` |
| Interactive docs | `http://localhost:8000/docs` (routes tagged **contract v1**) |

## Building before the scanner works: mock mode

Set `MOCK_API=true` in `.env` and restart the api (`make up`). The four
contract routes then answer from fixed example data. No database, worker or
real scan is involved. There is one scan per status, so every UI state can be
built:

| `scan_id` | status | use it for |
|-----------|--------|------------|
| `11111111-1111-4111-8111-111111111111` | `DONE` | results page: 7 findings, 1 chain, every drill-down field |
| `22222222-2222-4222-8222-222222222222` | `RUNNING` | progress view (45 %, stage `analyzing`) |
| `33333333-3333-4333-8333-333333333333` | `QUEUED` | what `POST /api/scan` returns (any `https://` URL) |
| `44444444-4444-4444-8444-444444444444` | `FAILED` | error state (`error` message set) |

Mock mode applies the same validation (422 for a bad body) and returns `400` for a
non-`https://` URL, so error handling can be built too. Unknown ids return `404`.

## Endpoints

### `POST /api/scan`: start a scan

Request body (`ScanRequest`):

| Field | Type | Required | Default | Rule |
|-------|------|----------|---------|------|
| `url` | string | yes | | `https://` URL that resolves to a public address |
| `authorisation_confirmed` | boolean | yes | | **must be `true`**: the user confirms they may test the target |
| `crawl_depth` | integer | no | `2` | `1` or `2` |
| `use_wordlist` | boolean | no | `true` | probe common paths such as `/.env`, `/admin` |
| `passive_only` | boolean | no | `false` | no active probes (TLS probe, rate-limit burst, redirect check) |

Unknown fields are rejected (422).

<!-- example: ScanRequest -->
```json
{
  "url": "https://shop.example.com",
  "authorisation_confirmed": true,
  "crawl_depth": 2,
  "use_wordlist": true,
  "passive_only": false
}
```

Response **`202 Accepted`**: a `ScanStatus` with status `QUEUED`, plus
`Location: /api/results/{scan_id}`.

<!-- example: ScanStatus -->
```json
{
  "scan_id": "33333333-3333-4333-8333-333333333333",
  "url": "https://shop.example.com",
  "status": "QUEUED",
  "progress": 0,
  "stage": null,
  "options": {"crawl_depth": 2, "use_wordlist": true, "passive_only": false},
  "created_at": "2026-10-22T09:00:00Z",
  "started_at": null,
  "completed_at": null,
  "error": null,
  "severity_counts": {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
}
```

| Status | When | `error.code` |
|--------|------|--------------|
| 202 | scan queued | |
| 400 | URL not https, malformed, private/loopback IP, or does not resolve | `INVALID_TARGET` |
| 422 | body invalid: `authorisation_confirmed` missing or `false`, `crawl_depth` out of range, unknown field | `VALIDATION_ERROR` |

### `GET /api/results/{scan_id}`: status and results

Always **`200`** for a known scan, whatever its status. Poll it every 2–3 s
until `scan.status` is `DONE` or `FAILED`. `findings` and `chains` are empty
until `DONE`. **Findings are ranked by `final_score`, highest first** (ties
broken by `check_id`), so render them in the order received.

<!-- example: ScanResults -->
```json
{
  "contract_version": "1.0.0",
  "scan": {
    "scan_id": "11111111-1111-4111-8111-111111111111",
    "url": "https://shop.example.com",
    "status": "DONE",
    "progress": 100,
    "stage": "completed",
    "options": {"crawl_depth": 2, "use_wordlist": true, "passive_only": false},
    "created_at": "2026-10-20T09:00:00Z",
    "started_at": "2026-10-20T09:00:02Z",
    "completed_at": "2026-10-20T09:01:14Z",
    "error": null,
    "severity_counts": {"critical": 3, "high": 2, "medium": 0, "low": 2, "info": 0}
  },
  "findings": [
    {
      "id": "f0000000-0000-4000-8000-000000000001",
      "check_id": "INF-003",
      "title": ".env file exposed",
      "category": "INFO_DISCLOSURE",
      "endpoint_id": "f9817110-212d-59e9-88b0-f3f42e264569",
      "endpoint_url": "https://shop.example.com/.env",
      "owasp_map": ["API8:2023"],
      "cwe_map": ["CWE-538"],
      "cvss_vector": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:N/A:N",
      "base_score": 7.5,
      "final_score": 10.0,
      "severity_bucket": "CRITICAL",
      "evidence": {
        "text": ".env file exposed on /.env",
        "status": 200,
        "body_excerpt": "DB_HOST=10.0.3.17\nDB_PASSWORD=[REDACTED]"
      },
      "sensitivity_class": "LOW",
      "body_signals": ["CREDENTIALS", "INTERNAL_IP"],
      "chain_ids": ["c0050000-0000-4000-8000-000000000001"],
      "recommendation": "Block access to dotfiles; move secrets out of web root.",
      "limitation": null
    },
    {
      "id": "f0000000-0000-4000-8000-000000000004",
      "check_id": "TLS-001",
      "title": "Legacy TLS 1.0/1.1 offered",
      "category": "TLS",
      "endpoint_id": null,
      "endpoint_url": null,
      "owasp_map": ["API8:2023"],
      "cwe_map": ["CWE-327"],
      "cvss_vector": "CVSS:3.1/AV:N/AC:H/PR:N/UI:N/S:U/C:H/I:H/A:N",
      "base_score": 7.4,
      "final_score": 7.4,
      "severity_bucket": "HIGH",
      "evidence": {"text": "Legacy TLS 1.0/1.1 offered", "protocols": ["TLSv1.1"]},
      "sensitivity_class": null,
      "body_signals": [],
      "chain_ids": [],
      "recommendation": "Disable TLS 1.0/1.1; require TLS 1.2+.",
      "limitation": "Depends on protocol probe; may be inconclusive if the client's OpenSSL disables legacy protocols."
    }
  ],
  "chains": [
    {
      "id": "c0050000-0000-4000-8000-000000000001",
      "chain_code": "C005",
      "name": ".env Exposure -> Version Leak -> Full Compromise",
      "description": "An exposed .env combined with version disclosure can lead to full compromise.",
      "composite_score": 9.8,
      "severity": "CRITICAL",
      "finding_ids": [
        "f0000000-0000-4000-8000-000000000001",
        "f0000000-0000-4000-8000-000000000006"
      ]
    }
  ]
}
```

(Trimmed to 2 of the 7 findings; the full example is in `openapi.json` and
in mock mode. Note that the chain references a finding not shown here.)

| Status | When | `error.code` |
|--------|------|--------------|
| 200 | scan exists | |
| 404 | no scan with this id | `NOT_FOUND` |
| 422 | id is not a UUID | `VALIDATION_ERROR` |

#### Finding fields

| Field | Meaning / how to show it |
|-------|---------------------------|
| `check_id`, `title`, `category` | which check fired (`HDR-001`, …) |
| `endpoint_id`, `endpoint_url` | where. **Both `null` for host-level findings** (TLS) |
| `owasp_map`, `cwe_map` | standards references; may be `[]` |
| `cvss_vector`, `base_score` | the official CVSS v3.1 base vector and score of the check |
| `final_score` | CAWASMA's context-aware score. Label it as such: **it is not an official CVSS score** |
| `severity_bucket` | `CRITICAL` ≥ 9.0, `HIGH` ≥ 7.0, `MEDIUM` ≥ 4.0, `LOW` ≥ 0.1, `INFO` (may be forced to `CRITICAL` when credentials are exposed) |
| `evidence` | redacted JSON. `evidence.text` is always present; display other keys as key/value detail |
| `sensitivity_class` | how sensitive the endpoint is: `CRITICAL`, `HIGH`, `MEDIUM`, `LOW`; `null` for host-level |
| `body_signals` | sensitive data seen in the endpoint's response: `CREDENTIALS`, `PII`, `FINANCIAL`, `INTERNAL_IP` |
| `chain_ids` | ids into `chains[]`; use for "part of attack chain" badges and links |
| `recommendation` | how to fix |
| `limitation` | if set, black-box testing could not confirm the finding; show it next to the finding |

### `GET /api/results/{scan_id}/export?format=json|csv|html|pdf`: download

Returns the file with `Content-Disposition: attachment; filename="cawasma-{scan_id}.{format}"`.
Use it as a plain link (`<a href=… download>`). `format` defaults to `json`.

| `format` | Content-Type | Content |
|----------|--------------|---------|
| `json` | `application/json` | exactly the `ScanResults` body above |
| `csv` | `text/csv; charset=utf-8` | one row per finding, ranked; columns below |
| `html` | `text/html; charset=utf-8` | printable report (layout may change; not part of the frozen contract) |
| `pdf` | `application/pdf` | the same report as PDF |

CSV columns, in order: `id, check_id, title, category, severity_bucket,
final_score, base_score, cvss_vector, sensitivity_class, body_signals,
owasp_map, cwe_map, endpoint_url, chain_ids`. List values are joined with `;`.

| Status | When | `error.code` |
|--------|------|--------------|
| 200 | file | |
| 404 | no scan with this id | `NOT_FOUND` |
| 409 | scan is not `DONE` yet | `SCAN_NOT_FINISHED` |
| 422 | unknown `format` | `VALIDATION_ERROR` |
| 501 | PDF libraries missing on this server | `FORMAT_UNAVAILABLE` |

### `GET /api/scans?page=1&limit=20`: history

Newest first. `page` ≥ 1 (default 1), `limit` 1–100 (default 20). Items are
`ScanStatus` objects; `severity_counts` gives the finding totals per scan, for
the history table.

<!-- example: ScanList -->
```json
{
  "items": [
    {
      "scan_id": "44444444-4444-4444-8444-444444444444",
      "url": "https://legacy.example.net",
      "status": "FAILED",
      "progress": 8,
      "stage": "crawling",
      "options": {"crawl_depth": 2, "use_wordlist": true, "passive_only": true},
      "created_at": "2026-10-19T09:00:00Z",
      "started_at": "2026-10-19T09:00:02Z",
      "completed_at": "2026-10-19T09:00:17Z",
      "error": "Target unreachable: connection timed out after 15s.",
      "severity_counts": {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
    }
  ],
  "meta": {"page": 4, "limit": 1, "total": 4, "pages": 4}
}
```

| Status | When | `error.code` |
|--------|------|--------------|
| 200 | page (possibly empty `items`) | |
| 422 | `page` / `limit` out of range | `VALIDATION_ERROR` |

## Scan status values

```
QUEUED ──▶ RUNNING ──▶ DONE
                 └───▶ FAILED
```

| `status` | Meaning | `progress` | Results |
|----------|---------|-----------|---------|
| `QUEUED` | accepted, waiting for a worker | 0 | empty |
| `RUNNING` | scanning; `stage` says what it is doing (display only, values may change) | 1–99 | empty |
| `DONE` | finished | 100 | complete |
| `FAILED` | stopped; `error` says why | where it stopped | empty |

`DONE` and `FAILED` are final. There is no cancel state.

## Errors

Every error has the same shape:

<!-- example: ErrorResponse -->
```json
{"success": false, "error": {"code": "INVALID_TARGET", "message": "Only HTTPS targets are allowed."}}
```

`422` responses also carry `details`: a list of `{loc, msg, type}` entries, one
per invalid field, e.g. `{"loc": ["body", "authorisation_confirmed"], "msg":
"Input should be True", ...}`. Use them to highlight the form field.

| `code` | HTTP | Meaning |
|--------|------|---------|
| `VALIDATION_ERROR` | 422 | request body, path or query invalid (see `details`) |
| `INVALID_TARGET` | 400 | URL not allowed or not reachable as a public HTTPS target |
| `NOT_FOUND` | 404 | unknown scan id |
| `SCAN_NOT_FINISHED` | 409 | export requested before the scan is `DONE` |
| `FORMAT_UNAVAILABLE` | 501 | PDF export not available on this server |
| `INTERNAL_ERROR` | 500 | bug; the message never contains internals |

Show `message` to the user; branch on `code`, never on `message`.

## Versioning and change policy

- `CONTRACT_VERSION` follows semver and is sent in `X-Contract-Version`, in
  `ScanResults.contract_version` and in `openapi.json` (`info.x-contract-version`).
- **Minor** (1.0 → 1.1): new optional response fields or new endpoints. Existing
  fields keep their names, types and meaning. Clients must ignore unknown fields.
- **Major** (1.x → 2.0): renaming or removing fields, changing types or enum
  values, changing status codes. Needs Neelam's agreement before the PR is merged.
- Every change bumps the version, regenerates `openapi.json` (`make openapi`)
  and adds a line to the changelog below.

## Pre-contract routes (deprecated)

The current Vite frontend uses older routes (`POST /api/scans`,
`/api/scans/{id}`, `/findings`, `/endpoints`, `/chains`, `/report`, the
WebSocket). They still work, are marked deprecated in `openapi.json`, and will
be removed once the Next.js app uses the contract routes.

**Breaking for the Vite app:** `GET /api/scans` now returns contract
`ScanStatus` items (`scan_id`, `url`, status `DONE`) instead of the old shape
(`id`, `target_url`, status `COMPLETED`), because the contract needs that path
for history. The old dashboard list must switch to the new fields.

## Changelog

- **1.0.0** (Sprint 1): first frozen version.
