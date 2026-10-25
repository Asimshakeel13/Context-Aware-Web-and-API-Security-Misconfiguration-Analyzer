"""Example data for contract v1: OpenAPI examples and ``MOCK_API=true`` responses.

Four scans, one per status, so the frontend can build every state without a
running pipeline:

=======================================  ========  =====================================
id                                       status    what it shows
=======================================  ========  =====================================
``11111111-1111-4111-8111-111111111111``  DONE      7 findings, 1 chain (full results)
``22222222-2222-4222-8222-222222222222``  RUNNING   progress 45, stage "analyzing"
``33333333-3333-4333-8333-333333333333``  QUEUED    what ``POST /api/scan`` returns
``44444444-4444-4444-8444-444444444444``  FAILED    error message set
=======================================  ========  =====================================

Values are built through the real schemas (validated at import) and scored with
the real CVSS code, so they cannot drift from the contract.
"""
from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

from app.api.schemas.contract import (
    Chain,
    Finding,
    ScanOptions,
    ScanResults,
    ScanState,
    ScanStatus,
    SeverityCounts,
)
from app.core.checks.catalog import CATALOG
from app.core.contracts import BodySignal, SensitivityClass
from app.core.checks.registry import CHECKS, load_implementations, spec_for
from app.core.cvss import compute_score, environmental_score
from app.core.cvss31 import base_score

DONE_ID = uuid.UUID("11111111-1111-4111-8111-111111111111")
RUNNING_ID = uuid.UUID("22222222-2222-4222-8222-222222222222")
QUEUED_ID = uuid.UUID("33333333-3333-4333-8333-333333333333")
FAILED_ID = uuid.UUID("44444444-4444-4444-8444-444444444444")

TARGET = "https://shop.example.com"
_T0 = datetime(2026, 10, 20, 9, 0, tzinfo=UTC)
_CHAIN_ID = uuid.UUID("c0050000-0000-4000-8000-000000000001")


def _uid(n: int) -> uuid.UUID:
    return uuid.UUID(f"f0000000-0000-4000-8000-{n:012d}")


# (n, check_id, endpoint path or None, class, body signals, bonus, force CRITICAL, owasp, cwe,
#  evidence)
_FINDINGS = [
    (1, "INF-003", "/.env", SensitivityClass.LOW,
     [BodySignal.CREDENTIALS, BodySignal.INTERNAL_IP], 5.5, True,
     ["API8:2023"], ["CWE-538"],
     {"text": ".env file exposed on /.env", "status": 200,
      "body_excerpt": "DB_HOST=10.0.3.17\nDB_PASSWORD=[REDACTED]"}),
    (2, "API-003", "/api/v1/users/42", SensitivityClass.HIGH, [BodySignal.PII], 2.0, False,
     ["API2:2023"], ["CWE-306"],
     {"text": "Unauthenticated data exposure on /api/v1/users/42", "auth_header_sent": False}),
    (3, "HDR-002", "/api/payment/checkout", SensitivityClass.CRITICAL,
     [BodySignal.PII, BodySignal.FINANCIAL], 0.0, False, ["API8:2023"], ["CWE-693"],
     {"text": "Missing Content-Security-Policy on /api/payment/checkout",
      "header": "Content-Security-Policy", "present": False}),
    (4, "TLS-001", None, None, [], 0.0, False, ["API8:2023"], ["CWE-327"],
     {"text": "Legacy TLS 1.0/1.1 offered", "protocols": ["TLSv1.1"]}),
    (5, "CKI-003", "/admin/login", SensitivityClass.CRITICAL, [], 0.0, False,
     ["API8:2023"], ["CWE-1275"],
     {"text": "Cookie missing SameSite attribute on /admin/login", "cookie": "admin_session"}),
    (6, "HDR-007", "/", SensitivityClass.LOW, [], 0.0, False, ["API8:2023"], ["CWE-497"],
     {"text": "Server version disclosure on /", "header": "Server",
      "value": "nginx/1.18.0 (Ubuntu)"}),
    (7, "HDR-001", "/", SensitivityClass.LOW, [], 0.0, False, ["API8:2023"], ["CWE-319"],
     {"text": "Missing HSTS on /", "header": "Strict-Transport-Security", "present": False}),
]
_CHAIN_MEMBERS = {"INF-003", "HDR-007"}


def _endpoint_id(path: str) -> uuid.UUID:
    return uuid.uuid5(DONE_ID, path)


def _build_findings() -> list[Finding]:
    load_implementations()
    out = []
    for n, check_id, path, cls, signals, bonus, force, owasp, cwe, evidence in _FINDINGS:
        meta = CATALOG[check_id]
        vector = meta.cvss_vector
        base = base_score(vector)
        legacy = compute_score(base, cls, bonus, force_critical=force)
        final, bucket = legacy.cawasma_final_score, legacy.severity
        env = None
        if check_id in CHECKS:    # moved to the spec registry: scored as the pipeline does
            vector = spec_for(check_id).base_cvss_vector
            env = environmental_score(vector, cls or SensitivityClass.LOW, signals)
            base, final, bucket = env.base_score, env.final_score, env.severity_bucket
        out.append(Finding(
            id=_uid(n), check_id=check_id, title=meta.name, category=meta.category,
            endpoint_id=_endpoint_id(path) if path else None,
            endpoint_url=TARGET + path if path else None,
            owasp_map=owasp, cwe_map=cwe, cvss_vector=vector,
            base_score=base, final_score=final,
            final_vector=env.vector if env else None,
            score_reasons=list(env.score_reasons) if env else [],
            severity_bucket=bucket, evidence=evidence,
            sensitivity_class=cls, body_signals=signals,
            chain_ids=[_CHAIN_ID] if check_id in _CHAIN_MEMBERS else [],
            recommendation=meta.recommendation, limitation=meta.limitation,
        ))
    return out


def _counts(findings: list[Finding]) -> SeverityCounts:
    counts = SeverityCounts()
    for f in findings:
        name = f.severity_bucket.value.lower()
        setattr(counts, name, getattr(counts, name) + 1)
    return counts


_DONE_FINDINGS = _build_findings()

DONE_STATUS = ScanStatus(
    scan_id=DONE_ID, url=TARGET, status=ScanState.DONE, progress=100, stage="completed",
    options=ScanOptions(), created_at=_T0, started_at=_T0 + timedelta(seconds=2),
    completed_at=_T0 + timedelta(seconds=74), severity_counts=_counts(_DONE_FINDINGS),
)
RUNNING_STATUS = ScanStatus(
    scan_id=RUNNING_ID, url="https://api.example.org", status=ScanState.RUNNING, progress=45,
    stage="analyzing", options=ScanOptions(crawl_depth=1),
    created_at=_T0 + timedelta(days=1), started_at=_T0 + timedelta(days=1, seconds=3),
)
QUEUED_STATUS = ScanStatus(
    scan_id=QUEUED_ID, url=TARGET, status=ScanState.QUEUED, progress=0, stage=None,
    options=ScanOptions(), created_at=_T0 + timedelta(days=2),
)
FAILED_STATUS = ScanStatus(
    scan_id=FAILED_ID, url="https://legacy.example.net", status=ScanState.FAILED, progress=8,
    stage="crawling", options=ScanOptions(passive_only=True),
    created_at=_T0 - timedelta(days=1), started_at=_T0 - timedelta(days=1) + timedelta(seconds=2),
    completed_at=_T0 - timedelta(days=1) + timedelta(seconds=17),
    error="Target unreachable: connection timed out after 15s.",
)

RESULTS: dict[uuid.UUID, ScanResults] = {
    DONE_ID: ScanResults(scan=DONE_STATUS, findings=_DONE_FINDINGS, chains=[Chain(
        id=_CHAIN_ID, chain_code="C005", name=".env Exposure -> Version Leak -> Full Compromise",
        description="An exposed .env combined with version disclosure can lead to full "
                    "compromise.",
        composite_score=9.8, severity="CRITICAL",
        finding_ids=[f.id for f in _DONE_FINDINGS if f.check_id in _CHAIN_MEMBERS],
    )]),
    RUNNING_ID: ScanResults(scan=RUNNING_STATUS, findings=[]),
    QUEUED_ID: ScanResults(scan=QUEUED_STATUS, findings=[]),
    FAILED_ID: ScanResults(scan=FAILED_STATUS, findings=[]),
}

# Newest first, as GET /api/scans returns them.
SCANS: list[ScanStatus] = sorted((r.scan for r in RESULTS.values()),
                                 key=lambda s: s.created_at, reverse=True)
