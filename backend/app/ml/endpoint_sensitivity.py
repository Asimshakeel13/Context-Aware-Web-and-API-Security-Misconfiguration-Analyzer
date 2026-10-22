"""Learned endpoint-sensitivity classifier (stub, owner: Asim).

Replace :meth:`MLEndpointClassifier.classify` with the trained model. Until then
the engine keeps using :class:`app.core.sensitivity.SensitivityClassifier`.
"""
from __future__ import annotations

from app.core.sensitivity import ClassificationResult


class MLEndpointClassifier:
    """Satisfies :class:`app.ml.interfaces.EndpointSensitivityClassifier`."""

    def classify(
        self, path: str, extra_expansions: dict[str, str] | None = None
    ) -> ClassificationResult:
        raise NotImplementedError("ML endpoint classifier not implemented yet")
