"""Learned response-body signal classifier (stub, owner: Asim).

Replace :meth:`MLBodyClassifier.classify` with the trained model. Until then
the engine keeps using :func:`app.core.body_classifier.classify_body`.
"""
from __future__ import annotations

from app.core.body_classifier import BodyClassification


class MLBodyClassifier:
    """Satisfies :class:`app.ml.interfaces.BodySignalClassifier`."""

    def classify(
        self, body: str | None, content_type: str | None = None
    ) -> BodyClassification:
        raise NotImplementedError("ML body classifier not implemented yet")
