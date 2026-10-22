"""The demo seed is idempotent and scored through the real CVSS path."""
from __future__ import annotations

import contextlib

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import async_sessionmaker

import app.db.seed as seed_mod
from app.db.models import Finding

pytestmark = pytest.mark.asyncio


async def test_seed_is_idempotent(engine, monkeypatch):
    async_session = async_sessionmaker(bind=engine, expire_on_commit=False)

    @contextlib.asynccontextmanager
    async def fake_scope():
        async with async_session() as session:
            yield session
            await session.commit()

    monkeypatch.setattr(seed_mod, "session_scope", fake_scope)

    assert await seed_mod.seed() is True
    assert await seed_mod.seed() is False

    async with async_session() as s:
        count = await s.scalar(select(func.count()).select_from(Finding))
        scores = {
            (f.endpoint_id is not None, f.rule_id, f.cawasma_final_score)
            for f in (await s.execute(select(Finding))).scalars()
        }
    assert count == 4
    # Same finding, different context -> different final score (docs/06).
    hdr003 = sorted(score for _, rule, score in scores if rule == "HDR-003")
    assert hdr003 == [3.7, 10.0]
