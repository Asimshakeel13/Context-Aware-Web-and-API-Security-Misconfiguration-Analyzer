"""app/ml stubs honour the ML contract (docs/cvss-mapping-contract.md).

Asim replaces these modules (his Prompts 6 and 7); this test keeps whatever
lives there conforming.
"""
from __future__ import annotations

from app.core.contracts import (
    BodySignal,
    EndpointInfo,
    ResponseInfo,
    SensitivityClass,
    check_conformance,
)
from app.ml import body_classifier, sensitivity


def test_ml_modules_conform_to_the_contract():
    assert check_conformance(sensitivity.classify, body_classifier.analyze) == []


def test_stubs_answer_like_the_builtin_classifiers():
    endpoint = EndpointInfo("https://shop.example.com/api/payment/checkout",
                            "/api/payment/checkout")
    assert sensitivity.classify(endpoint) is SensitivityClass.CRITICAL
    response = ResponseInfo("https://shop.example.com/.env", 200, "text/plain",
                            body="DB_PASSWORD=hunter2")
    assert BodySignal.CREDENTIALS in body_classifier.analyze(response)
