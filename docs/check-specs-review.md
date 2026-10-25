# Checks specification review

Scores are derived from each CVSS v3.1 base vector by the repository
validator. Severity uses the current buckets: CRITICAL (9.0–10.0), HIGH
(7.0–8.9), MEDIUM (4.0–6.9), and LOW (0.1–3.9).

| check_id | base score | severity | rationale |
|---|---:|---|---|
| INF-005 | 9.1 | CRITICAL | Exposed configuration, backups, or private keys can disclose credentials and enable compromise. |
| API-001 | 9.1 | CRITICAL | Unauthenticated access to sensitive resources threatens confidentiality and integrity. |
| CKI-002 | 8.1 | HIGH | Script-readable session tokens increase the impact of client-side injection. |
| CKI-003 | 7.1 | HIGH | Cross-site cookie delivery can enable unauthorized state-changing requests. |
| COR-001 | 7.1 | HIGH | Wildcard credentialed CORS can expose authenticated data to arbitrary sites. |
| COR-002 | 7.1 | HIGH | Reflected untrusted origins can grant attacker-controlled sites access to authenticated responses. |
| API-002 | 6.5 | MEDIUM | Missing observable rate-limit headers can enable repeated credential attacks. |
| CKI-001 | 5.9 | MEDIUM | Missing Secure permits session exposure over downgraded or misconfigured transport. |
| HDR-001 | 5.4 | MEDIUM | Missing CSP removes a browser control that limits injected content. |
| HDR-002 | 5.4 | MEDIUM | Unsafe script allowances weaken protection against client-side code execution. |
| HDR-003 | 5.4 | MEDIUM | Missing framing restrictions can permit clickjacking. |
| HDR-004 | 5.4 | MEDIUM | Missing frame-ancestors leaves modern browsers without an explicit framing allow-list. |
| HST-001 | 5.3 | MEDIUM | Missing HSTS permits browser downgrade exposure. |
| INF-001 | 5.3 | MEDIUM | Server version disclosure supports targeted reconnaissance. |
| INF-002 | 5.3 | MEDIUM | Framework version disclosure supports targeted reconnaissance. |
| INF-003 | 5.3 | MEDIUM | Stack traces disclose internal implementation details and possibly secrets. |
| INF-004 | 5.3 | MEDIUM | Directory listings reveal deployment artifacts useful for further compromise. |
| INF-006 | 5.3 | MEDIUM | Verbose diagnostics disclose internal state and possibly sensitive data. |
| HDR-005 | 4.3 | MEDIUM | MIME confusion can turn passive content into browser-executed content. |
| HDR-006 | 4.3 | MEDIUM | Referrer leakage exposes URL details cross-origin. |
| HDR-007 | 4.3 | MEDIUM | Unrestricted browser features increase the impact of compromised content. |
| TRN-001 | 4.2 | MEDIUM | Missing HTTP-to-HTTPS redirect leaves downgrade exposure. |
| HST-002 | 3.1 | LOW | A partial HSTS policy reduces but does not remove downgrade exposure. |

## Debatable vectors and alternatives

These are review prompts, not changes made automatically:

- **TRN-001 (4.2):** `UI:R` assumes a victim must follow the unsafe HTTP link.
  If the scanner treats the network downgrade as directly attacker-reachable,
  consider `CVSS:3.1/AV:N/AC:H/PR:N/UI:N/S:U/C:L/I:L/A:N` (5.9).
- **HST-001 (5.3):** `UI:R` models browser downgrade exposure. If the
  deployment has a demonstrated active mixed-content path, `UI:N` may be
  defensible: `CVSS:3.1/AV:N/AC:H/PR:N/UI:N/S:U/C:H/I:N/A:N` (6.5).
- **HDR-001/HDR-002 (5.4):** the `UI:R` assumption is appropriate for browser
  content, but these checks are low impact for JSON-only APIs. Consider
  `C:L/I:N` (4.3) for API-only scope, or keep the current vector and let
  endpoint context prioritize it.
- **HDR-003/HDR-004 (5.4):** clickjacking requires a browser victim and is
  usually integrity-focused. An alternative is
  `CVSS:3.1/AV:N/AC:L/PR:N/UI:R/S:U/C:N/I:L/A:N` (3.1).
- **CKI-002 (8.1):** this assumes an XSS path exists and rates token theft as
  high confidentiality and integrity. If XSS is not established, consider
  `CVSS:3.1/AV:N/AC:L/PR:N/UI:R/S:U/C:H/I:L/A:N` (6.5).
- **COR-001/COR-002 (7.1):** `UI:R` reflects the victim visiting an
  attacker-controlled origin. If the API is consumed by a non-browser client,
  the browser-specific vector should not be applied.
- **INF-005/API-001 (9.1):** these are intentionally high-impact vectors, but
  `PR:N` is only correct when the response was verified without credentials.
  If an authenticated session is required, use
  `CVSS:3.1/AV:N/AC:L/PR:L/UI:N/S:U/C:H/I:H/A:N` (8.1).
- **API-002 (6.5):** missing rate-limit headers do not prove missing
  throttling. If a safe active repeated-request test confirms unlimited
  attempts, `CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:L/I:H/A:N` (8.1) is a possible
  alternative.

## Checks intentionally outside this YAML contract

TLS 1.0/1.1 negotiation, weak cipher suites, and invalid or expired
certificates require TLS-handshake and certificate observations. The current
`checks.yaml` contract accepts only HTTP response headers, status codes, and
body predicates, so adding placeholder HTTP rules for these checks would be
misleading. They should be represented by the existing TLS subsystem and
catalogued separately with equivalent CVSS vectors.

The same contract cannot directly express whether an HTTP response originated
from plain HTTP, whether an `Origin` value was reflected, or whether a path is
sensitive. Those checks are included with explicit `limitation` fields so the
engine must supply the safe active probe or endpoint classification before
reporting a finding.
