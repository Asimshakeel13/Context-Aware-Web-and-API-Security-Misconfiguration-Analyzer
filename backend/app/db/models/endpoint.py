"""Endpoint model -- one discovered URL/method within a scan.

Stores the NLP context classification (contribution 1) alongside basic response
metadata. The full data model matches spec section 19.
"""
from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import (
    JSON,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin
from app.db.models.enums import ContextClass, DiscoveryMethod

if TYPE_CHECKING:
    from app.db.models.cookie import Cookie
    from app.db.models.finding import Finding
    from app.db.models.header import Header
    from app.db.models.scan import Scan


class Endpoint(Base, TimestampMixin):
    __tablename__ = "endpoints"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )
    scan_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("scans.id", ondelete="CASCADE"), nullable=False, index=True
    )

    url: Mapped[str] = mapped_column(String(2048), nullable=False)
    path: Mapped[str] = mapped_column(String(2048), nullable=False)
    method: Mapped[str] = mapped_column(String(10), default="GET", nullable=False)
    status_code: Mapped[int | None] = mapped_column(Integer, nullable=True)
    content_type: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # --- NLP context classification (contribution 1) -----------------------
    context_class: Mapped[ContextClass | None] = mapped_column(
        Enum(ContextClass, name="context_class"), nullable=True
    )
    context_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    # Explainable reasons, e.g. ["Contains authentication-related tokens"].
    context_reason: Mapped[list | None] = mapped_column(JSON, nullable=True)

    response_time: Mapped[float | None] = mapped_column(Float, nullable=True)
    discovered_by: Mapped[DiscoveryMethod] = mapped_column(
        Enum(DiscoveryMethod, name="discovery_method"),
        default=DiscoveryMethod.SEED,
        nullable=False,
    )

    # --- Relationships -----------------------------------------------------
    scan: Mapped[Scan] = relationship(back_populates="endpoints")
    findings: Mapped[list[Finding]] = relationship(
        back_populates="endpoint", passive_deletes=True
    )
    headers: Mapped[list[Header]] = relationship(
        back_populates="endpoint", cascade="all, delete-orphan", passive_deletes=True
    )
    cookies: Mapped[list[Cookie]] = relationship(
        back_populates="endpoint", cascade="all, delete-orphan", passive_deletes=True
    )

    __table_args__ = (
        # The same URL+method is discovered once per scan (dedup, spec 18).
        UniqueConstraint("scan_id", "url", "method", name="uq_endpoint_scan_url_method"),
        Index("ix_endpoints_scan_context", "scan_id", "context_class"),
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Endpoint {self.method} {self.path} ctx={self.context_class}>"
