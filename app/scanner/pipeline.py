"""Scan pipeline -- orchestrates the whole analysis (spec section 19).

Flow per scan:

    crawl -> (host: TLS probe + HTTP->HTTPS check)
          -> for each endpoint: fetch, classify path, classify body, probe
             (OPTIONS / CORS / benign injection), run 58 checks, score
          -> correlate attack chains -> stats

This module is database-free: it returns dataclasses. Persistence lives in
``app/services/result_service.py`` and the Celery task. Progress is reported
through an async ``on_progress`` callback so the worker can publish it to Redis.
"""
from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from urllib.parse import urlparse

from app.config import settings
from app.database.models.enums import (
    ContextClass, DiscoveryMethod, SameSite, Severity,
)
from app.scanner.body_classifier import BodyClassification, classify_body
from app.scanner.chains import DetectedChain, correlate_chains
from app.scanner.crawler import Crawler
from app.scanner.cvss import compute_score
from app.scanner.engine import HttpEngine, HttpResult
from app.scanner.rules import CheckContext, RawFinding, run_checks
from app.scanner.sensitivity import get_classifier, raw_tokens
from app.services.llm import get_llm_client
from app.scanner.tls import TlsProbe, probe_tls
from app.utils.logging import get_logger
from app.utils.redaction import redact_headers

logger = get_logger(__name__)

ProgressFn = Callable[[str, int, str], Awaitable[None]]

# Rules whose score should receive the endpoint's response-body bonus.
_BONUS_RULES = {"API-013", "API-003", "INF-001", "INF-003", "INF-005"}
# Rules that represent credential exposure -> force CRITICAL when creds present.
_FORCE_CRIT_RULES = {"API-013", "INF-003"}


@dataclass
class CookieMeta:
    name: str
    value_length: int
    http_only: bool
    secure: bool
    same_site: SameSite
    domain: str | None
    path: str | None


@dataclass
class ScoredFinding:
    raw: RawFinding
    cvss_base_score: float
    context_multiplier: float
    response_bonus: float
    cawasma_final_score: float
    severity: Severity
    context_class: ContextClass | None
    context_confidence: float | None
    endpoint_index: int | None


@dataclass
class EndpointAnalysis:
    url: str
    path: str
    method: str
    status_code: int | None
    content_type: str | None
    response_time: float | None
    discovered_by: DiscoveryMethod
    context_class: ContextClass
    context_confidence: float
    context_reason: list[str]
    headers: dict[str, str]
    cookies: list[CookieMeta] = field(default_factory=list)
    body_class: BodyClassification | None = None


@dataclass
class ScanResult:
    target: str
    host: str
    endpoints: list[EndpointAnalysis]
    findings: list[ScoredFinding]
    chains: list[DetectedChain]
    tls: TlsProbe | None
    stats: dict


async def _noop(stage: str, percent: int, message: str) -> None:  # default progress
    return None


def _parse_cookies(set_cookie_headers: list[str]) -> list[CookieMeta]:
    metas: list[CookieMeta] = []
    for raw in set_cookie_headers:
        parts = [p.strip() for p in raw.split(";")]
        first = parts[0]
        name, _, value = first.partition("=")
        attrs = {}
        for p in parts[1:]:
            k, _, v = p.partition("=")
            attrs[k.lower()] = v or True
        ss_raw = str(attrs.get("samesite", "")).lower()
        same_site = {
            "strict": SameSite.STRICT, "lax": SameSite.LAX, "none": SameSite.NONE,
        }.get(ss_raw, SameSite.UNSET)
        metas.append(CookieMeta(
            name=name.strip(),
            value_length=len(value),
            http_only="httponly" in attrs,
            secure="secure" in attrs,
            same_site=same_site,
            domain=attrs.get("domain") if isinstance(attrs.get("domain"), str) else None,
            path=attrs.get("path") if isinstance(attrs.get("path"), str) else None,
        ))
    return metas


async def _probe_endpoint(engine: HttpEngine, ep_url: str, result: HttpResult,
                          is_api: bool) -> dict:
    """Run bounded auxiliary probes; return signals for the check context."""
    signals: dict = {
        "allowed_methods": set(),
        "cors_acao": None, "cors_acac": None, "cors_methods": None,
        "injection_error_reflected": False,
        "graphql_introspection": "__schema" in (result.body or ""),
    }
    # OPTIONS -> Allow header.
    try:
        opt = await engine.fetch(ep_url, method="OPTIONS")
        allow = opt.headers.get("allow") or opt.headers.get("Allow")
        if allow:
            signals["allowed_methods"] = {m.strip().upper() for m in allow.split(",")}
        signals["cors_methods"] = opt.headers.get("access-control-allow-methods")
    except Exception as exc:  # noqa: BLE001
        logger.debug("OPTIONS probe failed: %s", exc)

    # CORS probe with a test Origin header.
    probe_origin = "https://cawasma-probe.example"
    try:
        cors = await engine.fetch(ep_url, extra_headers={"Origin": probe_origin})
        signals["cors_acao"] = cors.headers.get("access-control-allow-origin")
        signals["cors_acac"] = cors.headers.get("access-control-allow-credentials")
        if not signals["cors_methods"]:
            signals["cors_methods"] = cors.headers.get("access-control-allow-methods")
    except Exception as exc:  # noqa: BLE001
        logger.debug("CORS probe failed: %s", exc)

    # Benign injection probe (detection-only) for API-ish endpoints.
    if is_api:
        sep = "&" if urlparse(ep_url).query else "?"
        probe_url = f"{ep_url}{sep}cawasma_probe=%27%22%3C"
        try:
            inj = await engine.fetch(probe_url)
            if inj.status_code and inj.status_code >= 500:
                signals["injection_error_reflected"] = True
            elif "cawasma_probe" in (inj.body or "") and any(
                tok in (inj.body or "") for tok in ("SQL", "syntax", "Exception", "Traceback")
            ):
                signals["injection_error_reflected"] = True
        except Exception as exc:  # noqa: BLE001
            logger.debug("injection probe failed: %s", exc)
    return signals


async def _check_http_redirect(engine: HttpEngine, host: str) -> bool | None:
    """Return True if http:// redirects to https://, False if not, None if N/A."""
    try:
        res = await engine.fetch(f"http://{host}/")
        if res.error:
            return None
        if res.final_url.startswith("https://"):
            return True
        if any(u.startswith("https://") for u in res.redirect_chain):
            return True
        return False
    except Exception:  # noqa: BLE001
        return None


async def run_pipeline(target: str, on_progress: ProgressFn | None = None,
                       *, probe: bool = True, allow_private: bool = False) -> ScanResult:
    """Execute the full scan and return a structured result.

    ``allow_private`` relaxes SSRF loopback/private-IP blocking and is intended
    for tests against a local mock server only.
    """
    report = on_progress or _noop
    host = urlparse(target).hostname or ""
    classifier = get_classifier()
    llm = get_llm_client()  # None unless LLM_ENABLED + API key configured

    await report("initializing", 2, "Preparing scan")

    async with HttpEngine(allow_private=allow_private) as engine:
        # --- Discovery ---------------------------------------------------
        await report("crawling", 8, "Discovering endpoints")
        crawler = Crawler(engine)
        discovered = await crawler.crawl(target)
        if not discovered:
            discovered = []
        total = max(len(discovered), 1)

        # --- Host-level checks ------------------------------------------
        await report("tls", 12, "Probing TLS configuration")
        tls = await asyncio.to_thread(probe_tls, host) if probe else None
        http_redirects = await _check_http_redirect(engine, host) if probe else None

        # --- Per-endpoint analysis --------------------------------------
        endpoints: list[EndpointAnalysis] = []
        findings: list[ScoredFinding] = []

        for i, de in enumerate(discovered):
            pct = 15 + int((i / total) * 70)
            await report("analyzing", pct, f"Analyzing {de.path}")

            result = await engine.fetch(de.url, method="GET")
            expansions = None
            if llm is not None:
                expansions = await llm.expand_abbreviations(raw_tokens(de.path))
            cls = classifier.classify(de.path, extra_expansions=expansions)
            body_class = classify_body(result.body, result.content_type)
            is_api = "/api" in de.path or "json" in (result.content_type or "").lower()

            signals = (await _probe_endpoint(engine, de.url, result, is_api)
                       if probe else {})

            ctx = CheckContext(
                url=de.url, path=de.path, result=result,
                context_class=cls.context_class, body_class=body_class,
                allowed_methods=signals.get("allowed_methods", set()),
                cors_acao=signals.get("cors_acao"),
                cors_acac=signals.get("cors_acac"),
                cors_methods=signals.get("cors_methods"),
                tls=tls,
                http_scheme_redirects_https=http_redirects,
                graphql_introspection=signals.get("graphql_introspection", False),
                injection_error_reflected=signals.get("injection_error_reflected", False),
            )

            ep = EndpointAnalysis(
                url=de.url, path=de.path, method=de.method,
                status_code=result.status_code, content_type=result.content_type,
                response_time=result.response_time, discovered_by=de.discovered_by,
                context_class=cls.context_class, context_confidence=cls.confidence,
                context_reason=cls.reason,
                headers=redact_headers(result.headers),
                cookies=_parse_cookies(result.set_cookie_headers),
                body_class=body_class,
            )
            ep_index = len(endpoints)
            endpoints.append(ep)

            for raw in run_checks(ctx):
                bonus = body_class.bonus if raw.rule_id in _BONUS_RULES else 0.0
                force = (raw.rule_id in _FORCE_CRIT_RULES) and body_class.credentials
                score = compute_score(
                    raw.base_score, cls.context_class, bonus, force_critical=force,
                )
                findings.append(ScoredFinding(
                    raw=raw,
                    cvss_base_score=score.cvss_base_score,
                    context_multiplier=score.context_multiplier,
                    response_bonus=score.response_bonus,
                    cawasma_final_score=score.cawasma_final_score,
                    severity=score.severity,
                    context_class=cls.context_class,
                    context_confidence=cls.confidence,
                    endpoint_index=ep_index,
                ))

        # --- Attack-chain correlation -----------------------------------
        await report("correlating", 92, "Correlating attack chains")
        present = {f.raw.rule_id for f in findings}
        chains = correlate_chains(present)

        stats = _build_stats(endpoints, findings, chains)
        await report("completed", 100, "Scan complete")

    return ScanResult(
        target=target, host=host, endpoints=endpoints,
        findings=findings, chains=chains, tls=tls, stats=stats,
    )


def _build_stats(endpoints, findings, chains) -> dict:
    by_sev = {s.value: 0 for s in Severity}
    for f in findings:
        by_sev[f.severity.value] += 1
    return {
        "endpoints": len(endpoints),
        "findings": len(findings),
        "chains": len(chains),
        "by_severity": by_sev,
        "max_score": max((f.cawasma_final_score for f in findings), default=0.0),
    }
