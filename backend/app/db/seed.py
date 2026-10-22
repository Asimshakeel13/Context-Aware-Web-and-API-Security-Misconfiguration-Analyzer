"""Seed the database with one completed demo scan.

Run with ``python -m app.db.seed`` (``make seed``). Idempotent: the demo scan has
a fixed id and is skipped if it already exists. The data mirrors the worked
example in docs/06-scoring-model.md -- the same finding on a LOW and a CRITICAL
endpoint -- and is scored through :func:`app.core.cvss.compute_score`, so the
frontend can be developed against realistic rows without running a scan.
"""
from __future__ import annotations

import asyncio
import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import select

from app.core.checks.catalog import CATALOG
from app.core.cvss import compute_score
from app.db.models import Endpoint, Finding, Scan
from app.db.models.enums import ContextClass, DiscoveryMethod, ScanStatus
from app.db.session import session_scope
from app.utils.logging import configure_logging, get_logger

logger = get_logger(__name__)

DEMO_SCAN_ID = uuid.UUID("00000000-0000-4000-8000-00000000c0de")
DEMO_TARGET = "https://demo.example.com"

# (path, context class, confidence, discovered by, response bonus)
_ENDPOINTS = [
    ("/about", ContextClass.LOW, 0.91, DiscoveryMethod.HTML, 0.0),
    ("/api/payment/checkout", ContextClass.CRITICAL, 0.95, DiscoveryMethod.JAVASCRIPT, 2.0),
]
_RULES = ["HDR-003", "HDR-002"]


async def seed() -> bool:
    """Insert the demo scan. Returns False if it was already present."""
    async with session_scope() as session:
        existing = await session.scalar(select(Scan.id).where(Scan.id == DEMO_SCAN_ID))
        if existing is not None:
            logger.info("seed: demo scan %s already present, skipping", DEMO_SCAN_ID)
            return False

        finished = datetime.now(UTC)
        scan = Scan(
            id=DEMO_SCAN_ID,
            target_url=DEMO_TARGET,
            status=ScanStatus.COMPLETED,
            progress=100,
            current_stage="completed",
            started_at=finished - timedelta(seconds=42),
            completed_at=finished,
            duration_seconds=42.0,
        )
        session.add(scan)

        for path, ctx, confidence, discovered_by, bonus in _ENDPOINTS:
            endpoint = Endpoint(
                scan=scan,
                url=DEMO_TARGET + path,
                path=path,
                status_code=200,
                content_type="application/json" if path.startswith("/api") else "text/html",
                context_class=ctx,
                context_confidence=confidence,
                context_reason=[f"seeded demo endpoint ({ctx.value})"],
                response_time=0.12,
                discovered_by=discovered_by,
            )
            session.add(endpoint)
            for rule_id in _RULES:
                meta = CATALOG[rule_id]
                score = compute_score(meta.base_score, ctx, bonus)
                session.add(Finding(
                    scan=scan,
                    endpoint=endpoint,
                    rule_id=meta.rule_id,
                    title=meta.name,
                    category=meta.category,
                    context_class=ctx,
                    context_confidence=confidence,
                    cvss_vector=meta.cvss_vector,
                    cvss_base_score=score.cvss_base_score,
                    cawasma_context_multiplier=score.context_multiplier,
                    response_bonus=score.response_bonus,
                    cawasma_final_score=score.cawasma_final_score,
                    severity=score.severity,
                    evidence="Seeded demo finding.",
                    impact=meta.impact,
                    recommendation=meta.recommendation,
                    references=list(meta.references),
                    limitation=meta.limitation,
                ))
    logger.info("seed: inserted demo scan %s (%s)", DEMO_SCAN_ID, DEMO_TARGET)
    return True


def main() -> None:
    configure_logging()
    asyncio.run(seed())


if __name__ == "__main__":
    main()
