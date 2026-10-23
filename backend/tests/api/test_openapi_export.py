"""docs/openapi.json is the published contract: it must match the code."""
from __future__ import annotations

import json

from app.api.schemas import CONTRACT_VERSION
from scripts import export_openapi


def test_committed_openapi_matches_the_code():
    assert export_openapi.main(["--check"]) == 0, "run `make openapi` and commit docs/openapi.json"


def test_openapi_declares_the_contract():
    spec = json.loads(export_openapi.render())
    assert spec["info"]["x-contract-version"] == CONTRACT_VERSION
    for path in ("/api/scan", "/api/results/{scan_id}", "/api/results/{scan_id}/export",
                 "/api/scans"):
        assert path in spec["paths"], path
    assert spec["paths"]["/api/scans/{scan_id}"]["get"]["deprecated"] is True
