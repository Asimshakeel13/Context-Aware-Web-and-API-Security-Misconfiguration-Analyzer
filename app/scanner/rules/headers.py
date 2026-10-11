"""Header checks HDR-001..HDR-012 (spec section 13)."""
from __future__ import annotations

import re

from app.database.models.enums import ContextClass
from app.scanner.rules.base import CheckContext, RawFinding, make, rule


def _missing(ctx: CheckContext, header: str) -> bool:
    return not ctx.has_header(header)


@rule
def hdr_001_hsts(ctx: CheckContext) -> RawFinding | None:
    if _missing(ctx, "Strict-Transport-Security"):
        return make("HDR-001", "Response has no Strict-Transport-Security header.")
    return None


@rule
def hdr_002_csp(ctx: CheckContext) -> RawFinding | None:
    if _missing(ctx, "Content-Security-Policy"):
        return make("HDR-002", "Response has no Content-Security-Policy header.")
    return None


@rule
def hdr_003_xfo(ctx: CheckContext) -> RawFinding | None:
    # CSP frame-ancestors can substitute for X-Frame-Options.
    csp = (ctx.header("Content-Security-Policy") or "").lower()
    if _missing(ctx, "X-Frame-Options") and "frame-ancestors" not in csp:
        return make("HDR-003", "No X-Frame-Options and no CSP frame-ancestors.")
    return None


@rule
def hdr_004_xcto(ctx: CheckContext) -> RawFinding | None:
    if _missing(ctx, "X-Content-Type-Options"):
        return make("HDR-004", "Response has no X-Content-Type-Options: nosniff.")
    return None


@rule
def hdr_005_referrer(ctx: CheckContext) -> RawFinding | None:
    if _missing(ctx, "Referrer-Policy"):
        return make("HDR-005", "Response has no Referrer-Policy header.")
    return None


@rule
def hdr_006_permissions(ctx: CheckContext) -> RawFinding | None:
    if _missing(ctx, "Permissions-Policy"):
        return make("HDR-006", "Response has no Permissions-Policy header.")
    return None


@rule
def hdr_007_server(ctx: CheckContext) -> RawFinding | None:
    server = ctx.header("Server")
    if server and re.search(r"\d", server):  # contains a version number
        return make("HDR-007", f"Server header discloses version: {server}")
    return None


@rule
def hdr_008_powered_by(ctx: CheckContext) -> RawFinding | None:
    xp = ctx.header("X-Powered-By")
    if xp:
        return make("HDR-008", f"X-Powered-By discloses stack: {xp}")
    return None


@rule
def hdr_009_coop(ctx: CheckContext) -> RawFinding | None:
    if _missing(ctx, "Cross-Origin-Opener-Policy"):
        return make("HDR-009", "Response has no Cross-Origin-Opener-Policy header.")
    return None


@rule
def hdr_010_corp(ctx: CheckContext) -> RawFinding | None:
    if _missing(ctx, "Cross-Origin-Resource-Policy"):
        return make("HDR-010", "Response has no Cross-Origin-Resource-Policy header.")
    return None


@rule
def hdr_011_cache(ctx: CheckContext) -> RawFinding | None:
    # Only relevant for sensitive endpoints.
    if ctx.context_class in (ContextClass.HIGH, ContextClass.CRITICAL):
        cc = (ctx.header("Cache-Control") or "").lower()
        if "no-store" not in cc:
            return make("HDR-011", f"Sensitive endpoint Cache-Control: '{cc or 'absent'}'.")
    return None


@rule
def hdr_012_expect_ct(ctx: CheckContext) -> RawFinding | None:
    # Legacy/informational: only when HSTS present but no CT signalling.
    if ctx.has_header("Strict-Transport-Security") and _missing(ctx, "Expect-CT"):
        return make("HDR-012", "No Expect-CT header (legacy CT signalling absent).")
    return None
