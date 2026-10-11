"""Tests for attack-chain correlation (Contribution 2)."""
from __future__ import annotations

from app.database.models.enums import Severity
from app.scanner.chains import CHAIN_TEMPLATES, correlate_chains


def test_five_templates_defined():
    codes = {t.code for t in CHAIN_TEMPLATES}
    assert codes == {"C001", "C002", "C003", "C004", "C005"}


def test_no_chain_without_findings():
    assert correlate_chains(set()) == []


def test_c005_env_chain_fires():
    present = {"INF-003", "HDR-007"}  # .env + version leak
    chains = correlate_chains(present)
    codes = {c.code for c in chains}
    assert "C005" in codes
    c005 = next(c for c in chains if c.code == "C005")
    assert c005.composite_score == 9.8
    assert c005.severity == Severity.CRITICAL
    assert "INF-003" in c005.matched_rule_ids


def test_c004_requires_both_mandatory():
    # Only one mandatory present -> must NOT fire.
    assert all(c.code != "C004" for c in correlate_chains({"API-003"}))
    # Both present -> fires.
    assert any(c.code == "C004" for c in correlate_chains({"API-003", "API-006"}))


def test_c001_needs_mandatory_cookie():
    # XSS headers present but no JS-readable cookie -> C001 must not fire.
    assert all(c.code != "C001" for c in correlate_chains({"HDR-002", "HDR-003"}))
    assert any(c.code == "C001" for c in correlate_chains({"HDR-002", "HDR-003", "CKI-001"}))
