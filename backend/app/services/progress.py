"""Scan progress events over Redis pub/sub (spec sections 23-24).

The Celery worker publishes progress to a per-scan Redis channel; the FastAPI
WebSocket endpoint subscribes and forwards events to the browser. The worker
cannot write to FastAPI's sockets directly, so Redis is the bridge.
"""
from __future__ import annotations

import json

from app.config import settings
from app.utils.logging import get_logger

logger = get_logger(__name__)


def channel_for(scan_id) -> str:
    return f"scan:{scan_id}:events"


class RedisProgressPublisher:
    """Publishes JSON progress events to a scan's Redis channel."""

    def __init__(self, scan_id) -> None:
        self.scan_id = str(scan_id)
        self.channel = channel_for(self.scan_id)
        self._redis = None

    async def _client(self):
        if self._redis is None:
            import redis.asyncio as aioredis

            self._redis = aioredis.from_url(settings.REDIS_URL)
        return self._redis

    async def publish(self, stage: str, percent: int, message: str) -> None:
        event = {"scan_id": self.scan_id, "stage": stage,
                 "percent": percent, "message": message}
        try:
            client = await self._client()
            await client.publish(self.channel, json.dumps(event))
        except Exception as exc:  # noqa: BLE001 - progress must not fail a scan
            logger.debug("progress publish failed: %s", exc)

    async def close(self) -> None:
        if self._redis is not None:
            try:
                await self._redis.aclose()
            except Exception:  # noqa: BLE001
                pass
