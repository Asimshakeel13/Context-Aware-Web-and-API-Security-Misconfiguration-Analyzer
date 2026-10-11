"""Report assembly + rendering tests."""
from __future__ import annotations

import json

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.database.models import Scan
from app.database.models.enums import ScanStatus
from app.scanner.pipeline import run_pipeline
from app.services.report_service import (
    ReportFormatUnavailable, build_report_data, render_csv, render_html,
    render_json, render_pdf,
)
from app.services.result_service import persist_result
from tests.fixtures.mock_server import mock_server

pytestmark = pytest.mark.asyncio


async def _seed(engine):
    async_session = async_sessionmaker(bind=engine, expire_on_commit=False)
    with mock_server() as base:
        result = await run_pipeline(base, probe=False, allow_private=True)
    async with async_session() as session:
        scan = Scan(target_url=result.target, status=ScanStatus.COMPLETED, progress=100)
        session.add(scan)
        await session.commit()
        await session.refresh(scan)
        await persist_result(session, scan, result)
        await session.commit()
        return scan.id, async_session


async def test_report_formats(engine):
    scan_id, async_session = await _seed(engine)
    async with async_session() as session:
        data = await build_report_data(session, scan_id)

    assert data is not None
    # JSON parses and keeps base vs final distinct.
    parsed = json.loads(render_json(data))
    assert parsed["summary"]["total_findings"] >= 1
    assert "cvss_base_score" in parsed["findings"][0]
    assert "cawasma_final_score" in parsed["findings"][0]

    # CSV has a header + at least one row.
    csv_text = render_csv(data)
    assert "cawasma_final_score" in csv_text.splitlines()[0]
    assert len(csv_text.splitlines()) >= 2

    # HTML renders and labels the score as non-official.
    html = render_html(data)
    assert "CAWASMA Security Report" in html
    assert "not an official CVSS" in html


async def test_pdf_unavailable_is_graceful(engine):
    scan_id, async_session = await _seed(engine)
    async with async_session() as session:
        data = await build_report_data(session, scan_id)
    try:
        pdf = render_pdf(data)
        assert pdf[:4] == b"%PDF"           # if WeasyPrint is present
    except ReportFormatUnavailable:
        pass                                 # acceptable when native libs absent


async def test_report_not_found(engine):
    import uuid
    async_session = async_sessionmaker(bind=engine, expire_on_commit=False)
    async with async_session() as session:
        assert await build_report_data(session, uuid.uuid4()) is None
