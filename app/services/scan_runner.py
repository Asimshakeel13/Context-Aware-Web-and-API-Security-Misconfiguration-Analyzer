"""Async driver that runs one scan end-to-end (spec section 19/24).

Separated from the Celery task so it can be unit-tested directly (the Celery
task is a thin ``asyncio.run`` wrapper). Updates the Scan row's status/progress,
publishes progress to Redis, persists the result, and records failures honestly.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select

from app.database.models import Scan
from app.database.models.enums import ScanStatus
from app.database.session import session_scope
from app.scanner.pipeline import run_pipeline
from app.services.progress import RedisProgressPublisher
from app.services.result_service import persist_result
from app.utils.logging import get_logger

logger = get_logger(__name__)


async def run_scan_async(scan_id: str | uuid.UUID, *, probe: bool = True) -> None:
    """Run the scan identified by ``scan_id``; never raises."""
    sid = uuid.UUID(str(scan_id))
    publisher = RedisProgressPublisher(sid)
    started = datetime.now(timezone.utc)

    async with session_scope() as session:
        scan = (await session.execute(select(Scan).where(Scan.id == sid))).scalar_one_or_none()
        if scan is None:
            logger.warning("run_scan: scan %s not found", sid)
            return

        scan.status = ScanStatus.RUNNING
        scan.started_at = started
        scan.progress = 0
        scan.current_stage = "initializing"
        await session.commit()

        last_pct = -10

        async def on_progress(stage: str, percent: int, message: str) -> None:
            nonlocal last_pct
            await publisher.publish(stage, percent, message)
            if percent - last_pct >= 5 or percent >= 100:
                scan.progress = percent
                scan.current_stage = stage
                await session.commit()
                last_pct = percent

        try:
            result = await run_pipeline(scan.target_url, on_progress, probe=probe)
            await persist_result(session, scan, result)
            scan.status = ScanStatus.COMPLETED
            scan.progress = 100
            scan.current_stage = "completed"
            scan.completed_at = datetime.now(timezone.utc)
            scan.duration_seconds = (scan.completed_at - started).total_seconds()
            await session.commit()
            logger.info("scan %s completed: %s", sid, result.stats)
        except Exception as exc:  # noqa: BLE001 - record failure, never propagate
            logger.exception("scan %s failed", sid)
            await session.rollback()
            scan = (await session.execute(
                select(Scan).where(Scan.id == sid))).scalar_one_or_none()
            if scan is not None:
                scan.status = ScanStatus.FAILED
                scan.error_message = str(exc)[:500]
                scan.completed_at = datetime.now(timezone.utc)
                await session.commit()
        finally:
            await publisher.close()
