"""Contracts between the scanner engine and the ML classifiers.

These Protocols mirror the signatures the pipeline already calls
(``app.core.pipeline``). Keep them stable: the engine, CVSS scoring and tests
depend on the result types, not on any particular model.
"""
from __future__ import annotations

from typing import Protocol, runtime_checkable

from app.core.body_classifier import BodyClassification
from app.core.sensitivity import ClassificationResult


@runtime_checkable
class EndpointSensitivityClassifier(Protocol):
    """Classify an endpoint path into a sensitivity class with reasons."""

    def classify(
        self, path: str, extra_expansions: dict[str, str] | None = None
    ) -> ClassificationResult: ...


@runtime_checkable
class BodySignalClassifier(Protocol):
    """Detect sensitive-data signals in a (truncated) response body."""

    def classify(
        self, body: str | None, content_type: str | None = None
    ) -> BodyClassification: ...
