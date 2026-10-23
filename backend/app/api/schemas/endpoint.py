"""Endpoint, finding, and attack-chain response schemas (spec sections 29, 46)."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.db.models.enums import (
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
    context_reason: list[str] | None
    body_signals: dict[str, Any]
    response_time: float | None
    discovered_by: DiscoveryMethod
    created_at: datetime


class FindingResponse(BaseModel):
    """Public finding shape.

    JSON names predate the DB column renames and are kept so the frontend keeps
    working (docs/db-decisions.md, D2): ``rule_id`` <- ``check_id``,
    ``cvss_base_score`` <- ``base_score``, ``cawasma_final_score`` <-
    ``final_score``, ``severity`` <- ``severity_bucket``, ``evidence`` <-
    ``evidence["text"]`` (full JSON in ``evidence_details``).
    """

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: uuid.UUID
    rule_id: str = Field(validation_alias="check_id")
    title: str
    category: FindingCategory
    endpoint_id: uuid.UUID | None
    context_class: ContextClass | None
    context_confidence: float | None
    owasp_map: list[str]
    cwe_map: list[str]
    # Official CVSS (unmodified) vs CAWASMA custom score kept distinct.
    cvss_vector: str
    cvss_base_score: float = Field(validation_alias="base_score")
    cawasma_context_multiplier: float | None
    response_bonus: float | None
    cawasma_final_score: float = Field(validation_alias="final_score")
    severity: Severity = Field(validation_alias="severity_bucket")
    evidence: str | None = Field(validation_alias="evidence")
    evidence_details: dict[str, Any] = Field(validation_alias="evidence")
    impact: str | None
    recommendation: str | None
    references: list | None
    limitation: str | None
    created_at: datetime

    @field_validator("evidence", mode="before")
    @classmethod
    def _evidence_text(cls, value: Any) -> Any:
        return value.get("text") if isinstance(value, dict) else value


class ChainResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    chain_code: str
    name: str
    description: str | None
    template_composite_score: float
    severity: Severity
    created_at: datetime
