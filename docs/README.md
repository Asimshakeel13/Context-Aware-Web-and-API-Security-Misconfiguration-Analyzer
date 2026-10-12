# CAWASMA — Documentation

**Context-Aware Web & API Security Misconfiguration Analyzer**
Final Year Project — Javed Azam

This folder contains the full technical documentation for CAWASMA. Each file is
self-contained; start with the Overview and follow the order below.

| # | Document | What it covers |
|---|----------|----------------|
| 01 | [Overview](01-overview.md) | What CAWASMA is, the problem, the research gap, the novelty |
| 02 | [Architecture](02-architecture.md) | System design, process topology, data flow, technology choices |
| 03 | [Installation & Running](03-installation.md) | Setup with and without Docker, configuration, tests |
| 04 | [API Reference](04-api-reference.md) | All REST endpoints, the WebSocket, request/response shapes |
| 05 | [Security Checks (all 58)](05-security-checks.md) | Every check with its category, CVSS vector and base score |
| 06 | [Scoring Model](06-scoring-model.md) | CVSS base + context multiplier + response bonus formula |
| 07 | [Novel Contributions](07-novel-contributions.md) | The three contributions, in depth |
| 08 | [Database Schema](08-database-schema.md) | Tables, relationships, cascades |
| 09 | [Attack Chains](09-attack-chains.md) | The five chain templates and how they fire |
| 10 | [Limitations & OWASP Coverage](10-limitations-owasp.md) | Honest black-box limits, OWASP API mapping |
| 11 | [Viva Guide](11-viva-guide.md) | Likely questions and concise answers |

### Related files (project root)

- **[README.md](../README.md)** — quick project summary and build status
- **[HOW-TO-RUN.md](../HOW-TO-RUN.md)** — step-by-step run guide (Roman Urdu)

### At a glance

- **Type:** defensive, black-box, HTTPS-only web & REST-API misconfiguration scanner
- **Core novelty:** context-aware risk prioritization (not just "find bugs")
- **Checks:** 58 across 7 categories, each with a predefined CVSS v3.1 vector
- **Contributions:** (1) NLP endpoint sensitivity classification, (2) attack-chain
  correlation, (3) response-body sensitivity classification
- **Stack:** FastAPI · PostgreSQL · Redis · Celery · httpx · SQLAlchemy ·
  sentence-transformers · WeasyPrint · React (Vite) frontend
- **Tests:** 88 automated tests (unit + API + end-to-end)
