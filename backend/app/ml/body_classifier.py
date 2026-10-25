"""Response-body signal classifier (owner: Asim). STUB.

Asim replaces this module in his Prompt 7. Keep the signature from
docs/cvss-mapping-contract.md; until then it delegates to the built-in
regex/Luhn classifier, so it already conforms.
"""
from __future__ import annotations

from app.core.contracts import BodySignal, ResponseInfo, builtin_analyze


def analyze(response: ResponseInfo) -> set[BodySignal]:
    """Sensitive-data signals in ``response.body``. Must not raise (contract rule 1)."""
    return builtin_analyze(response)
