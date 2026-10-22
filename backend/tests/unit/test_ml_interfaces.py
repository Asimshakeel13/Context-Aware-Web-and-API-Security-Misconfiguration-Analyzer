"""The ML stubs and the built-in classifiers honour the same contracts."""
from __future__ import annotations

import pytest

from app.core.sensitivity import SensitivityClassifier
from app.ml.body_signals import MLBodyClassifier
from app.ml.endpoint_sensitivity import MLEndpointClassifier
from app.ml.interfaces import BodySignalClassifier, EndpointSensitivityClassifier


def test_builtin_endpoint_classifier_satisfies_protocol():
    assert isinstance(SensitivityClassifier(use_embeddings=False),
                      EndpointSensitivityClassifier)


def test_stubs_satisfy_protocols():
    assert isinstance(MLEndpointClassifier(), EndpointSensitivityClassifier)
    assert isinstance(MLBodyClassifier(), BodySignalClassifier)


def test_stubs_are_not_silently_used():
    with pytest.raises(NotImplementedError):
        MLEndpointClassifier().classify("/api/login")
    with pytest.raises(NotImplementedError):
        MLBodyClassifier().classify("{}")
