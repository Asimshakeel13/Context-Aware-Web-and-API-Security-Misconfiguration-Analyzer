"""Endpoint sensitivity classifier (owner: Asim). STUB.

Asim replaces this module in his Prompt 6 (embedding classifier). Keep the
signature from docs/cvss-mapping-contract.md; until then it delegates to the
built-in keyword/embedding classifier, so it already conforms.
"""
from __future__ import annotations

from app.core.contracts import EndpointInfo, SensitivityClass, builtin_classify


def classify(endpoint: EndpointInfo) -> SensitivityClass:
    """Sensitivity class of ``endpoint``. Must not raise (contract rule 1)."""
    return builtin_classify(endpoint)
