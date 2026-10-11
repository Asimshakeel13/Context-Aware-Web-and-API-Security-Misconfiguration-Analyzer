"""Scan request/response schemas (spec sections 26-29, 45)."""
from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.database.models.enums import ScanStatus


class ScanCreate(BaseModel):
    target_url: str = Field(
        ..., examples=["https://example.com"], description="HTTPS target URL."
    )


class ScanCreated(BaseModel):
    """Returned immediately after POST /api/scans (spec section 23)."""

    scan_id: uuid.UUID
    status: ScanStatus


class ScanSummary(BaseModel):
    endpoints: int = 0
    findings: int = 0
    critical: int = 0
    high: int = 0
    medium: int = 0
    low: int = 0
    info: int = 0


class ScanStatusResponse(BaseModel):
    scan_id: uuid.UUID
    status: ScanStatus
    progress: int
    current_stage: str | None = None


class ScanResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    target_url: str
    status: ScanStatus
    progress: int
    current_stage: str | None
    started_at: datetime | None
    completed_at: datetime | None
    duration_seconds: float | None
    error_message: str | None
    created_at: datetime
    updated_at: datetime


class ScanDetail(ScanResponse):
    """Scan response enriched with a summary of counts."""

    summary: ScanSummary
