"""Findings / endpoints / chains listing endpoints (spec section 26)."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas.common import Page, PaginationMeta
from app.api.schemas.endpoint import (
    ChainResponse,
    EndpointResponse,
    FindingResponse,
)
from app.dependencies import PaginationParams, pagination
from app.database.session import get_session
from app.services import scan_service

router = APIRouter(prefix="/api/scans", tags=["results"])


async def _ensure_scan(session: AsyncSession, scan_id: uuid.UUID) -> None:
    if await scan_service.get_scan(session, scan_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Scan not found."
        )


@router.get("/{scan_id}/findings", response_model=Page[FindingResponse])
async def list_findings(
    scan_id: uuid.UUID,
    page: PaginationParams = Depends(pagination),
    session: AsyncSession = Depends(get_session),
) -> Page[FindingResponse]:
    await _ensure_scan(session, scan_id)
    rows, total = await scan_service.list_findings(
        session, scan_id, page.offset, page.limit
    )
    pages = (total + page.limit - 1) // page.limit
    return Page[FindingResponse](
        items=[FindingResponse.model_validate(r) for r in rows],
        meta=PaginationMeta(page=page.page, limit=page.limit, total=total, pages=pages),
    )


@router.get("/{scan_id}/endpoints", response_model=Page[EndpointResponse])
async def list_endpoints(
    scan_id: uuid.UUID,
    page: PaginationParams = Depends(pagination),
    session: AsyncSession = Depends(get_session),
) -> Page[EndpointResponse]:
    await _ensure_scan(session, scan_id)
    rows, total = await scan_service.list_endpoints(
        session, scan_id, page.offset, page.limit
    )
    pages = (total + page.limit - 1) // page.limit
    return Page[EndpointResponse](
        items=[EndpointResponse.model_validate(r) for r in rows],
        meta=PaginationMeta(page=page.page, limit=page.limit, total=total, pages=pages),
    )


@router.get("/{scan_id}/chains", response_model=list[ChainResponse])
async def list_chains(
    scan_id: uuid.UUID, session: AsyncSession = Depends(get_session)
) -> list[ChainResponse]:
    await _ensure_scan(session, scan_id)
    rows = await scan_service.list_chains(session, scan_id)
    return [ChainResponse.model_validate(r) for r in rows]
