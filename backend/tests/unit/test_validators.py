"""Tests for target URL validation."""
from __future__ import annotations

import pytest

from app.utils.validators import (
    InvalidTargetError,
    same_origin,
    validate_target_url,
)


def test_valid_https_url():
    t = validate_target_url("https://example.com/path?q=1#frag")
    assert t.scheme == "https"
    assert t.host == "example.com"
    assert t.port == 443
    assert "#frag" not in t.url  # fragment stripped


def test_http_rejected_when_https_required():
    with pytest.raises(InvalidTargetError):
        validate_target_url("http://example.com")


def test_http_allowed_when_not_required():
    t = validate_target_url("http://example.com", require_https=False)
    assert t.scheme == "http"
    assert t.port == 80


@pytest.mark.parametrize("bad", ["", "   ", "ftp://example.com", "not a url", "https://"])
def test_malformed_rejected(bad):
    with pytest.raises(InvalidTargetError):
        validate_target_url(bad)


def test_same_origin():
    assert same_origin("https://a.com/x", "https://a.com/y")
    assert not same_origin("https://a.com", "https://b.com")
    assert not same_origin("https://a.com", "http://a.com")
