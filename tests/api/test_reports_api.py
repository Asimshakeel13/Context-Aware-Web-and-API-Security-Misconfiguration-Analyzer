"""API tests for the report endpoint (route wiring + formats)."""
from __future__ import annotations

import uuid

import pytest

from app.database.models import Scan
from app.database.models.enums import ScanStatus
from app.scanner.pipeline import run_pipeline
from app.services.result_service import persist_result
from tests.fixtures.mock_server import mock_server

pytestmark = pytest.mark.asyncio


async def _seed(sessionmaker_) -> uuid.UUID:
    with mock_server() as base:
        result = await run_pipeline(base, probe=False, allow_private=True)
    async with sessionmaker_() as session:
        scan = Scan(target_url=result.target, status=ScanStatus.COMPLETED, progress=100)
        session.add(scan)
        await session.commit()
        await session.refresh(scan)
        await persist_result(session, scan, result)
        await session.commit()
        return scan.id


async def test_report_json(client, sessionmaker_):
    scan_id = await _seed(sessionmaker_)
    r = await client.get(f"/api/scans/{scan_id}/report?format=json")
    assert r.status_code == 200
    body = r.json()
    assert body["summary"]["total_findings"] >= 1


async def test_report_csv_has_attachment(client, sessionmaker_):
    scan_id = await _seed(sessionmaker_)
    r = await client.get(f"/api/scans/{scan_id}/report?format=csv")
    assert r.status_code == 200
    assert "text/csv" in r.headers["content-type"]
    assert "attachment" in r.headers.get("content-disposition", "")


async def test_report_html(client, sessionmaker_):
    scan_id = await _seed(sessionmaker_)
    r = await client.get(f"/api/scans/{scan_id}/report?format=html")
    assert r.status_code == 200
    assert "CAWASMA Security Report" in r.text


async def test_report_pdf_graceful(client, sessionmaker_):
    scan_id = await _seed(sessionmaker_)
    r = await client.get(f"/api/scans/{scan_id}/report?format=pdf")
    # 200 if WeasyPrint native libs are present, 501 if not -- never 500.
    assert r.status_code in (200, 501)


async def test_report_not_found(client):
    r = await client.get(f"/api/scans/{uuid.uuid4()}/report?format=json")
    assert r.status_code == 404
