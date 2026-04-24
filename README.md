# Context-Aware-Web-and-API-Security-Misconfiguration-Analyzer
CAWASMA is a black-box HTTPS security misconfiguration analyzer for web applications and REST APIs. Unlike existing scanners that assign static severity scores, CAWASMA introduces three novel contributions:
    1. NLP-Based Endpoint Sensitivity Classification — automatically infers the sensitivity of an endpoint (CRITICAL/HIGH/MEDIUM/LOW) from its URL path using pre-trained transformer embeddings. No manual configuration required.
    2. Cross-Finding Attack Chain Correlation — detects combinations of individually medium-severity findings that together form a critical exploit path, computing a composite CVSS score for the full chain.
    3. Response-Body-Aware CVSS Adjustment — scans each endpoint's response body for PII, financial data, credentials, and secrets, feeding detected sensitivity back into the CVSS scoring formula.
Key Features:
    • 58 security checks across 7 modules (headers, cookies, CORS, TLS, API, auth, info disclosure)
    • CVSS v3.1 scoring with context-aware adjustment
    • Attack chain detection (5 pre-built chains)
    • NLP endpoint classifier using all-MiniLM-L6-v2 (22MB, runs locally)
    • Flask web dashboard with live scan progress via WebSocket
    • Export reports as PDF, JSON, HTML, CSV
    • AI-generated executive summary and remediation guidance
    
