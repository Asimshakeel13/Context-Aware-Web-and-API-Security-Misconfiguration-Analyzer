"""Rule registry aggregation.

Importing this package imports every category module, which registers all 58
detection functions on ``REGISTRY``. ``run_checks`` executes them against a
context and returns the findings that fired.
"""
from __future__ import annotations

from app.scanner.rules.base import CheckContext, RawFinding, REGISTRY
from app.scanner.rules import (  # noqa: F401  (import side-effect: registration)
    auth,
    cookies,
    cors,
    headers,
    info_disclosure,
    rest_api,
    tls_rules,
)
from app.utils.logging import get_logger

logger = get_logger(__name__)


def run_checks(ctx: CheckContext) -> list[RawFinding]:
    """Run every registered check against a context; return fired findings."""
    findings: list[RawFinding] = []
    for detect in REGISTRY:
        try:
            f = detect(ctx)
            if f is not None:
                findings.append(f)
        except Exception as exc:  # noqa: BLE001 - one bad rule must not stop the scan
            logger.warning("rule %s raised: %s", getattr(detect, "__name__", "?"), exc)
    return findings


__all__ = ["CheckContext", "RawFinding", "REGISTRY", "run_checks"]
