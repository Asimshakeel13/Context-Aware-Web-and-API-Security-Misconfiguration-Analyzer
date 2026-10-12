# 10 — Limitations & OWASP Coverage

Honesty about scope is a design principle of CAWASMA. A black-box, unauthenticated
scanner genuinely cannot confirm some classes of issue, and the tool says so rather
than pretending.

## Black-box limitations

The following checks require an authenticated session, business-logic context, or
server-side knowledge that is simply not observable from the outside. CAWASMA fires
them **only on a real surface signal** and attaches an explicit `limitation` string
such as *"Not determinable from unauthenticated black-box analysis."*

| Rule | Why it is limited |
|------|-------------------|
| `API-005` Mass assignment | Needs to submit objects and observe binding |
| `API-006` BOLA / IDOR | Needs two users' tokens to prove cross-object access |
| `API-010` JWT misconfiguration | Only surface indicators are visible |
| `API-011` API overfetching | Needs business context to judge "excess" |
| `API-014` Injection probe | Benign, detection-only; not an exploit |
| `API-001` Rate limiting | Inferred from a bounded burst; absence of 429 ≠ proof |
| `API-003` Unauthenticated data exposure | "Intended to be protected?" needs confirmation |
| `AUT-002` Broken function-level auth | Needs privileged/unprivileged comparison |
| `AUT-003` Weak password-reset token | Would require initiating a reset flow (out of scope) |
| `AUT-004` Session not invalidated on logout | Requires an authenticated session |
| `AUT-005` Weak auth handling | Surface indicators only |
| `AUT-006` Default credentials | **Passive** detection only — CAWASMA never submits credentials |
| `AUT-007` OAuth2 open redirect | Indicator-based; needs manual confirmation |
| `TLS-001` Legacy TLS 1.0/1.1 | May be inconclusive if the client's OpenSSL blocks legacy protocols |
| `CKI-006` Low token entropy | Estimated from length — heuristic |
| `HDR-012` Expect-CT | Deprecated; reported for completeness only |

What CAWASMA will **never** do: claim BOLA is exploitable, claim mass assignment
exists, or claim authentication is broken, unless safe evidence actually supports
it.

## OWASP API Security Top-10 coverage

| OWASP API risk | CAWASMA coverage |
|----------------|------------------|
| API1 — BOLA / IDOR | covered (surface signal + limitation) |
| API2 — Broken Authentication | covered (indicators) |
| API3 — Mass Assignment / BOPLA | covered (surface signal + limitation) |
| API4 — Rate Limiting | covered (bounded probe) |
| API5 — Function-Level Authorization | partial |
| API6 — Business Flow abuse | out of scope |
| API7 — SSRF (of the target) | out of scope *(CAWASMA protects **itself** against SSRF)* |
| API8 — Security Misconfiguration | **core focus** |
| API9 — Inventory Management | partial (endpoint discovery, deprecated/versioning checks) |
| API10 — Unsafe Consumption | out of scope |

CAWASMA does not claim full coverage of categories that require functionality
outside its defensive black-box scope.

## Protocol scope

CAWASMA targets **web applications and REST APIs**. It intentionally does **not**
perform full SOAP, GraphQL, gRPC or WebSocket security auditing. GraphQL
introspection detection is included as one check (`API-012`), but CAWASMA is not a
full GraphQL scanner.

## Project limitations (general)

- Results reflect a point-in-time, unauthenticated view of the target.
- The NLP embedding layer and the optional LLM require extra setup; without them
  the explainable keyword layers are used.
- PDF reports need WeasyPrint's native libraries (present in the Docker image).
- CAWASMA is a defensive analysis aid, not a replacement for manual penetration
  testing or authenticated assessment.
