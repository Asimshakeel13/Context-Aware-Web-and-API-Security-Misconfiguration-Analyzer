# 05 — Security Checks (all 58)

CAWASMA implements **58 checks** across **7 categories**. Each check carries
predefined metadata — these CVSS v3.1 vectors and base scores are fixed in the
code (`app/scanner/rules/catalog.py`) and are **never invented at runtime**.

Every check in code also stores: `rule_id`, `name`, `category`, `description`,
`cvss_vector`, `base_score`, detection logic, `evidence` (redacted), `impact`,
`recommendation`, and `references`. Checks marked **⚠** cannot be fully confirmed
from unauthenticated black-box analysis; they fire only on a genuine surface
signal and always carry an explicit `limitation` note (see
[Limitations](10-limitations-owasp.md)).

> The base CVSS score is the *standard* severity of the issue in isolation.
> CAWASMA then adjusts it by endpoint context and response sensitivity to produce
> the final, prioritized score — see [Scoring Model](06-scoring-model.md).

## The catalog

### Security Headers (12)

| Rule | Name | Base CVSS | CVSS Vector | Limitation? |
|------|------|:---------:|-------------|:-----------:|
| `HDR-001` | Missing HSTS (Strict-Transport-Security) | 5.9 | `AV:N/AC:H/PR:N/UI:N/S:U/C:H/I:N/A:N` |  |
| `HDR-002` | Missing Content-Security-Policy | 6.1 | `AV:N/AC:L/PR:N/UI:R/S:C/C:L/I:L/A:N` |  |
| `HDR-003` | Missing X-Frame-Options | 6.1 | `AV:N/AC:L/PR:N/UI:R/S:C/C:L/I:L/A:N` |  |
| `HDR-004` | Missing X-Content-Type-Options | 4.3 | `AV:N/AC:L/PR:N/UI:R/S:U/C:L/I:N/A:N` |  |
| `HDR-005` | Missing Referrer-Policy | 3.1 | `AV:N/AC:H/PR:N/UI:N/S:U/C:L/I:N/A:N` |  |
| `HDR-006` | Missing Permissions-Policy | 3.1 | `AV:N/AC:H/PR:N/UI:N/S:U/C:L/I:N/A:N` |  |
| `HDR-007` | Server version disclosure | 5.3 | `AV:N/AC:L/PR:N/UI:N/S:U/C:L/I:N/A:N` |  |
| `HDR-008` | X-Powered-By disclosure | 4.3 | `AV:N/AC:L/PR:N/UI:N/S:U/C:L/I:N/A:N` |  |
| `HDR-009` | Missing Cross-Origin-Opener-Policy | 4.3 | `AV:N/AC:H/PR:N/UI:R/S:U/C:L/I:N/A:N` |  |
| `HDR-010` | Missing Cross-Origin-Resource-Policy | 4.3 | `AV:N/AC:H/PR:N/UI:R/S:U/C:L/I:N/A:N` |  |
| `HDR-011` | Weak cache control on sensitive endpoint | 4.3 | `AV:N/AC:H/PR:N/UI:N/S:U/C:L/I:N/A:N` |  |
| `HDR-012` | Missing Expect-CT / CT enforcement | 3.1 | `AV:N/AC:H/PR:N/UI:N/S:U/C:L/I:N/A:N` | ⚠ |

### Cookies (6)

| Rule | Name | Base CVSS | CVSS Vector | Limitation? |
|------|------|:---------:|-------------|:-----------:|
| `CKI-001` | Cookie missing HttpOnly flag | 5.3 | `AV:N/AC:L/PR:N/UI:R/S:U/C:L/I:N/A:N` |  |
| `CKI-002` | Cookie missing Secure flag | 5.9 | `AV:N/AC:H/PR:N/UI:N/S:U/C:H/I:N/A:N` |  |
| `CKI-003` | Cookie missing SameSite attribute | 4.3 | `AV:N/AC:L/PR:N/UI:R/S:U/C:L/I:N/A:N` |  |
| `CKI-004` | Session token in URL | 6.5 | `AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:N/A:N` |  |
| `CKI-005` | Overly broad cookie scope | 4.3 | `AV:N/AC:H/PR:N/UI:N/S:U/C:L/I:N/A:N` |  |
| `CKI-006` | Low session-token entropy | 5.3 | `AV:N/AC:H/PR:N/UI:N/S:U/C:L/I:N/A:N` | ⚠ |

### CORS (5)

| Rule | Name | Base CVSS | CVSS Vector | Limitation? |
|------|------|:---------:|-------------|:-----------:|
| `COR-001` | CORS wildcard origin | 5.3 | `AV:N/AC:L/PR:N/UI:N/S:U/C:L/I:N/A:N` |  |
| `COR-002` | CORS origin reflection | 7.5 | `AV:N/AC:L/PR:N/UI:R/S:C/C:H/I:N/A:N` |  |
| `COR-003` | CORS allows credentials with weak origin | 8.1 | `AV:N/AC:L/PR:N/UI:R/S:C/C:H/I:L/A:N` |  |
| `COR-004` | Unsafe methods allowed cross-origin | 5.4 | `AV:N/AC:L/PR:N/UI:R/S:U/C:L/I:L/A:N` |  |
| `COR-005` | Missing CORS max-age | 3.1 | `AV:N/AC:H/PR:N/UI:N/S:U/C:N/I:N/A:L` |  |

### TLS / Certificates (8)

| Rule | Name | Base CVSS | CVSS Vector | Limitation? |
|------|------|:---------:|-------------|:-----------:|
| `TLS-001` | Legacy TLS 1.0/1.1 offered | 7.4 | `AV:N/AC:H/PR:N/UI:N/S:U/C:H/I:H/A:N` | ⚠ |
| `TLS-002` | Weak cipher suite negotiated | 7.4 | `AV:N/AC:H/PR:N/UI:N/S:U/C:H/I:H/A:N` |  |
| `TLS-003` | Certificate expired or expiring soon | 7.4 | `AV:N/AC:H/PR:N/UI:N/S:U/C:H/I:H/A:N` |  |
| `TLS-004` | Self-signed certificate | 6.5 | `AV:N/AC:H/PR:N/UI:N/S:U/C:H/I:N/A:N` |  |
| `TLS-005` | No HTTP-to-HTTPS redirect | 6.5 | `AV:N/AC:H/PR:N/UI:N/S:U/C:H/I:N/A:N` |  |
| `TLS-006` | Mixed content references | 5.3 | `AV:N/AC:H/PR:N/UI:R/S:C/C:L/I:L/A:N` |  |
| `TLS-007` | HSTS preload not configured | 3.7 | `AV:N/AC:H/PR:N/UI:N/S:U/C:L/I:N/A:N` |  |
| `TLS-008` | Certificate hostname mismatch | 6.5 | `AV:N/AC:H/PR:N/UI:N/S:U/C:H/I:N/A:N` |  |

### REST API (14)

| Rule | Name | Base CVSS | CVSS Vector | Limitation? |
|------|------|:---------:|-------------|:-----------:|
| `API-001` | Rate limiting absent | 5.3 | `AV:N/AC:L/PR:N/UI:N/S:U/C:N/I:N/A:L` | ⚠ |
| `API-002` | HTTP TRACE method enabled | 5.3 | `AV:N/AC:L/PR:N/UI:N/S:U/C:L/I:N/A:N` |  |
| `API-003` | Unauthenticated data exposure | 7.5 | `AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:N/A:N` | ⚠ |
| `API-004` | Verbose error / stack trace | 5.3 | `AV:N/AC:L/PR:N/UI:N/S:U/C:L/I:N/A:N` |  |
| `API-005` | Possible mass assignment | 5.9 | `AV:N/AC:L/PR:L/UI:N/S:U/C:L/I:H/A:N` | ⚠ |
| `API-006` | Possible BOLA / IDOR | 6.5 | `AV:N/AC:L/PR:L/UI:N/S:U/C:H/I:N/A:N` | ⚠ |
| `API-007` | Missing API versioning | 3.1 | `AV:N/AC:H/PR:N/UI:N/S:U/C:N/I:N/A:L` |  |
| `API-008` | Deprecated API in use | 4.3 | `AV:N/AC:H/PR:N/UI:N/S:U/C:L/I:N/A:N` |  |
| `API-009` | OPTIONS exposes excessive methods | 4.3 | `AV:N/AC:L/PR:N/UI:N/S:U/C:L/I:N/A:N` |  |
| `API-010` | JWT misconfiguration indicators | 6.5 | `AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:L/A:N` | ⚠ |
| `API-011` | API overfetching (excess data) | 4.3 | `AV:N/AC:L/PR:N/UI:N/S:U/C:L/I:N/A:N` | ⚠ |
| `API-012` | GraphQL introspection enabled | 5.3 | `AV:N/AC:L/PR:N/UI:N/S:U/C:L/I:N/A:N` |  |
| `API-013` | Secrets in API response | 8.6 | `AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:N/A:N` |  |
| `API-014` | Injection error reflection | 6.1 | `AV:N/AC:L/PR:N/UI:R/S:U/C:L/I:L/A:N` | ⚠ |

### Authentication (7)

| Rule | Name | Base CVSS | CVSS Vector | Limitation? |
|------|------|:---------:|-------------|:-----------:|
| `AUT-001` | HTTP Basic authentication scheme | 5.3 | `AV:N/AC:H/PR:N/UI:N/S:U/C:H/I:N/A:N` |  |
| `AUT-002` | Broken function-level authorization | 6.5 | `AV:N/AC:L/PR:L/UI:N/S:U/C:H/I:H/A:N` | ⚠ |
| `AUT-003` | Weak password-reset token | 6.5 | `AV:N/AC:H/PR:N/UI:R/S:U/C:H/I:N/A:N` | ⚠ |
| `AUT-004` | Session not invalidated on logout | 5.3 | `AV:N/AC:H/PR:L/UI:N/S:U/C:H/I:N/A:N` | ⚠ |
| `AUT-005` | Weak authentication handling indicators | 5.3 | `AV:N/AC:L/PR:N/UI:N/S:U/C:L/I:N/A:N` | ⚠ |
| `AUT-006` | Default credentials exposure (passive) | 7.5 | `AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:N` | ⚠ |
| `AUT-007` | OAuth2 open redirect indicators | 6.1 | `AV:N/AC:L/PR:N/UI:R/S:C/C:L/I:L/A:N` | ⚠ |

### Information Disclosure (6)

| Rule | Name | Base CVSS | CVSS Vector | Limitation? |
|------|------|:---------:|-------------|:-----------:|
| `INF-001` | Internal IP address in response | 5.3 | `AV:N/AC:L/PR:N/UI:N/S:U/C:L/I:N/A:N` |  |
| `INF-002` | Directory listing enabled | 5.3 | `AV:N/AC:L/PR:N/UI:N/S:U/C:L/I:N/A:N` |  |
| `INF-003` | .env file exposed | 9.1 | `AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:N/A:N` |  |
| `INF-004` | .git repository exposed | 7.5 | `AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:N/A:N` |  |
| `INF-005` | Backup / archive file exposed | 7.5 | `AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:N/A:N` |  |
| `INF-006` | Public API documentation exposed | 5.3 | `AV:N/AC:L/PR:N/UI:N/S:U/C:L/I:N/A:N` |  |
## Category summary

| Category | Count | Rule IDs |
|----------|:-----:|----------|
| Security Headers | 12 | `HDR-001` … `HDR-012` |
| Cookies | 6 | `CKI-001` … `CKI-006` |
| CORS | 5 | `COR-001` … `COR-005` |
| TLS / Certificates | 8 | `TLS-001` … `TLS-008` |
| REST API | 14 | `API-001` … `API-014` |
| Authentication | 7 | `AUT-001` … `AUT-007` |
| Information Disclosure | 6 | `INF-001` … `INF-006` |
| **Total** | **58** | |

## Notes on specific detections

- **TLS checks** use a raw `ssl` probe (not httpx) to read negotiated
  protocol/cipher and to parse the certificate (expiry, self-signed, hostname
  match) with the `cryptography` library — this works even against untrusted or
  self-signed certificates.
- **CORS checks** send a probe request carrying a test `Origin` header and inspect
  `Access-Control-Allow-Origin` / `-Allow-Credentials` to detect reflection and
  credentialed weak-origin configurations.
- **Rate limiting** (`API-001`) is inferred from a small, bounded burst — absence
  of a `429` is reported as an indicator, not proof.
- **Secrets / `.env`** detections feed the response-body classifier; credential
  exposure forces the finding's severity to CRITICAL.
