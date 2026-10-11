"""Endpoint, finding, and attack-chain response schemas (spec sections 29, 46)."""
from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.database.models.enums import (
    ContextClass,
    DiscoveryMethod,
    FindingCategory,
    Severity,
)


class EndpointResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    url: str
    path: str
    method: str
    status_code: int | None
    content_type: str | None
    context_class: ContextClass | None
    context_confidence: float | None
    context_reason: list | None
    response_time: float | None
    discovered_by: DiscoveryMethod
    created_at: datetime


class FindingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    rule_id: str
    title: str
    category: FindingCategory
    endpoint_id: uuid.UUID | None
    context_class: ContextClass | None
    context_confidence: float | None
    # Official CVSS (unmodified) vs CAWASMA custom score kept distinct.
    cvss_vector: str | None
    cvss_base_score: float | None
    cawasma_context_multiplier: float | None
    response_bonus: float | None
    cawasma_final_score: float | None
    severity: Severity
    evidence: str | None
    impact: str | None
    recommendation: str | None
    references: list | None
    limitation: str | None
    created_at: datetime


class ChainResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    chain_code: str
    name: str
    description: str | None
    template_composite_score: float
    severity: Severity
    created_at: datetime
