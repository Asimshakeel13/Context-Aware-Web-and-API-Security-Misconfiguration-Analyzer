"""Persist a pipeline :class:`ScanResult` into the database (spec section 19).

Kept separate from the pipeline so the scanner stays database-free and unit-
testable. All writes happen inside the caller's transaction/session.
"""
from __future__ import annotations

from app.database.models import (
    AiInsight, AttackChain, Cookie, Endpoint, Finding, Header, Scan, TlsInfo,
)
from app.scanner.pipeline import ScanResult
from app.services.insights import generate_insight
from app.utils.logging import get_logger

logger = get_logger(__name__)

# Only persist headers that carry security signal (keeps rows bounded).
_SECURITY_HEADERS = {
    "strict-transport-security", "content-security-policy", "x-frame-options",
    "x-content-type-options", "referrer-policy", "permissions-policy",
    "cross-origin-opener-policy", "cross-origin-resource-policy",
    "cache-control", "server", "x-powered-by", "set-cookie",
    "access-control-allow-origin", "access-control-allow-credentials",
    "www-authenticate",
}


async def persist_result(session, scan: Scan, result: ScanResult) -> None:
    """Write endpoints, findings, TLS, chains and an insight for ``scan``."""
    endpoint_rows: list[Endpoint] = []

    for ep in result.endpoints:
        row = Endpoint(
            scan_id=scan.id,
            url=ep.url,
            path=ep.path,
            method=ep.method,
            status_code=ep.status_code,
            content_type=ep.content_type,
            context_class=ep.context_class,
            context_confidence=ep.context_confidence,
            context_reason=ep.context_reason,
            response_time=ep.response_time,
            discovered_by=ep.discovered_by,
        )
        session.add(row)
        endpoint_rows.append(row)

        for name, value in ep.headers.items():
            if name.lower() in _SECURITY_HEADERS:
                session.add(Header(endpoint=row, name=name, value=value))
        for ck in ep.cookies:
            session.add(Cookie(
                endpoint=row, name=ck.name, value_length=ck.value_length,
                http_only=ck.http_only, secure=ck.secure, same_site=ck.same_site,
                domain=ck.domain, path=ck.path,
            ))

    # Findings -- keep a rule_id -> [Finding] map for chain linking.
    finding_rows: list[Finding] = []
    by_rule: dict[str, list[Finding]] = {}
    for sf in result.findings:
        raw = sf.raw
        ep_row = (endpoint_rows[sf.endpoint_index]
                  if sf.endpoint_index is not None and sf.endpoint_index < len(endpoint_rows)
                  else None)
        row = Finding(
            scan_id=scan.id,
            endpoint=ep_row,
            rule_id=raw.rule_id,
            title=raw.title,
            category=raw.category,
            description=raw.evidence,
            context_class=sf.context_class,
            context_confidence=sf.context_confidence,
            cvss_vector=raw.cvss_vector,
            cvss_base_score=sf.cvss_base_score,
            cawasma_context_multiplier=sf.context_multiplier,
            response_bonus=sf.response_bonus,
            cawasma_final_score=sf.cawasma_final_score,
            severity=sf.severity,
            evidence=raw.evidence,
            impact=raw.impact,
            recommendation=raw.recommendation,
            references=raw.references,
            limitation=raw.limitation,
        )
        session.add(row)
        finding_rows.append(row)
        by_rule.setdefault(raw.rule_id, []).append(row)

    # TLS info (host-level).
    if result.tls and result.tls.reachable:
        t = result.tls
        session.add(TlsInfo(
            scan_id=scan.id, host=t.host,
            protocols_offered=t.protocols_offered,
            negotiated_protocol=t.negotiated_protocol,
            negotiated_cipher=t.negotiated_cipher,
            cert_subject=t.cert_subject, cert_issuer=t.cert_issuer,
            cert_not_after=t.cert_not_after, is_self_signed=t.is_self_signed,
            hostname_matches=t.hostname_matches,
        ))

    # Attack chains + link member findings.
    for ch in result.chains:
        chain_row = AttackChain(
            scan_id=scan.id, chain_code=ch.code, name=ch.name,
            description=ch.description,
            template_composite_score=ch.composite_score, severity=ch.severity,
        )
        for rid in ch.matched_rule_ids:
            for fr in by_rule.get(rid, []):
                chain_row.findings.append(fr)
        session.add(chain_row)

    # Deterministic executive insight (built-in, not an external LLM).
    session.add(AiInsight(
        scan_id=scan.id, provider="builtin",
        summary=generate_insight(result),
    ))

    logger.info("persisted scan %s: %d endpoints, %d findings, %d chains",
                scan.id, len(endpoint_rows), len(finding_rows), len(result.chains))
