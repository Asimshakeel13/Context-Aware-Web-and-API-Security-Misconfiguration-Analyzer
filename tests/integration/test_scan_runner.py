"""Scan runner drives QUEUED -> RUNNING -> COMPLETED and persists results."""
from __future__ import annotations

import contextlib

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker

import app.services.scan_runner as runner
from app.database.models import Finding, Scan
from app.database.models.enums import ScanStatus
from app.scanner.pipeline import run_pipeline
from tests.fixtures.mock_server import mock_server

pytestmark = pytest.mark.asyncio


async def test_scan_runner_completes(engine, monkeypatch):
    async_session = async_sessionmaker(bind=engine, expire_on_commit=False)

    @contextlib.asynccontextmanager
    async def fake_scope():
        session = async_session()
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

    async def noop(self, *a, **k):
        return None

    async def patched_pipeline(target, on_progress=None, *, probe=True, allow_private=False):
        return await run_pipeline(target, on_progress, probe=False, allow_private=True)

    monkeypatch.setattr(runner, "session_scope", fake_scope)
    monkeypatch.setattr(runner, "run_pipeline", patched_pipeline)
    monkeypatch.setattr(runner.RedisProgressPublisher, "publish", noop)
    monkeypatch.setattr(runner.RedisProgressPublisher, "close", noop)

    with mock_server() as base:
        async with async_session() as s:
            scan = Scan(target_url=base, status=ScanStatus.QUEUED, progress=0)
            s.add(scan)
            await s.commit()
            await s.refresh(scan)
            sid = scan.id
        await runner.run_scan_async(sid)

    async with async_session() as s:
        scan = await s.get(Scan, sid)
        assert scan.status == ScanStatus.COMPLETED
        assert scan.progress == 100
        assert scan.duration_seconds is not None
        from sqlalchemy import func, select
        n = (await s.execute(
            select(func.count()).select_from(Finding).where(Finding.scan_id == sid)
        )).scalar_one()
        assert n > 0
