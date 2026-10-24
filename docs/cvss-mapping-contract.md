# Context → CVSS mapping contract, version 1.0.0

What Asim's code and config must provide so the engine can turn a check's
CVSS v3.1 **base** vector into a **context-aware** score through CVSS v3.1
environmental metrics. Owners: Asim provides the classifiers and the two YAML
files; Atta's engine calls them and computes the scores.

```
endpoint ──classify()──▶ SensitivityClass ─┐
                                           ├─▶ cvss_mapping.yaml ─▶ CR / IR / AR ─▶ environmental score
response ──analyze()───▶ set[BodySignal] ──┘        (combine: max)                 (engine, cvss31.py)
```

> **Status:** the engine still scores with the interim multiplier formula
> (docs/06-scoring-model.md). The types, the conformance check and the file
> validators below are in place now; the engine switches to environmental
> scoring once `cvss_mapping.yaml` is filled in.

## 1. Interfaces Asim's code provides

All types are defined in `backend/app/core/contracts.py`. **Import them from
there and do not redefine them**, so both sides always agree.

```python
from app.core.contracts import (
    BodySignal, EndpointInfo, ResponseInfo, SensitivityClass,
)

# backend/app/ml/sensitivity.py
def classify(endpoint: EndpointInfo) -> SensitivityClass: ...

# backend/app/ml/body_classifier.py
def analyze(response: ResponseInfo) -> set[BodySignal]: ...
```

### Types

| Type | Values / fields |
|------|-----------------|
| `SensitivityClass` | `CRITICAL`, `HIGH`, `MEDIUM`, `LOW` (enum) |
| `BodySignal` | `CREDENTIALS` (passwords, keys, tokens), `PII` (emails, phones, national IDs), `FINANCIAL` (Luhn-valid cards, IBANs), `INTERNAL_IP` (RFC 1918, loopback, link-local) |
| `EndpointInfo` | `url` (absolute), `path`, `method` (default `GET`), `status_code` (int or None), `content_type` (str or None) |
| `ResponseInfo` | `url`, `status_code`, `content_type` (str or None), `headers` (mapping), `body` (decoded text, already truncated to `MAX_RESPONSE_SIZE`; `""` for binary) |

### Rules both functions must follow

1. **Never raise.** On any internal failure return the safe default:
   `SensitivityClass.MEDIUM` from `classify` (neutral weighting) and `set()`
   from `analyze`, and log the error.
2. **Deterministic**: same input, same output. No randomness at call time.
3. **No network calls.** Load models once (at import or on first call) from
   local files baked into the image; nothing is downloaded during a scan.
4. **Fast**: target ≤ 50 ms per call on CPU after warm-up. A scan makes up to
   200 calls of each.
5. **Never log or store the raw body.** Evidence is redacted by the engine;
   `analyze` returns only signals.
6. **Handle edge cases**: empty body, binary content, non-UTF-8 text, paths up to
   2048 characters, `content_type` of `None`.
7. **Import cleanly without the ML extras** (`INSTALL_ML=false` images), or let
   the import fail. The engine then falls back to the built-in classifiers.

### Conformance check

`check_conformance(classify, analyze)` in `app/core/contracts.py` verifies
return types, determinism and edge-case inputs (not accuracy, which is your
evaluation). It must return `[]`. The built-in implementations
(`builtin_classify`, `builtin_analyze`) already pass it
(`backend/tests/unit/test_specs.py`). Add the same test for your modules:

```python
from app.core.contracts import check_conformance
from app.ml import body_classifier, sensitivity

def test_ml_modules_conform():
    assert check_conformance(sensitivity.classify, body_classifier.analyze) == []
```

`backend/app/ml/interfaces.py` (the Sprint 0 stub with the old
`classify(path, extra_expansions)` signature) is superseded by this contract.
It's your file, so delete or replace it when you start.

## 2. `config/cvss_mapping.yaml`

Maps each sensitivity class and each body signal to CVSS v3.1 **Security
Requirements**: Confidentiality (`CR`), Integrity (`IR`), Availability (`AR`).

```yaml
mapping_version: 1

sensitivity_classes:          # every SensitivityClass must have a row
  CRITICAL: {CR: H, IR: H, AR: M}
  HIGH:     {CR: H, IR: M, AR: L}
  MEDIUM:   {CR: M, IR: M, AR: M}
  LOW:      {CR: L, IR: L, AR: L}

body_signals:                 # every BodySignal must have a row
  CREDENTIALS: {CR: H, IR: H, AR: X}
  PII:         {CR: H, IR: X, AR: X}
  FINANCIAL:   {CR: H, IR: H, AR: X}
  INTERNAL_IP: {CR: M, IR: X, AR: X}

combine: max
```

(The values above only illustrate the syntax. The committed file is a template
with every value `X`, so scores are unchanged until Asim fills it in.)

| Key | Rule |
|-----|------|
| `mapping_version` | `1` |
| `sensitivity_classes` | exactly the 4 classes, each `{CR, IR, AR}` |
| `body_signals` | exactly the 4 signals, each `{CR, IR, AR}` |
| values | `L` (Low, ×0.5), `M` (Medium, ×1.0), `H` (High, ×1.5), `X` (Not Defined: no change, treated like M by CVSS) |
| `combine` | `max` (the only value in v1) |

**How the engine combines them (`max`):** for each of CR, IR and AR separately,
it takes the highest value among the endpoint's class row and the rows of
every detected signal, ordering `L < M < H`; `X` rows contribute nothing, and if
all are `X` the result is `X`.

Example: a `HIGH` endpoint {CR: H, IR: M, AR: L} whose response has `PII`
{CR: H, IR: X, AR: X} gives **CR: H, IR: M, AR: L**. With `CREDENTIALS`
{CR: H, IR: H, AR: X} it gives **CR: H, IR: H, AR: L**.

The engine then appends `CR/IR/AR` to the check's base vector (modified base
metrics stay equal to the base metrics) and computes the CVSS v3.1
environmental score. That is the finding's `final_score`. The official
`base_score` is stored separately and never changed.

## 3. `config/chains.yaml`

Attack-chain templates: findings that together form a worse exploitation path.

```yaml
chains_version: 1
chains:
  - chain_id: C005
    name: .env Exposure -> Version Leak -> Full Compromise
    description: >-
      An exposed .env file combined with server version disclosure can lead to
      full compromise.
    requires: [INF-003, HDR-007, INF-004]
    mandatory: [INF-003]
    min_matches: 2
    composite_score: 9.8
    severity: CRITICAL
```

| Field | Rule |
|-------|------|
| `chain_id` | `C` + 3 digits, unique |
| `name` | 3–255 chars |
| `description` | ≥ 10 chars |
| `requires` | ≥ 2 distinct check ids that can contribute; each must exist in `checks.yaml` or the catalog |
| `mandatory` | subset of `requires`; all must be present for the chain to fire (may be empty) |
| `min_matches` | how many of `requires` (counting mandatory ones) must be present; `len(mandatory) ≤ min_matches ≤ len(requires)` |
| `composite_score` | 0–10: the documented template score for this pattern, **not** a computed CVSS |
| `severity` | must equal the bucket of `composite_score` (`CRITICAL` ≥ 9.0, `HIGH` ≥ 7.0, `MEDIUM` ≥ 4.0, `LOW` ≥ 0.1) |

A chain fires for a scan when every `mandatory` check and at least
`min_matches` of `requires` produced findings. Every matching finding becomes a
member of the chain.

The committed file contains one example (C005). The engine keeps using the five
templates in `backend/app/core/chains.py` until this file holds the full set.
Moving C001–C004 over is part of filling it in.

## Validation

```bash
make validate-config
```

This checks both files (and `checks.yaml`): unknown keys, missing classes or
signals, invalid values, chain consistency and unknown check ids. CI runs it on
every push. Models: `backend/app/core/specs.py`.

## Versioning

`ML_CONTRACT_VERSION` (`app/core/contracts.py`) and the `*_version` keys in the
files are bumped together with this document. Adding a `BodySignal` is a minor
change: add its row to `cvss_mapping.yaml` in the same PR, or validation fails.
Changing a function signature or removing a value is a major change; agree it
between Atta and Asim first.
