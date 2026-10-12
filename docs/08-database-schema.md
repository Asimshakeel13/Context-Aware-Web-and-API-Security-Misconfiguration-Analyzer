# 08 — Database Schema

PostgreSQL via SQLAlchemy (async) ORM, with Alembic migrations. The schema is a
clean relational graph with foreign keys, indexes, timestamps and cascade rules.
(Models live in `app/database/models/`.)

## Tables

| Table | Holds | Key relationships |
|-------|-------|-------------------|
| `scans` | one scan job: target, status, progress, stage, timings, error | parent of everything |
| `endpoints` | discovered endpoints: url, path, method, status, **context class/confidence/reason** | `scan_id → scans` |
| `findings` | security findings: rule, category, **both CVSS and CAWASMA scores**, evidence, impact, recommendation, limitation | `scan_id → scans`, `endpoint_id → endpoints` |
| `headers` | relevant captured response headers (redacted) | `endpoint_id → endpoints` |
| `cookies` | cookie **metadata** only (flags, scope, length) — never the token value | `endpoint_id → endpoints` |
| `tls_info` | host-level TLS: protocols, cipher, cert subject/issuer/expiry, self-signed, hostname match | `scan_id → scans` |
| `attack_chains` | triggered chains: code, name, template composite score, severity | `scan_id → scans` |
| `chain_findings` | many-to-many link between chains and their member findings | `chain_id`, `finding_id` |
| `ai_insights` | optional executive summary (provider recorded) | `scan_id → scans` |
| `feedback` | analyst feedback / false-positive corrections | `scan_id → scans` |

## Relationships & cascades

```
scans ─1:N─▶ endpoints ─1:N─▶ headers
   │             └────1:N─▶ cookies
   ├───1:N─▶ findings ◀──N:M──▶ attack_chains   (via chain_findings)
   │             ▲
   │             └── endpoint_id (nullable, SET NULL if endpoint removed)
   ├───1:N─▶ tls_info
   ├───1:N─▶ attack_chains
   ├───1:N─▶ ai_insights
   └───1:N─▶ feedback
```

- Deleting a `scan` **cascades** to all its children (endpoints, findings,
  headers, cookies, TLS info, chains, insights, feedback) — one delete removes the
  whole graph.
- `findings.endpoint_id` is **nullable** and set to `NULL` if the endpoint row is
  removed, so a finding is never orphaned destructively.

## Scoring columns (findings)

The `findings` table keeps the official and custom values in **separate columns**
so they are always distinguishable:

```
cvss_vector · cvss_base_score                     ← official CVSS v3.1
cawasma_context_multiplier · response_bonus · cawasma_final_score   ← CAWASMA custom
severity · limitation
```

## Portability

The models use cross-dialect types (`sa.Uuid`, `JSON`, `Enum`) and the initial
migration uses generic types only, so the same schema runs on **PostgreSQL** (via
asyncpg) and on **SQLite** (used by the test suite and the lightweight run mode).
