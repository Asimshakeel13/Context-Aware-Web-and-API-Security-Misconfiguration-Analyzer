"""Scan service -- persistence and orchestration for scans.

The API layer calls these functions; they own all database access so routes
stay thin and the scanner modules stay DB-free. Actual background execution is
wired to Celery in Phase 14; ``create_scan`` currently persists a QUEUED record
and returns immediately (spec section 23), which is the real, honest state.
"""
from __future__ import annotations

import uuid

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas.scan import ScanSummary
from app.config import settings
from app.database.models import (
    AttackChain,
    Endpoint,
    Finding,
    Scan,
    ScanStatus,
    Severity,
)
from app.utils.logging import get_logger
from app.utils.validators import validate_target_url

logger = get_logger(__name__)


async def create_scan(session: AsyncSession, target_url: str) -> Scan:
    """Validate the target and create a QUEUED scan record."""
    parsed = validate_target_url(target_url)  # raises InvalidTargetError
    scan = Scan(target_url=parsed.url, status=ScanStatus.QUEUED, progress=0)
    session.add(scan)
    await session.commit()
    await session.refresh(scan)
    logger.info("scan created id=%s target=%s", scan.id, scan.target_url)
    _dispatch(scan.id)
    return scan


def _dispatch(scan_id) -> None:
    """Start the scan: inline background task, or enqueue on Celery.

    ``RUN_SCANS_INLINE`` runs the scan in-process as an asyncio background task,
    so the full product works without Celery/Redis (simple deployments, demos).
    Otherwise the scan is enqueued on Celery (the docker-compose default).
    Either path is best-effort and never blocks/raises during scan creation.
    """
    if settings.RUN_SCANS_INLINE:
        try:
            import asyncio

            from app.services.scan_runner import run_scan_async

            asyncio.get_running_loop().create_task(run_scan_async(scan_id))
        except Exception as exc:  # noqa: BLE001
            logger.error("failed to start inline scan %s: %s", scan_id, exc)
        return

    if not settings.AUTO_DISPATCH_SCANS:
        return
    try:
        from celery_worker.celery_app import celery_app

        celery_app.send_task("cawasma.run_scan", args=[str(scan_id)])
    except Exception as exc:  # noqa: BLE001 - broker issues must not 500 the request
        logger.error("failed to dispatch scan %s to Celery: %s", scan_id, exc)


async def get_scan(session: AsyncSession, scan_id: uuid.UUID) -> Scan | None:
    return await session.get(Scan, scan_id)


async def list_scans(
    session: AsyncSession, offset: int, limit: int
) -> tuple[list[Scan], int]:
    total = await session.scalar(select(func.count()).select_from(Scan)) or 0
    rows = (
        await session.scalars(
            select(Scan).order_by(Scan.created_at.desc()).offset(offset).limit(limit)
        )
    ).all()
    return list(rows), total


async def delete_scan(session: AsyncSession, scan_id: uuid.UUID) -> bool:
    scan = await session.get(Scan, scan_id)
    if scan is None:
        return False
    await session.delete(scan)  # cascades to the whole graph
    await session.commit()
    return True


async def build_summary(session: AsyncSession, scan_id: uuid.UUID) -> ScanSummary:
    """Aggregate counts for a scan (endpoints, findings by severity)."""
    endpoint_count = await session.scalar(
        select(func.count()).select_from(Endpoint).where(Endpoint.scan_id == scan_id)
    ) or 0
    finding_count = await session.scalar(
        select(func.count()).select_from(Finding).where(Finding.scan_id == scan_id)
    ) or 0

    by_sev = dict(
        (
            await session.execute(
                select(Finding.severity, func.count())
                .where(Finding.scan_id == scan_id)
                .group_by(Finding.severity)
            )
        ).all()
    )
    return ScanSummary(
        endpoints=endpoint_count,
        findings=finding_count,
        critical=by_sev.get(Severity.CRITICAL, 0),
        high=by_sev.get(Severity.HIGH, 0),
        medium=by_sev.get(Severity.MEDIUM, 0),
        low=by_sev.get(Severity.LOW, 0),
        info=by_sev.get(Severity.INFO, 0),
    )


async def list_findings(
    session: AsyncSession, scan_id: uuid.UUID, offset: int, limit: int
) -> tuple[list[Finding], int]:
    total = await session.scalar(
        select(func.count()).select_from(Finding).where(Finding.scan_id == scan_id)
    ) or 0
    rows = (
        await session.scalars(
            select(Finding)
            .where(Finding.scan_id == scan_id)
            .order_by(Finding.cawasma_final_score.desc().nullslast())
            .offset(offset)
            .limit(limit)
        )
    ).all()
    return list(rows), total


async def list_endpoints(
    session: AsyncSession, scan_id: uuid.UUID, offset: int, limit: int
) -> tuple[list[Endpoint], int]:
    total = await session.scalar(
        select(func.count()).select_from(Endpoint).where(Endpoint.scan_id == scan_id)
    ) or 0
    rows = (
        await session.scalars(
            select(Endpoint)
            .where(Endpoint.scan_id == scan_id)
            .order_by(Endpoint.created_at.asc())
            .offset(offset)
            .limit(limit)
        )
    ).all()
    return list(rows), total


async def list_chains(
    session: AsyncSession, scan_id: uuid.UUID
) -> list[AttackChain]:
    rows = (
        await session.scalars(
            select(AttackChain)
            .where(AttackChain.scan_id == scan_id)
            .order_by(AttackChain.template_composite_score.desc())
        )
    ).all()
    return list(rows)
