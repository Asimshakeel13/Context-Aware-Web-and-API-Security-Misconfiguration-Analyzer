"""Scan request/response schemas (spec sections 26-29, 45)."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.db.models.enums import ScanStatus


def _public_status(value: Any) -> Any:
    # DONE is published as "COMPLETED" (docs/db-decisions.md, D3).
    return value.public_value if isinstance(value, ScanStatus) else value


class ScanCreate(BaseModel):
    target_url: str = Field(
        ..., examples=["https://example.com"], description="HTTPS target URL."
    )
    authorization_confirmed: bool = Field(
        False, description="Operator confirms they are authorised to test the target."
    )


class ScanCreated(BaseModel):
    """Returned immediately after POST /api/scans (spec section 23)."""

    scan_id: uuid.UUID
    status: str

    _status = field_validator("status", mode="before")(_public_status)


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
    status: str
    progress: int
    current_stage: str | None = None

    _status = field_validator("status", mode="before")(_public_status)


class ScanResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    target_url: str
    status: str
    progress: int
    current_stage: str | None
    options: dict[str, Any]
    authorization_confirmed: bool
    authorization_confirmed_at: datetime | None
    started_at: datetime | None
    completed_at: datetime | None
    duration_seconds: float | None
    error_message: str | None
    created_at: datetime
    updated_at: datetime

    _status = field_validator("status", mode="before")(_public_status)


class ScanDetail(ScanResponse):
    """Scan response enriched with a summary of counts."""

    summary: ScanSummary
