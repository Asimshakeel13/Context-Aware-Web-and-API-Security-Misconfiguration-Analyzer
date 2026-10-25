# CAWASMA — Asim

> Imported from the team PDF `CAWASMA_plan_asim.pdf` (local copy in `pdf/`, not committed). Converted to Markdown on 2026-10-25; tables and lists are kept, page headers dropped.

Security, ML/NLP & evaluation Per-Person Development Plan · 22 October 2026 · Shoaib Younas

## Your place in the team

| Partner | Role | Owns |
|---|---|---|
| Atta Ur Rehman (A) | Backend & scanner engine | engine, crawler, checks (implementation), cvss, FastAPI, Celery/async, DB; half of Docker/CI |
| Neelam (B) | Frontend & shared DevOps | Next.js dashboard, API integration, export UI; half of Docker/CI |
| Asim (C) | Security & ML/NLP & evaluation | Check specs, CVSS mapping, chain templates, NLP classifier, body classifier, evaluation |

Asim specifies the security logic and Atta codes it; Docker/CI is shared between Atta and Neelam. Three people work in parallel only if the interfaces between them are fixed early — agree the contracts below in Sprint 1. **How scoring works (one line).** Final severity = the check's base CVSS v3.1 vector recomputed through the environmental metrics, where the NLP-derived endpoint sensitivity class and response-body signals raise the Confidentiality/Integrity Requirement — one standards-valid 0–10 score that reflects what is exposed and where. This is the context-aware scoring Burp/ZAP/Nikto lack.

## Shared contracts (agree in Sprint 1)

1. **Check specification (Asim → Atta).** One spec per check in a `checks.yaml`: `check_id`, category, what it detects, the exact HTTP condition, OWASP/CWE map, base CVSS v3.1 vector. Asim writes it; Atta implements the function + its fire/no-fire test.
2. **FINDING schema (shared).** `id, endpoint_id, check_id, owasp_map, cwe_map, cvss_vector, base_score, final_score, severity_bucket,` `evidence`. Atta produces it, Asim's scoring fills the vector/score, Neelam renders it.
3. **API contract (Atta → Neelam).** Freeze endpoints + example JSON in Sprint 1 so Neelam builds against a mock: `POST /api/scan`, `GET /api/results/{id}`, `GET /api/results/{id}/export?format=...`.
4. **Classifier + signals (Asim → cvss).** `sensitivity.py` returns a class; `body_classifier.py` returns signal flags. Asim designs the class/signals → CVSS environmental (CR/IR) mapping; Atta's `cvss.py` applies it.
5. **Shared DevOps (Atta + Neelam).** Co-own `docker-compose.yml` and CI; pair on Phase 0. Asim's evaluation targets live in a separate `docker-compose.eval.yml`.

## Your plan — Security, ML/NLP & evaluation

You are the security brain of the project and own the parts that make CAWASMA novel and defensible — the scoring logic, the chains, and the evaluation that produces the jury's numbers. The Python here is light and library-driven; the heavy lifting is security knowledge and careful data work. Pair with Atta whenever Python glue is needed.

### What you own

Check **specifications**, the CVSS environmental mapping, the chain templates, `sensitivity.py` (NLP classifier), `body_classifier.py` (PII/secrets detection), the hand-labelled endpoint dataset, the ground-truth finding lists, and the full evaluation (precision/recall/FPR + ZAP/Nuclei baselines). You also maintain the vulnerable-target Docker file.

### Task breakdown

- **Check specifications (biggest early task).** For each check, write the spec Atta implements: what it detects, the exact HTTP condition, the OWASP/CWE map, the base CVSS v3.1 vector. Pure security knowledge, and it gates Atta's work — front-load it in Sprint 1.
- **CVSS environmental mapping.** Design how sensitivity class + response signals map to CVSS environmental metrics (class → Confidentiality/Integrity Requirement; credential leak → CR High). Atta codes it; you own its correctness. This replaces the old multiplier and makes the score defensible.
- **Chain templates.** Define the five templates — which findings chain, why, and the composite score — each with a one-line justification. Atta codes the trigger logic; you supply the reasoning.
- **sensitivity.py (ML/NLP).** Load all-MiniLM-L6-v2 (sentence-transformers), define 4 class anchors, embed the path, cosine-similarity to the nearest. The Python is short and library-driven. The real work is tuning anchors and **hand-labelling 150–300 endpoint paths** to measure accuracy + confusion matrix.
- **body_classifier.py.** spaCy + regex to detect credentials, PII, financial data, internal IPs. Mostly pattern/domain work.
- **Evaluation (your headline deliverable).** Stand up Juice Shop/DVWA/VAmPI/crAPI in Docker; write ground-truth lists; compute precision/recall/FPR; run ZAP and Nuclei as baselines; produce the comparison tables and the before/after ranking experiment. Security tools you already know — no heavy coding.
- **Tool security review.** Check CAWASMA's own safety: SSRF guard, passive-only, authorisation gate, no secret leakage.

### Your sprint-by-sprint

| Sprint | Your tasks |
|---|---|
| 1 | Lit review; write the check specs (full set); design the CVSS environmental mapping and the 5 chain templates + justifications |
| 2 | Stand up vulnerable targets in Docker; write ground-truth lists; start hand-labelling endpoints; build sensitivity.py (pair with Atta on the Python) |
| 3 | Finish + measure the classifier (accuracy, confusion matrix); build body_classifier.py ; define chain-trigger logic for Atta; validate check outputs vs ground truth |
| 4 | Run evaluation on all targets; tool security review (SSRF, passive-only, auth gate) |
| 5 | Full precision/recall/FPR vs ZAP + Nuclei; before/after ranking experiment; tune anchors/patterns to cut false positives |
| 6 | Final results tables; security sign-off; help with the demo |

### What to learn

- **Light Python** for the ML pieces: load a sentence-transformer, encode text, cosine similarity, plus basic spaCy/regex — ~10–20 line patterns. Lean on Atta for setup, then it's your domain tuning.
- The CVSS environmental metric group (plays to your security background).
- The DevOps you're studying helps with the vulnerable-target Docker file.

### Your dependencies

- **You need from Atta:** help wiring the ML scripts into the pipeline and the Python scaffolding for `sensitivity.py` / `body_classifier.py`; the FINDING shape to validate against.
- **Others need from you:** check specs + base CVSS vectors + class→CR/IR mapping (Atta, Sprint 1 — this blocks him, so it's urgent); the classifier/body/chain outputs (Atta, Sprint 3); the evaluation numbers (whole team).

### Your definition of done

Every check has a spec and a ground-truth expectation; the classifier has a measured accuracy; the scoring mapping is designed and validated; chains are justified; and there's a precision/recall/FPR table comparing CAWASMA to ZAP and Nuclei, plus a before/after ranking result. Those numbers are what the project is judged on — they're yours.

## The two moments the whole team must sync

1. **End of Sprint 1 — contracts frozen.** API contract, FINDING shape, check-spec format, and the CVSS mapping all agreed and written down.
2. **End of Sprint 2 — vertical slice works.** One URL produces one scored finding on the dashboard, with the eval harness live. If this slips, everything after compresses — protect it.
