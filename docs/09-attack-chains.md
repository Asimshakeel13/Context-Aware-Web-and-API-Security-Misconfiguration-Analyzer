# 09 — Attack Chains (Contribution 2)

An **attack chain** models how several individually-modest findings combine into a
single high-impact exploitation path. CAWASMA ships **five predefined templates**.

### Firing rules (no false chains)

A chain is reported **only when** its *mandatory* member findings are present, plus
enough of its *required* set. If the required findings were not actually detected,
the chain does **not** fire — CAWASMA never claims a chain exists without evidence.
Each chain also records exactly which rule IDs matched.

### Composite score

Each chain carries a documented **template composite score** — the known
severity of that pattern. This is stored on the chain record
(`template_composite_score`), **separate** from any individual finding's score, and
appears as its own item in the database and reports (findings and chains are never
mixed).

## The five templates

#### C001 — XSS -> Cookie Theft -> Account Takeover

- **Composite score:** 9.4 (CRITICAL)
- **Fires when:** mandatory rules `CKI-001` present, plus enough of `HDR-002, HDR-003, CKI-001`
- **Description:** Missing XSS/framing protections plus a JS-readable session cookie create an XSS-to-account-takeover path.

#### C002 — Information Disclosure -> Targeted Exploit

- **Composite score:** 8.2 (HIGH)
- **Fires when:** mandatory rules `—` present, plus enough of `HDR-007, HDR-008, INF-002, API-004`
- **Description:** Version/stack disclosure combined with a directory/info leak enables targeted exploitation.

#### C003 — CORS -> CSRF -> Privilege Escalation

- **Composite score:** 9.6 (CRITICAL)
- **Fires when:** mandatory rules `CKI-003` present, plus enough of `COR-002, COR-003, CKI-003`
- **Description:** Reflective/credentialed CORS plus missing SameSite enables cross-site request forgery toward privileged actions.

#### C004 — Unauthenticated Data Exposure -> BOLA -> Full Data Breach

- **Composite score:** 9.1 (CRITICAL)
- **Fires when:** mandatory rules `API-003, API-006` present, plus enough of `API-003, API-006`
- **Description:** Unauthenticated data access plus object-id enumeration indicates a broad data-breach path.

#### C005 — .env Exposure -> Version Leak -> Full Compromise

- **Composite score:** 9.8 (CRITICAL)
- **Fires when:** mandatory rules `INF-003` present, plus enough of `INF-003, HDR-007, INF-004`
- **Description:** An exposed .env combined with version disclosure can lead to full compromise.
## Summary

| Code | Chain | Composite | Severity |
|------|-------|:---------:|----------|
| C001 | XSS → Cookie Theft → Account Takeover | 9.4 | CRITICAL |
| C002 | Information Disclosure → Targeted Exploit | 8.2 | HIGH |
| C003 | CORS → CSRF → Privilege Escalation | 9.6 | CRITICAL |
| C004 | Unauthenticated Data Exposure → BOLA → Full Data Breach | 9.1 | CRITICAL |
| C005 | .env Exposure → Version Leak → Full Compromise | 9.8 | CRITICAL |

Definitions live in `app/scanner/chains.py`; correlation runs after all findings
are scored, via `correlate_chains(present_rule_ids)`.
