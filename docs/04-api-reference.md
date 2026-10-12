# 04 — API Reference

Base URL (default): `http://localhost:8000`
Interactive docs: `http://localhost:8000/docs` (Swagger) and `/redoc`.

All responses are Pydantic models (never raw ORM rows). Errors use a consistent
envelope and never leak stack traces:

```json
{ "success": false, "error": { "code": "INVALID_TARGET", "message": "..." } }
```

## Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/health` | Liveness + dependency status (degrades gracefully) |
| POST | `/api/scans` | Create a scan (returns immediately) |
| GET | `/api/scans` | List scans (paginated) |
| GET | `/api/scans/{id}` | Scan detail + summary counts |
| GET | `/api/scans/{id}/status` | Status + progress + current stage |
| GET | `/api/scans/{id}/findings` | Findings (paginated) |
| GET | `/api/scans/{id}/endpoints` | Discovered endpoints (paginated) |
| GET | `/api/scans/{id}/chains` | Detected attack chains |
| GET | `/api/scans/{id}/report?format=` | Report: `json` \| `csv` \| `html` \| `pdf` |
| DELETE | `/api/scans/{id}` | Delete a scan and all its data |
| WS | `/ws/scans/{id}` | Live progress stream |

Pagination: `?page=1&limit=20` (limit max 100). Paginated bodies carry
`{ "items": [...], "meta": { "page", "limit", "total", "pages" } }`.

## Create a scan

```http
POST /api/scans
{ "target_url": "https://example.com" }
```
```json
201 Created
{ "scan_id": "a1b2c3d4-...", "status": "QUEUED" }
```
Invalid/non-HTTPS targets return `400` with the error envelope.

## Status

```json
GET /api/scans/{id}/status
{ "scan_id": "...", "status": "RUNNING", "progress": 63, "current_stage": "analyzing" }
```
Statuses: `QUEUED` · `RUNNING` · `COMPLETED` · `FAILED` · `CANCELLED`.

## Finding schema (key fields)

```json
{
  "rule_id": "HDR-003",
  "title": "Missing X-Frame-Options",
  "category": "HEADERS",
  "context_class": "CRITICAL",
  "context_confidence": 0.94,
  "cvss_vector": "CVSS:3.1/AV:N/AC:L/PR:N/UI:R/S:C/C:L/I:L/A:N",
  "cvss_base_score": 6.1,
  "cawasma_context_multiplier": 2.0,
  "response_bonus": 2.0,
  "cawasma_final_score": 10.0,
  "severity": "CRITICAL",
  "evidence": "… (redacted) …",
  "impact": "...",
  "recommendation": "...",
  "references": ["https://owasp.org/..."],
  "limitation": null
}
```

Note how the **official CVSS** fields (`cvss_vector`, `cvss_base_score`) are kept
separate from the **CAWASMA custom** fields (`cawasma_context_multiplier`,
`response_bonus`, `cawasma_final_score`) — see [Scoring Model](06-scoring-model.md).

## WebSocket events

Connect to `ws://localhost:8000/ws/scans/{id}`. The server first sends a snapshot,
then live events:

```json
{ "type": "snapshot", "status": "RUNNING", "percent": 20, "stage": "analyzing" }
{ "scan_id": "...", "stage": "analyzing", "percent": 55, "message": "Analyzing /api/users" }
{ "scan_id": "...", "stage": "completed", "percent": 100, "message": "Scan complete" }
```
Clients that cannot use WebSockets can poll `/status` instead (the frontend does
both automatically).

## Reports & export

```
GET /api/scans/{id}/report?format=json   → application/json
GET /api/scans/{id}/report?format=csv    → text/csv (attachment)
GET /api/scans/{id}/report?format=html   → text/html
GET /api/scans/{id}/report?format=pdf    → application/pdf (attachment)
```
All report content is pre-redacted. If WeasyPrint's native libraries are absent,
`format=pdf` returns `501` with a clear message rather than crashing.
