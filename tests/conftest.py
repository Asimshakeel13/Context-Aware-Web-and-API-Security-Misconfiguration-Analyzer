"""Shared test fixtures.

Uses a file-based async SQLite database so the API can be tested without a real
PostgreSQL. The scanner modules are DB-free and tested directly.
"""
from __future__ import annotations

import os
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.database.models import Base
from app.database.session import get_session
from app.config import settings as _settings
_settings.AUTO_DISPATCH_SCANS = False  # no Celery broker in tests
from app.main import app

TEST_DB = "sqlite+aiosqlite:///./_test.db"


@pytest_asyncio.fixture
async def engine():
    if os.path.exists("_test.db"):
        os.remove("_test.db")
    eng = create_async_engine(TEST_DB, echo=False)
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield eng
    await eng.dispose()
    if os.path.exists("_test.db"):
        os.remove("_test.db")


@pytest_asyncio.fixture
async def sessionmaker_(engine):
    return async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


@pytest_asyncio.fixture
async def client(sessionmaker_) -> AsyncGenerator[AsyncClient, None]:
    async def _override() -> AsyncGenerator[AsyncSession, None]:
        async with sessionmaker_() as session:
            yield session

    app.dependency_overrides[get_session] = _override
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()
