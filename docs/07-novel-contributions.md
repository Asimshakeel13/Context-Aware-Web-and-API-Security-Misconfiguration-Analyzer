# 07 — Novel Contributions

CAWASMA's academic contribution is three mechanisms that together deliver
context-aware prioritization.

---

## Contribution 1 — NLP Endpoint Sensitivity Classification

**File:** `app/scanner/sensitivity.py` (+ optional `app/services/llm.py`)

Classifies each discovered endpoint as **CRITICAL / HIGH / MEDIUM / LOW** from its
URL path, and — crucially — explains *why*. The pipeline is:

```
Endpoint URL → tokenization → abbreviation expansion
            → keyword/semantic classification → class + confidence + reasons
```

It is a **hybrid, explainable** classifier:

- A deterministic **keyword layer** produces the authoritative, human-readable
  reasons (e.g. "Contains payment/financial tokens"). This is what makes the
  output defensible in a viva — every decision has a stated cause.
- An optional **sentence-transformer layer** (`all-MiniLM-L6-v2`) adds semantic
  cosine-similarity to per-class anchor phrases, blended into the confidence.
- **Abbreviation expansion** turns short tokens into full words (`usr → user`,
  `iam → identity access management`). By default this uses a built-in table; if
  an LLM is configured it can perform the expansion instead — with the table as a
  guaranteed fallback.

**Graceful degradation:** if `sentence-transformers`/`torch` is not installed, the
classifier runs keyword-only and logs it. The scanner never depends on a model
download, so demos never break.

Output shape:
```json
{ "class": "CRITICAL", "confidence": 0.94, "reason": ["Contains payment/financial tokens"] }
```

Tier calibration matches the project's worked examples, e.g.
`/svc/iam/priv/escalate → CRITICAL`, `/api/v2/usr/auth/mfa/verify → HIGH`,
`/public/about → LOW`.

---

## Contribution 2 — Attack-Chain Correlation

**File:** `app/scanner/chains.py`

Individual low/medium findings can combine into a single high-impact path. CAWASMA
defines **five chain templates** and reports a chain **only when its required
member findings are actually detected** — never speculatively. Each chain carries
a documented *template composite score* (the known pattern's severity), stored
separately from individual findings.

See [Attack Chains](09-attack-chains.md) for all five templates and their firing
conditions.

---

## Contribution 3 — Response-Body Sensitivity Classification

**File:** `app/scanner/body_classifier.py`

Scans each response body for four safe sensitivity signals and converts them into
the response bonus used by the scoring model:

| Signal | Detection | Bonus |
|--------|-----------|:-----:|
| Credentials | JWTs, AWS keys, private keys, `KEY=…`/`PASSWORD=…` assignments | +3.5 (forces CRITICAL) |
| PII | emails, phone numbers, SSN-like patterns | +2.0 |
| Financial | IBANs, money patterns, Luhn-valid card numbers | +1.5 |
| Internal IP | RFC-1918 private addresses | +2.0 |

**Safety:** detected secrets are **never stored or displayed raw**. Only a
redacted, truncated evidence snippet is kept (`"api_key = \"████\""`). Card numbers
are Luhn-validated to reduce false positives.

---

## How the three combine

```
         Contribution 1                     Contribution 3
   endpoint context (×2.0…×0.6)        response bonus (+3.5…+1.5)
              │                                   │
              └───────────────┬───────────────────┘
                              ▼
         final = min(10, base × context + bonus)
                              │
                              ▼
                     Contribution 2
        findings correlated into attack chains
```

Together they turn a flat list of misconfigurations into a prioritized, explainable
risk picture — which is the project's core research contribution.
