// Mock dataset used only when the backend is unreachable, so the UI can still
// be demonstrated (viva-safe). The app shows a clear "demo data" banner when
// this is active. All shapes mirror the real API responses exactly.

const now = new Date().toISOString();

const SCAN_ID = "demo-0000-0000-0000-000000000001";

const endpoints = [
  { id: "e1", url: "https://demo.target/api/payment/checkout", path: "/api/payment/checkout", method: "GET", status_code: 200, content_type: "application/json", context_class: "CRITICAL", context_confidence: 0.94, context_reason: ["Contains payment/financial tokens"], response_time: 0.21, discovered_by: "HTML", created_at: now },
  { id: "e2", url: "https://demo.target/api/v2/usr/auth/mfa/verify", path: "/api/v2/usr/auth/mfa/verify", method: "GET", status_code: 200, content_type: "application/json", context_class: "HIGH", context_confidence: 0.81, context_reason: ["Contains authentication/session tokens"], response_time: 0.18, discovered_by: "JAVASCRIPT", created_at: now },
  { id: "e3", url: "https://demo.target/.env", path: "/.env", method: "GET", status_code: 200, content_type: "text/plain", context_class: "MEDIUM", context_confidence: 0.6, context_reason: ["No sensitive tokens detected; treated as low-sensitivity"], response_time: 0.09, discovered_by: "WORDLIST", created_at: now },
  { id: "e4", url: "https://demo.target/about", path: "/about", method: "GET", status_code: 200, content_type: "text/html", context_class: "LOW", context_confidence: 0.7, context_reason: ["Public/informational path"], response_time: 0.12, discovered_by: "HTML", created_at: now },
  { id: "e5", url: "https://demo.target/api/users/123", path: "/api/users/123", method: "GET", status_code: 200, content_type: "application/json", context_class: "HIGH", context_confidence: 0.78, context_reason: ["Contains user/account tokens"], response_time: 0.15, discovered_by: "RECURSIVE", created_at: now },
];

const f = (o) => ({ context_confidence: 0.9, references: [], limitation: null, created_at: now, ...o });

const findings = [
  f({ id: "F1", rule_id: "INF-003", title: ".env file exposed", category: "INFO_DISCLOSURE", endpoint_id: "e3", context_class: "MEDIUM", cvss_vector: "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:N/A:N", cvss_base_score: 9.1, cawasma_context_multiplier: 1.0, response_bonus: 3.5, cawasma_final_score: 10.0, severity: "CRITICAL", evidence: "Exposed .env with environment variables (values redacted).", impact: "Environment file may expose secrets and credentials.", recommendation: "Block access to dotfiles; move secrets out of web root." }),
  f({ id: "F2", rule_id: "API-013", title: "Secrets in API response", category: "REST_API", endpoint_id: "e3", context_class: "MEDIUM", cvss_vector: "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:N/A:N", cvss_base_score: 8.6, cawasma_context_multiplier: 1.0, response_bonus: 3.5, cawasma_final_score: 10.0, severity: "CRITICAL", evidence: "Credential-like secret detected: SECRET_KEY=████████", impact: "Response body contains credential-like secrets.", recommendation: "Remove secrets from responses; rotate any exposed values." }),
  f({ id: "F3", rule_id: "HDR-003", title: "Missing X-Frame-Options", category: "HEADERS", endpoint_id: "e1", context_class: "CRITICAL", cvss_vector: "CVSS:3.1/AV:N/AC:L/PR:N/UI:R/S:C/C:L/I:L/A:N", cvss_base_score: 6.1, cawasma_context_multiplier: 2.0, response_bonus: 0, cawasma_final_score: 10.0, severity: "CRITICAL", evidence: "No X-Frame-Options and no CSP frame-ancestors.", impact: "Page can be framed, enabling clickjacking.", recommendation: "Set 'X-Frame-Options: DENY' or a CSP frame-ancestors directive." }),
  f({ id: "F4", rule_id: "COR-002", title: "CORS origin reflection", category: "CORS", endpoint_id: "e1", context_class: "CRITICAL", cvss_vector: "CVSS:3.1/AV:N/AC:L/PR:N/UI:R/S:C/C:H/I:N/A:N", cvss_base_score: 7.5, cawasma_context_multiplier: 2.0, response_bonus: 0, cawasma_final_score: 10.0, severity: "CRITICAL", evidence: "Origin reflected: ACAO echoed probe origin.", impact: "Arbitrary origins reflected, enabling cross-origin data theft.", recommendation: "Validate Origin against an allow-list; do not echo it." }),
  f({ id: "F5", rule_id: "CKI-001", title: "Cookie missing HttpOnly flag", category: "COOKIES", endpoint_id: "e2", context_class: "HIGH", cvss_vector: "CVSS:3.1/AV:N/AC:L/PR:N/UI:R/S:U/C:L/I:N/A:N", cvss_base_score: 5.3, cawasma_context_multiplier: 1.5, response_bonus: 0, cawasma_final_score: 8.0, severity: "HIGH", evidence: "Cookie 'session' lacks HttpOnly.", impact: "Cookie readable by JavaScript, aiding token theft via XSS.", recommendation: "Set the HttpOnly attribute on session cookies." }),
  f({ id: "F6", rule_id: "API-006", title: "Possible BOLA / IDOR", category: "REST_API", endpoint_id: "e5", context_class: "HIGH", cvss_vector: "CVSS:3.1/AV:N/AC:L/PR:L/UI:N/S:U/C:H/I:N/A:N", cvss_base_score: 6.5, cawasma_context_multiplier: 1.5, response_bonus: 0, cawasma_final_score: 9.8, severity: "CRITICAL", evidence: "Numeric object identifier in path: /api/users/123", impact: "Object identifiers may be accessible across users.", recommendation: "Enforce per-object authorization checks.", limitation: "Not determinable from unauthenticated black-box analysis." }),
  f({ id: "F7", rule_id: "HDR-001", title: "Missing HSTS", category: "HEADERS", endpoint_id: "e2", context_class: "HIGH", cvss_vector: "CVSS:3.1/AV:N/AC:H/PR:N/UI:N/S:U/C:H/I:N/A:N", cvss_base_score: 5.9, cawasma_context_multiplier: 1.5, response_bonus: 0, cawasma_final_score: 8.9, severity: "HIGH", evidence: "Response has no Strict-Transport-Security header.", impact: "Allows protocol-downgrade / MITM interception.", recommendation: "Send 'Strict-Transport-Security: max-age=31536000; includeSubDomains'." }),
  f({ id: "F8", rule_id: "HDR-002", title: "Missing Content-Security-Policy", category: "HEADERS", endpoint_id: "e4", context_class: "LOW", cvss_vector: "CVSS:3.1/AV:N/AC:L/PR:N/UI:R/S:C/C:L/I:L/A:N", cvss_base_score: 6.1, cawasma_context_multiplier: 0.6, response_bonus: 0, cawasma_final_score: 3.7, severity: "LOW", evidence: "Response has no Content-Security-Policy header.", impact: "Increases exploitability of XSS and content injection.", recommendation: "Define a restrictive Content-Security-Policy." }),
];

const chains = [
  { id: "c1", chain_code: "C005", name: ".env Exposure → Version Leak → Full Compromise", description: "An exposed .env combined with version disclosure can lead to full compromise.", template_composite_score: 9.8, severity: "CRITICAL", created_at: now },
  { id: "c2", chain_code: "C003", name: "CORS → CSRF → Privilege Escalation", description: "Reflective/credentialed CORS plus missing SameSite enables cross-site request forgery toward privileged actions.", template_composite_score: 9.6, severity: "CRITICAL", created_at: now },
];

const summary = { endpoints: 5, findings: 8, critical: 5, high: 2, medium: 0, low: 1, info: 0 };

const scan = {
  id: SCAN_ID, target_url: "https://demo.target", status: "COMPLETED", progress: 100,
  current_stage: "completed", started_at: now, completed_at: now, duration_seconds: 7.4,
  error_message: null, created_at: now, updated_at: now, summary,
};

export const MOCK = {
  health: { status: "demo", service: "cawasma-backend", dependencies: {} },
  scans: [scan],
  scan,
  endpoints,
  findings,
  chains,
  SCAN_ID,
};
