# Attack-chain templates: trigger logic

For Atta, from Asim. The five templates live in
[`config/chains.yaml`](../config/chains.yaml) (format: [cvss-mapping-contract.md](cvss-mapping-contract.md),
section 3). This page says how the engine should decide that a chain fired,
and what it should store. The chain vectors are a **draft** for Asim's review.

| Chain | Fires when | Scope | Score |
|-------|-----------|-------|------:|
| C001 Session theft via XSS | HttpOnly missing **and** (CSP missing **or** unsafe) | same host | 9.3 |
| C002 Error disclosure + version banner | (stack trace **or** debug page) **and** (server **or** framework banner) | same host | 5.6 |
| C003 Credentialed CORS read on a sensitive API | (origin reflected **or** credentials with weak origin) on a HIGH/CRITICAL endpoint | same endpoint | 8.1 |
| C004 Credential interception on login | HSTS missing **and** no HTTP→HTTPS redirect, on a host with a HIGH/CRITICAL endpoint | same host | 6.8 |
| C005 Exposed configuration leaks live credentials | (.env **or** .git exposed) **and** the response contains credentials | same endpoint | 10.0 |

Every chain scores above all of its members (SRS O4); the validator rejects one that doesn't.

## General algorithm

```text
input:  scan findings  (check_id, endpoint_id or null, host)
        endpoints      (id, host, sensitivity_class, body_signals)
        templates      (config/chains.yaml)
output: attack_chains rows + chain_findings links

for each template T:
    units = scope units of the scan for T.scope:
              same_endpoint -> each endpoint
              same_host     -> each host
              any_endpoint  -> the whole scan (one unit)
    for each unit U:
        F = findings in U
            # host-level findings (endpoint_id null, e.g. TLS-005) belong to every
            # endpoint and to the host of their scan
        matched = [ [f in F where f.check_id in G] for G in T.groups ]
        if any group in matched is empty:            continue
        M = all findings in matched                  # the members
        if T.endpoint_sensitivity and no endpoint in U has a class in it:
                                                     continue
        if T.body_signals and no member's endpoint shows one of them:
                                                     continue
        emit chain(T, U, M)                          # once per template per unit
```

`emit` stores one `attack_chains` row (`chain_code` = `T.chain_id`,
`template_composite_score` = the base score of `T.composite_cvss_vector`,
`severity` = `T.severity`) and one `chain_findings` link per member.

For `endpoint_sensitivity` on a **same_host** chain (C004), "an endpoint in U"
means any endpoint on that host, not only one carrying a member finding: the
login page is what makes the missing HSTS dangerous, even if the finding was
reported on `/`. For **same_endpoint** chains it is the endpoint itself.

## Per chain

**C001 Session theft via XSS** (same host)

```text
inputs:    findings on host H
condition: exists CKI-001 on H  and  exists (HDR-002 or HDR-013) on H
output:    chain C001, members = those findings
```

**C002 Error disclosure plus version banner** (same host)

```text
condition: exists (API-004 or INF-007) on H  and  exists (HDR-007 or HDR-008) on H
```

**C003 Credentialed CORS read on a sensitive API** (same endpoint)

```text
inputs:    findings and sensitivity class of endpoint E
condition: exists (COR-002 or COR-003) on E  and  E.sensitivity_class in {HIGH, CRITICAL}
```

**C004 Credential interception on login** (same host)

```text
condition: exists HDR-001 on H  and  exists TLS-005 on H (host-level)
           and  some endpoint of H has sensitivity_class in {HIGH, CRITICAL}
```

**C005 Exposed configuration leaks live credentials** (same endpoint)

```text
condition: exists (INF-003 or INF-004) on E  and  CREDENTIALS in E.body_signals
```

## How a chain appears in the data

- **Finding:** members are linked through `chain_findings`, so the API's
  `Finding.chain_ids` lists every chain a finding belongs to. Also add a short
  reference to each member's `evidence`, so a single finding still explains
  itself:

  ```json
  "evidence": {"text": "...", "chains": [{"chain_id": "C005", "name": "Exposed configuration leaks live credentials"}]}
  ```

- **Chain:** store why it fired. `attack_chains` has no evidence column today, so
  this needs a small migration (Atta). Suggested JSON:

  ```json
  {"scope": {"kind": "endpoint", "value": "https://shop.example.com/.env"},
   "groups": [["INF-003"]],
   "context": {"body_signals": ["CREDENTIALS"]},
   "composite_cvss_vector": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:C/C:H/I:H/A:H"}
  ```

  `groups` lists the matched check ids per group, and `context` records which
  sensitivity class or body signal satisfied the condition.

## Weak spots to defend (or drop) before the jury

- **C002 is the weakest.** Banners plus error pages are reconnaissance, not an
  exploit path; "targeted exploitation" assumes a matching vulnerability exists.
  Its score (5.6) barely clears its members (5.3), and the vector is mostly a
  judgement. Consider presenting it as context, or dropping it.
- **C001 assumes an injection point.** No check proves XSS, so `AC:L` and
  `S:C/C:H/I:H` are generous; `AC:H` would score 8.0, which no longer exceeds
  `CKI-001` (8.1) and so would fail O4. Be ready to say why the chain holds
  without a confirmed injection.
- **C004 can't be confirmed passively.** It needs an on-path attacker that the
  scanner can't demonstrate, and "login endpoint" depends on the sensitivity
  classifier being right. `AV:A` is a defensible alternative (6.4).
- **C003 depends on the classifier** marking the endpoint HIGH/CRITICAL. A
  misclassified public endpoint means no chain, and vice versa.
- **C005 is the strongest:** both conditions are observed directly in one
  response.
