"""Report generation (spec sections 25-27): JSON, CSV, HTML, PDF.

All evidence persisted by the scanner is already redacted, so reports are safe
to share. PDF rendering uses WeasyPrint, whose native libraries are installed in
the Docker image; if they are unavailable the API returns a clear 501 rather
than crashing.
"""
from __future__ import annotations

import csv
import io
import json
import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.database.models import AttackChain, Endpoint, Finding, Scan, TlsInfo
from app.database.models.enums import Severity
from app.utils.logging import get_logger

logger = get_logger(__name__)

_SEV_ORDER = [Severity.CRITICAL, Severity.HIGH, Severity.MEDIUM,
              Severity.LOW, Severity.INFO]


class ReportFormatUnavailable(RuntimeError):
    """Raised when a requested format cannot be produced in this environment."""


def _dt(value: datetime | None) -> str | None:
    return value.isoformat() if value else None


async def build_report_data(session, scan_id: uuid.UUID) -> dict | None:
    """Assemble the full report payload for a scan, or None if not found."""
    scan = (await session.execute(
        select(Scan)
        .where(Scan.id == scan_id)
        .options(
            selectinload(Scan.ai_insights),
            selectinload(Scan.tls_info),
        )
    )).scalar_one_or_none()
    if scan is None:
        return None

    findings = list((await session.execute(
        select(Finding)
        .where(Finding.scan_id == scan_id)
        .options(selectinload(Finding.endpoint))
        .order_by(Finding.cawasma_final_score.desc())
    )).scalars())

    endpoints = list((await session.execute(
        select(Endpoint).where(Endpoint.scan_id == scan_id)
        .order_by(Endpoint.context_class)
    )).scalars())

    chains = list((await session.execute(
        select(AttackChain).where(AttackChain.scan_id == scan_id)
        .options(selectinload(AttackChain.findings))
    )).scalars())

    by_sev = {s.value: 0 for s in Severity}
    for f in findings:
        by_sev[f.severity.value] += 1

    return {
        "scan": {
            "id": str(scan.id),
            "target_url": scan.target_url,
            "status": scan.status.value,
            "started_at": _dt(scan.started_at),
            "completed_at": _dt(scan.completed_at),
            "duration_seconds": scan.duration_seconds,
        },
        "summary": {
            "total_findings": len(findings),
            "total_endpoints": len(endpoints),
            "total_chains": len(chains),
            "by_severity": by_sev,
            "max_score": max((f.cawasma_final_score or 0 for f in findings), default=0),
        },
        "insight": scan.ai_insights[0].summary if scan.ai_insights else None,
        "tls": [{
            "host": t.host, "negotiated_protocol": t.negotiated_protocol,
            "negotiated_cipher": t.negotiated_cipher,
            "protocols_offered": t.protocols_offered,
            "cert_issuer": t.cert_issuer, "cert_not_after": _dt(t.cert_not_after),
            "is_self_signed": t.is_self_signed, "hostname_matches": t.hostname_matches,
        } for t in scan.tls_info],
        "endpoints": [{
            "url": e.url, "path": e.path, "method": e.method,
            "status_code": e.status_code,
            "context_class": e.context_class.value if e.context_class else None,
            "context_confidence": e.context_confidence,
            "context_reason": e.context_reason,
            "discovered_by": e.discovered_by.value,
        } for e in endpoints],
        "findings": [{
            "rule_id": f.rule_id, "title": f.title,
            "category": f.category.value, "severity": f.severity.value,
            "cvss_vector": f.cvss_vector, "cvss_base_score": f.cvss_base_score,
            "context_class": f.context_class.value if f.context_class else None,
            "cawasma_context_multiplier": f.cawasma_context_multiplier,
            "response_bonus": f.response_bonus,
            "cawasma_final_score": f.cawasma_final_score,
            "endpoint_url": f.endpoint.url if f.endpoint else None,
            "evidence": f.evidence, "impact": f.impact,
            "recommendation": f.recommendation, "references": f.references,
            "limitation": f.limitation,
        } for f in findings],
        "chains": [{
            "code": c.chain_code, "name": c.name, "description": c.description,
            "composite_score": c.template_composite_score,
            "severity": c.severity.value,
            "member_findings": sorted({m.rule_id for m in c.findings}),
        } for c in chains],
    }


def render_json(data: dict) -> str:
    return json.dumps(data, indent=2, default=str)


def render_csv(data: dict) -> str:
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow([
        "rule_id", "title", "category", "severity", "cvss_base_score",
        "context_class", "context_multiplier", "response_bonus",
        "cawasma_final_score", "endpoint_url", "limitation",
    ])
    for f in data["findings"]:
        writer.writerow([
            f["rule_id"], f["title"], f["category"], f["severity"],
            f["cvss_base_score"], f["context_class"],
            f["cawasma_context_multiplier"], f["response_bonus"],
            f["cawasma_final_score"], f["endpoint_url"] or "",
            (f["limitation"] or "").replace("\n", " "),
        ])
    return buf.getvalue()


_HTML_TEMPLATE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<title>CAWASMA Report — {{ scan.target_url }}</title>
<style>
 body{font-family:Arial,Helvetica,sans-serif;margin:2rem;color:#1a1a1a}
 h1{font-size:1.5rem} h2{margin-top:1.6rem;border-bottom:2px solid #eee;padding-bottom:.3rem}
 table{border-collapse:collapse;width:100%;margin:.6rem 0;font-size:.85rem}
 th,td{border:1px solid #ddd;padding:.4rem .5rem;text-align:left;vertical-align:top}
 th{background:#f4f4f4}
 .CRITICAL{color:#fff;background:#9b1c1c;padding:1px 6px;border-radius:3px}
 .HIGH{color:#fff;background:#b45309;padding:1px 6px;border-radius:3px}
 .MEDIUM{color:#1a1a1a;background:#fde68a;padding:1px 6px;border-radius:3px}
 .LOW{color:#1a1a1a;background:#d1fae5;padding:1px 6px;border-radius:3px}
 .INFO{color:#1a1a1a;background:#e5e7eb;padding:1px 6px;border-radius:3px}
 .muted{color:#666;font-size:.8rem} .limit{color:#92400e;font-style:italic}
 pre{white-space:pre-wrap;background:#fafafa;padding:.6rem;border:1px solid #eee}
</style></head><body>
<h1>CAWASMA Security Report</h1>
<p class="muted">Target: <strong>{{ scan.target_url }}</strong> &middot;
 Status: {{ scan.status }} &middot; Completed: {{ scan.completed_at or "—" }}</p>

<h2>Executive summary</h2>
<pre>{{ insight or "No summary available." }}</pre>
<p>
{% for s,n in summary.by_severity.items() %}<span class="{{ s }}">{{ s }}: {{ n }}</span>&nbsp;{% endfor %}
</p>
<p class="muted">{{ summary.total_findings }} findings &middot;
 {{ summary.total_endpoints }} endpoints &middot;
 {{ summary.total_chains }} attack chains &middot; highest score {{ summary.max_score }}</p>

{% if chains %}
<h2>Attack chains (context-aware correlation)</h2>
<table><tr><th>Code</th><th>Chain</th><th>Composite</th><th>Severity</th><th>Members</th></tr>
{% for c in chains %}<tr><td>{{ c.code }}</td><td>{{ c.name }}<br><span class="muted">{{ c.description }}</span></td>
<td>{{ c.composite_score }}</td><td><span class="{{ c.severity }}">{{ c.severity }}</span></td>
<td>{{ c.member_findings|join(", ") }}</td></tr>{% endfor %}
</table>
{% endif %}

<h2>Findings (ranked by context-aware score)</h2>
<table><tr><th>Severity</th><th>Score</th><th>Rule</th><th>Endpoint</th>
<th>CVSS base</th><th>Context</th></tr>
{% for f in findings %}<tr>
<td><span class="{{ f.severity }}">{{ f.severity }}</span></td>
<td><strong>{{ f.cawasma_final_score }}</strong></td>
<td>{{ f.rule_id }} — {{ f.title }}
 {% if f.limitation %}<br><span class="limit">Limitation: {{ f.limitation }}</span>{% endif %}</td>
<td class="muted">{{ f.endpoint_url or "—" }}</td>
<td>{{ f.cvss_base_score }}</td>
<td>{{ f.context_class or "—" }} ×{{ f.cawasma_context_multiplier }}
 {% if f.response_bonus %}+{{ f.response_bonus }}{% endif %}</td>
</tr>{% endfor %}
</table>

<h2>Endpoints</h2>
<table><tr><th>Path</th><th>Status</th><th>Context</th><th>Confidence</th><th>Discovered</th></tr>
{% for e in endpoints %}<tr><td>{{ e.path }}</td><td>{{ e.status_code or "—" }}</td>
<td>{{ e.context_class or "—" }}</td><td>{{ "%.2f"|format(e.context_confidence or 0) }}</td>
<td>{{ e.discovered_by }}</td></tr>{% endfor %}
</table>

{% if tls %}
<h2>TLS</h2>
<table><tr><th>Host</th><th>Protocol</th><th>Cipher</th><th>Issuer</th><th>Expires</th><th>Self-signed</th></tr>
{% for t in tls %}<tr><td>{{ t.host }}</td><td>{{ t.negotiated_protocol }}</td>
<td>{{ t.negotiated_cipher }}</td><td>{{ t.cert_issuer }}</td>
<td>{{ t.cert_not_after }}</td><td>{{ t.is_self_signed }}</td></tr>{% endfor %}
</table>
{% endif %}

<hr><p class="muted">CAWASMA — Context-Aware Web &amp; API Security Misconfiguration
Analyzer. The context-aware final score is a custom prioritization metric and is
not an official CVSS value. Findings marked with a limitation require manual
verification.</p>
</body></html>"""


def render_html(data: dict) -> str:
    from jinja2 import Template

    return Template(_HTML_TEMPLATE).render(**data)


def render_pdf(data: dict) -> bytes:
    html = render_html(data)
    try:
        from weasyprint import HTML
    except Exception as exc:  # noqa: BLE001 - native libs may be absent
        raise ReportFormatUnavailable(
            "PDF rendering requires WeasyPrint native libraries (available in the "
            "Docker image)."
        ) from exc
    return HTML(string=html).write_pdf()
