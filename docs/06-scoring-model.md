# 06 — Scoring Model

This is the heart of CAWASMA's novelty. Two numbers are produced for every
finding and kept **strictly separate**:

1. the official **CVSS v3.1 base score** (predefined per rule, unchanged), and
2. the CAWASMA **context-aware final score** (custom prioritization metric).

CAWASMA never claims the final number is an official CVSS score.

## The formula

```
Final score = min( 10.0 , (CVSS base × Context multiplier) + Response bonus )
```

### Context multipliers (by endpoint sensitivity)

| Endpoint context | Multiplier |
|------------------|:----------:|
| CRITICAL | × 2.0 |
| HIGH | × 1.5 |
| MEDIUM | × 1.0 |
| LOW | × 0.6 |

### Response bonuses (by what the response exposes)

| Response signal | Bonus |
|-----------------|:-----:|
| Credentials | + 3.5 |
| PII | + 2.0 |
| Financial data | + 1.5 |
| Internal / infra IP | + 2.0 |

(Values live in `app/scanner/cvss.py` as `CONTEXT_MULTIPLIERS` and
`RESPONSE_BONUS`.)

## Severity buckets

The final score maps to a severity:

| Score range | Severity |
|-------------|----------|
| 9.0 – 10.0 | CRITICAL |
| 7.0 – 8.9 | HIGH |
| 4.0 – 6.9 | MEDIUM |
| 0.1 – 3.9 | LOW |
| 0.0 | INFO |

**Special rule:** if the response body contains **credentials**, the finding's
severity is forced to **CRITICAL** regardless of the arithmetic.

## Worked examples

**Example 1 — same finding, sensitive endpoint**
Finding: *Missing X-Frame-Options* (base 6.1) on `/api/payment/checkout`
(context CRITICAL), response contains PII + financial data (bonus +2.0 used).

```
6.1 × 2.0 = 12.2
12.2 + 2.0 = 14.2
min(10.0, 14.2) = 10.0  →  CRITICAL
```

**Example 2 — same finding, trivial endpoint**
Finding: *Missing X-Frame-Options* (base 6.1) on `/about` (context LOW), no
sensitive response.

```
6.1 × 0.6 = 3.66  →  rounded 3.7  →  LOW
```

Identical vulnerability, final scores of **10.0** vs **3.7** — this is the
prioritization conventional scanners miss.

## What is stored (kept distinguishable)

Each finding row stores all of these separately, so the standard and the custom
values can never be confused:

```
cvss_vector                 e.g. CVSS:3.1/AV:N/AC:L/PR:N/UI:R/S:C/C:L/I:L/A:N
cvss_base_score             e.g. 6.1   (official)
cawasma_context_multiplier  e.g. 2.0   (custom)
response_bonus              e.g. 2.0   (custom)
cawasma_final_score         e.g. 10.0  (custom)
severity                    e.g. CRITICAL
```

## Findings vs. attack chains

A **finding** is a single issue with its own context-aware score. An **attack
chain** is a *separate* record with a documented **template composite score**
(a known pattern's severity), and it fires only when its member findings are
actually detected. The two are stored and reported separately and must not be
conflated — see [Attack Chains](09-attack-chains.md).
