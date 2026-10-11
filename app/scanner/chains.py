"""Attack-chain correlation -- Contribution 2 (spec section 6).

Five predefined chain templates (C001-C005). A chain is reported ONLY when the
rule_ids it requires are actually present among the scan's findings -- never
speculatively. The ``composite_score`` is a documented *template* severity for a
known pattern (stored as ``template_composite_score``), not a computed CVSS.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from app.database.models.enums import Severity


@dataclass(frozen=True)
class ChainTemplate:
    code: str
    name: str
    description: str
    # A chain fires when at least this many of ``requires`` are present, and
    # every rule_id in ``mandatory`` is present.
    requires: tuple[str, ...]
    mandatory: tuple[str, ...]
    composite_score: float
    severity: Severity


CHAIN_TEMPLATES: tuple[ChainTemplate, ...] = (
    ChainTemplate(
        "C001", "XSS -> Cookie Theft -> Account Takeover",
        "Missing XSS/framing protections plus a JS-readable session cookie "
        "create an XSS-to-account-takeover path.",
        requires=("HDR-002", "HDR-003", "CKI-001"),
        mandatory=("CKI-001",),
        composite_score=9.4, severity=Severity.CRITICAL,
    ),
    ChainTemplate(
        "C002", "Information Disclosure -> Targeted Exploit",
        "Version/stack disclosure combined with a directory/info leak enables "
        "targeted exploitation.",
        requires=("HDR-007", "HDR-008", "INF-002", "API-004"),
        mandatory=(),
        composite_score=8.2, severity=Severity.HIGH,
    ),
    ChainTemplate(
        "C003", "CORS -> CSRF -> Privilege Escalation",
        "Reflective/credentialed CORS plus missing SameSite enables "
        "cross-site request forgery toward privileged actions.",
        requires=("COR-002", "COR-003", "CKI-003"),
        mandatory=("CKI-003",),
        composite_score=9.6, severity=Severity.CRITICAL,
    ),
    ChainTemplate(
        "C004", "Unauthenticated Data Exposure -> BOLA -> Full Data Breach",
        "Unauthenticated data access plus object-id enumeration indicates a "
        "broad data-breach path.",
        requires=("API-003", "API-006"),
        mandatory=("API-003", "API-006"),
        composite_score=9.1, severity=Severity.CRITICAL,
    ),
    ChainTemplate(
        "C005", ".env Exposure -> Version Leak -> Full Compromise",
        "An exposed .env combined with version disclosure can lead to full "
        "compromise.",
        requires=("INF-003", "HDR-007", "INF-004"),
        mandatory=("INF-003",),
        composite_score=9.8, severity=Severity.CRITICAL,
    ),
)


@dataclass
class DetectedChain:
    code: str
    name: str
    description: str
    composite_score: float
    severity: Severity
    matched_rule_ids: list[str] = field(default_factory=list)


def correlate_chains(present_rule_ids: set[str]) -> list[DetectedChain]:
    """Return chains whose conditions are satisfied by the present findings."""
    detected: list[DetectedChain] = []
    for tpl in CHAIN_TEMPLATES:
        if any(m not in present_rule_ids for m in tpl.mandatory):
            continue
        matched = [rid for rid in tpl.requires if rid in present_rule_ids]
        # Fire when all mandatory present AND at least 2 of the required (or all,
        # for short templates) are present.
        threshold = min(2, len(tpl.requires)) if not tpl.mandatory else max(
            len(tpl.mandatory), min(2, len(tpl.requires))
        )
        if len(matched) >= threshold:
            detected.append(
                DetectedChain(
                    code=tpl.code,
                    name=tpl.name,
                    description=tpl.description,
                    composite_score=tpl.composite_score,
                    severity=tpl.severity,
                    matched_rule_ids=matched,
                )
            )
    return detected
