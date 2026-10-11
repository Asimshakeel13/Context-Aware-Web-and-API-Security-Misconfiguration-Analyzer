"""Report endpoints (spec sections 25-27).

``GET /api/scans/{id}/report?format=json|csv|html|pdf`` returns the assessment
report in the requested format. All content is pre-redacted by the scanner.
"""
from __future__ import annotations

import uuid
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_session
from app.services.report_service import (
    ReportFormatUnavailable, build_report_data, render_csv, render_html,
    render_json, render_pdf,
)

router = APIRouter(prefix="/api/scans", tags=["reports"])

_MEDIA = {
    "json": "application/json",
    "csv": "text/csv",
    "html": "text/html; charset=utf-8",
    "pdf": "application/pdf",
}


@router.get("/{scan_id}/report")
async def get_report(
    scan_id: uuid.UUID,
    format: Literal["json", "csv", "html", "pdf"] = Query("json"),
    download: bool = Query(False),
    session: AsyncSession = Depends(get_session),
) -> Response:
    data = await build_report_data(session, scan_id)
    if data is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scan not found.")

    if format == "json":
        content: bytes = render_json(data).encode()
    elif format == "csv":
        content = render_csv(data).encode()
    elif format == "html":
        content = render_html(data).encode()
    else:  # pdf
        try:
            content = render_pdf(data)
        except ReportFormatUnavailable as exc:
            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED, detail=str(exc)
            ) from exc

    headers = {}
    if download or format in ("csv", "pdf"):
        ext = format
        headers["Content-Disposition"] = (
            f'attachment; filename="cawasma-{scan_id}.{ext}"'
        )
    return Response(content=content, media_type=_MEDIA[format], headers=headers)
