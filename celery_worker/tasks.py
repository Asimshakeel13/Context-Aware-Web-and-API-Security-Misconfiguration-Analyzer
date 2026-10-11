"""Celery task definitions (spec section 23).

The HTTP layer enqueues ``cawasma.run_scan`` and returns immediately; the worker
runs the async pipeline via ``asyncio.run`` in its own process and publishes
progress to Redis for the WebSocket to forward.
"""
from __future__ import annotations

import asyncio

from app.services.scan_runner import run_scan_async
from app.utils.logging import get_logger
from celery_worker.celery_app import celery_app

logger = get_logger(__name__)


@celery_app.task(name="cawasma.ping")
def ping() -> str:
    """Trivial task used to verify the worker/broker wiring."""
    return "pong"


@celery_app.task(name="cawasma.run_scan", bind=True)
def run_scan(self, scan_id: str) -> str:
    """Run a full scan in the worker process."""
    logger.info("worker received scan %s (task %s)", scan_id, self.request.id)
    asyncio.run(run_scan_async(scan_id))
    return scan_id
