# 01 — Overview

## What CAWASMA is

CAWASMA (Context-Aware Web and API Security Misconfiguration Analyzer) is a
defensive security tool that scans a web application or REST API for security
**misconfigurations** and reports them, ranked by risk. The analyst supplies a
single HTTPS URL; CAWASMA does the rest without any source code, credentials, or
agent installed on the target. It is therefore a **black-box** scanner suitable
for authorized security testing.

## Problem statement

Modern web and API deployments fail far more often through *misconfiguration*
(missing security headers, permissive CORS, exposed `.env` files, weak TLS,
unauthenticated data endpoints) than through exotic zero-day vulnerabilities.
Existing scanners detect many of these issues, but they almost always score a
finding the **same way no matter where it occurs**. A missing security header on
a public marketing page is treated with the same urgency as the same header
missing on a payment or authentication endpoint. This floods analysts with
findings that are technically correct but poorly prioritized.

## Research gap

The gap CAWASMA addresses is **prioritization, not detection**. Two questions are
usually ignored by conventional tools:

1. *Where* does the finding occur — how sensitive is that endpoint?
2. *What* does the endpoint's response expose — credentials, PII, financial data?

A finding on a sensitive endpoint that returns sensitive data is genuinely more
dangerous than the identical finding on a trivial page. CAWASMA encodes this
reasoning explicitly and transparently.

## The core novelty — context-aware risk prioritization

CAWASMA combines four signals into a single, explainable risk score:

```
Finding  →  Endpoint context  →  Response sensitivity  →  Attack-chain membership  →  Context-aware score  →  Priority
```

Concretely, the same finding is scored differently depending on context:

| Finding | Endpoint | Context | Final score |
|---------|----------|---------|:-----------:|
| Missing X-Frame-Options | `/about` | LOW | **3.7** (LOW) |
| Missing X-Frame-Options | `/api/payment/checkout` | CRITICAL | **10.0** (CRITICAL) |

Same vulnerability, very different urgency — and CAWASMA shows exactly how it got
there (see [Scoring Model](06-scoring-model.md)).

## What it is *not*

CAWASMA is strictly defensive. It never performs destructive exploitation, brute
force, denial of service, account takeover, credential theft, or state-changing
attacks. It prefers `GET`/`HEAD`/`OPTIONS` and uses other methods only for safe,
non-destructive detection. Where a weakness cannot be confirmed from
unauthenticated black-box analysis, CAWASMA says so honestly rather than
pretending (see [Limitations](10-limitations-owasp.md)).

## Three novel contributions

1. **NLP endpoint sensitivity classification** — classifies each discovered
   endpoint as CRITICAL / HIGH / MEDIUM / LOW from its URL, with explainable
   reasons.
2. **Attack-chain correlation** — detects when individual findings combine into a
   higher-impact exploitation path.
3. **Response-body sensitivity classification** — detects credentials, PII,
   financial data and internal IPs in responses (redacted) and raises risk
   accordingly.

Each is described in [Novel Contributions](07-novel-contributions.md).
