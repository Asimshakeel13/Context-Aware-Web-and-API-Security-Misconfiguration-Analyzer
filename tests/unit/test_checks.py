"""Tests for the 58-check catalog/registry and representative detections."""
from __future__ import annotations

from app.database.models.enums import ContextClass
from app.scanner.body_classifier import classify_body
from app.scanner.engine import HttpResult
from app.scanner.rules import REGISTRY, CheckContext, run_checks
from app.scanner.rules.catalog import CATALOG


def _ctx(headers=None, body="", status=200, path="/", url=None, ctype="text/html",
         **kw) -> CheckContext:
    res = HttpResult(
        requested_url=url or f"https://t.example{path}",
        final_url=url or f"https://t.example{path}",
        method="GET",
        status_code=status,
        headers=headers or {},
        body=body,
        content_type=ctype,
    )
    return CheckContext(url=url or f"https://t.example{path}", path=path, result=res, **kw)


def test_catalog_has_58_rules_with_complete_metadata():
    assert len(CATALOG) == 58
    ids = list(CATALOG.keys())
    assert len(ids) == len(set(ids))  # unique rule_ids
    for meta in CATALOG.values():
        assert meta.cvss_vector.startswith("CVSS:3.1/")
        assert 0.0 < meta.base_score <= 10.0
        assert meta.impact and meta.recommendation


def test_registry_has_58_detection_functions():
    assert len(REGISTRY) == 58


def test_missing_headers_fire():
    ctx = _ctx(headers={}, body="<html></html>")
    ids = {f.rule_id for f in run_checks(ctx)}
    # No security headers at all -> the header checks should fire.
    assert {"HDR-001", "HDR-002", "HDR-003", "HDR-004"} <= ids


def test_full_headers_suppress_findings():
    ctx = _ctx(headers={
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains; preload",
        "Content-Security-Policy": "default-src 'self'; frame-ancestors 'none'",
        "X-Frame-Options": "DENY",
        "X-Content-Type-Options": "nosniff",
        "Referrer-Policy": "no-referrer",
        "Permissions-Policy": "geolocation=()",
        "Cross-Origin-Opener-Policy": "same-origin",
        "Cross-Origin-Resource-Policy": "same-origin",
    })
    ids = {f.rule_id for f in run_checks(ctx)}
    for rid in ("HDR-001", "HDR-002", "HDR-003", "HDR-004", "HDR-005", "HDR-006"):
        assert rid not in ids


def test_insecure_cookie_flags():
    ctx = _ctx(body="")
    ctx.result.set_cookie_headers = ["sessionid=abc; Path=/"]
    ids = {f.rule_id for f in run_checks(ctx)}
    assert {"CKI-001", "CKI-002", "CKI-003"} <= ids  # no HttpOnly/Secure/SameSite


def test_cors_reflection_and_credentials():
    ctx = _ctx()
    ctx.cors_acao = ctx.probe_origin
    ctx.cors_acac = "true"
    ids = {f.rule_id for f in run_checks(ctx)}
    assert "COR-002" in ids  # reflection
    assert "COR-003" in ids  # credentials + weak origin


def test_env_exposure_and_secrets():
    body = "SECRET_KEY=abc123\nDB_PASSWORD=hunter2000"
    ctx = _ctx(body=body, path="/.env", ctype="text/plain")
    ctx.body_class = classify_body(body)
    ids = {f.rule_id for f in run_checks(ctx)}
    assert "INF-003" in ids   # .env exposed
    assert "API-013" in ids   # secrets in response


def test_verbose_error_detected():
    ctx = _ctx(body="Traceback (most recent call last): ...", ctype="text/html")
    ids = {f.rule_id for f in run_checks(ctx)}
    assert "API-004" in ids


def test_limitation_marked_on_blackbox_checks():
    # BOLA fires on a numeric id in an /api path and must carry a limitation.
    ctx = _ctx(path="/api/users/123", ctype="application/json", body='{"id":123}')
    bola = [f for f in run_checks(ctx) if f.rule_id == "API-006"]
    assert bola and bola[0].limitation
