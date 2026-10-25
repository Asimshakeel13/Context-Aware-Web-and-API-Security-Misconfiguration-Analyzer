"""Behaviour of the shipped checks in config/checks.yaml (review asim-p04).

These pin bugs found in review, not the security judgement behind each check.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from app.config import settings
from app.core.contracts import ResponseInfo
from app.core.specs import load_checks

CHECKS = {c.check_id: c for c in load_checks(Path(settings.CONFIG_DIR) / "checks.yaml").checks}


def _resp(headers: dict[str, str]) -> ResponseInfo:
    return ResponseInfo("https://shop.example.com/", 200, "text/html", headers)


@pytest.mark.parametrize("value, fires", [
    (None, True),                 # header absent
    ("DENY", False),
    ("SAMEORIGIN", False),
    ("sameorigin", False),        # case-insensitive
    (" DENY ", False),
    ("ALLOW-FROM https://x.example", True),
    ("DENY, SAMEORIGIN", True),   # invalid combined value
])
def test_hdr003_fires_only_without_deny_or_sameorigin(value, fires):
    headers = {} if value is None else {"X-Frame-Options": value}
    assert CHECKS["HDR-003"].http_condition.matches(_resp(headers)) is fires
