"""CVSS + CAWASMA context-aware scoring (spec sections 8-12).

Two numbers are produced and kept distinct:

* the official CVSS v3.1 **base score** (predefined per rule, never invented), and
* the CAWASMA **context-aware final score**, computed as:

      final = min(10.0, (base * context_multiplier) + response_bonus)

The final score is a custom prioritization metric -- it is explicitly NOT
presented as an official CVSS value.
"""
from __future__ import annotations

from dataclasses import dataclass

from app.database.models.enums import ContextClass, Severity

# Endpoint context multipliers (spec section 9).
CONTEXT_MULTIPLIERS: dict[ContextClass, float] = {
    ContextClass.CRITICAL: 2.0,
    ContextClass.HIGH: 1.5,
    ContextClass.MEDIUM: 1.0,
    ContextClass.LOW: 0.6,
}

# Response-body bonuses (spec section 9).
RESPONSE_BONUS = {
    "credentials": 3.5,
    "pii": 2.0,
    "financial": 1.5,
    "internal_ip": 2.0,
}

MAX_SCORE = 10.0


def severity_for(score: float) -> Severity:
    """Map a 0-10 score to a severity bucket (spec section 10)."""
    if score >= 9.0:
        return Severity.CRITICAL
    if score >= 7.0:
        return Severity.HIGH
    if score >= 4.0:
        return Severity.MEDIUM
    if score >= 0.1:
        return Severity.LOW
    return Severity.INFO


@dataclass
class ScoreResult:
    cvss_base_score: float
    context_multiplier: float
    response_bonus: float
    cawasma_final_score: float
    severity: Severity


def compute_score(
    base_cvss: float,
    context_class: ContextClass | None,
    response_bonus: float = 0.0,
    *,
    force_critical: bool = False,
) -> ScoreResult:
    """Apply the CAWASMA formula and derive severity.

    ``force_critical`` reflects the rule that credential exposure forces the
    final severity to CRITICAL (spec section 7), regardless of the numeric score.
    """
    multiplier = CONTEXT_MULTIPLIERS.get(context_class or ContextClass.MEDIUM, 1.0)
    raw = (base_cvss * multiplier) + response_bonus
    final = round(min(MAX_SCORE, raw), 1)
    severity = severity_for(final)
    if force_critical:
        severity = Severity.CRITICAL
        final = max(final, 9.0)
    return ScoreResult(
        cvss_base_score=base_cvss,
        context_multiplier=multiplier,
        response_bonus=response_bonus,
        cawasma_final_score=final,
        severity=severity,
    )
