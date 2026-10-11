"""Check framework: the context passed to every rule and the raw finding type.

Rules are pure functions ``detect(ctx) -> RawFinding | None``. They read only
from the :class:`CheckContext` and never touch the database, so each is trivial
to unit-test. The registry is populated by importing the category modules.
"""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field

from app.database.models.enums import ContextClass, FindingCategory, Severity
from app.scanner.body_classifier import BodyClassification
from app.scanner.catalog_ref import CATALOG  # re-export for rule modules
from app.scanner.cvss import severity_for
from app.scanner.engine import HttpResult
from app.scanner.tls import TlsProbe


@dataclass
class CheckContext:
    """Everything a rule may need about one endpoint (+ scan-level signals)."""

    url: str
    path: str
    result: HttpResult
    context_class: ContextClass | None = None
    body_class: BodyClassification | None = None

    # Optional probe-derived signals (populated by the pipeline in Phase 13).
    allowed_methods: set[str] = field(default_factory=set)
    cors_acao: str | None = None            # Access-Control-Allow-Origin (probe)
    cors_acac: str | None = None            # Access-Control-Allow-Credentials
    cors_methods: str | None = None         # Access-Control-Allow-Methods
    probe_origin: str = "https://cawasma-probe.example"
    tls: TlsProbe | None = None
    http_scheme_redirects_https: bool | None = None
    graphql_introspection: bool = False
    injection_error_reflected: bool = False

    def header(self, name: str) -> str | None:
        low = name.lower()
        for k, v in self.result.headers.items():
            if k.lower() == low:
                return v
        return None

    def has_header(self, name: str) -> bool:
        return self.header(name) is not None


@dataclass
class RawFinding:
    rule_id: str
    title: str
    category: FindingCategory
    base_severity: Severity
    cvss_vector: str
    base_score: float
    evidence: str | None = None
    impact: str = ""
    recommendation: str = ""
    references: list[str] = field(default_factory=list)
    limitation: str | None = None


DetectFn = Callable[[CheckContext], "RawFinding | None"]
REGISTRY: list[DetectFn] = []


def rule(fn: DetectFn) -> DetectFn:
    """Register a detection function."""
    REGISTRY.append(fn)
    return fn


def make(rule_id: str, evidence: str | None = None) -> RawFinding:
    """Build a RawFinding from catalog metadata + runtime evidence."""
    meta = CATALOG[rule_id]
    return RawFinding(
        rule_id=meta.rule_id,
        title=meta.name,
        category=meta.category,
        base_severity=severity_for(meta.base_score),
        cvss_vector=meta.cvss_vector,
        base_score=meta.base_score,
        evidence=evidence,
        impact=meta.impact,
        recommendation=meta.recommendation,
        references=list(meta.references),
        limitation=meta.limitation,
    )
