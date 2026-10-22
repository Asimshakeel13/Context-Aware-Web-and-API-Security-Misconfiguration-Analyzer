"""Scan model -- the top-level record for one scan job.

Everything else (endpoints, findings, chains, TLS info, AI insights) hangs off a
scan and is deleted with it via ON DELETE CASCADE.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, Float, Index, Integer, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin
from app.db.models.enums import ScanStatus

if TYPE_CHECKING:
    from app.db.models.ai_insight import AiInsight
    from app.db.models.attack_chain import AttackChain
    from app.db.models.endpoint import Endpoint
    from app.db.models.finding import Finding
    from app.db.models.tls import TlsInfo


class Scan(Base, TimestampMixin):
    __tablename__ = "scans"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )
    target_url: Mapped[str] = mapped_column(String(2048), nullable=False)
    status: Mapped[ScanStatus] = mapped_column(
        Enum(ScanStatus, name="scan_status"),
        default=ScanStatus.QUEUED,
        nullable=False,
        index=True,
    )
    # Progress 0-100 and a human-readable current stage (spec section 24).
    progress: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    current_stage: Mapped[str | None] = mapped_column(String(128), nullable=True)

    # Timezone-aware: the scan runner writes datetime.now(UTC).
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    duration_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)

    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # --- Relationships (all cascade-delete with the scan) ------------------
    endpoints: Mapped[list[Endpoint]] = relationship(
        back_populates="scan", cascade="all, delete-orphan", passive_deletes=True
    )
    findings: Mapped[list[Finding]] = relationship(
        back_populates="scan", cascade="all, delete-orphan", passive_deletes=True
    )
    attack_chains: Mapped[list[AttackChain]] = relationship(
        back_populates="scan", cascade="all, delete-orphan", passive_deletes=True
    )
    tls_info: Mapped[list[TlsInfo]] = relationship(
        back_populates="scan", cascade="all, delete-orphan", passive_deletes=True
    )
    ai_insights: Mapped[list[AiInsight]] = relationship(
        back_populates="scan", cascade="all, delete-orphan", passive_deletes=True
    )

    __table_args__ = (
        Index("ix_scans_status_created", "status", "created_at"),
    )

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"<Scan {self.id} {self.status} {self.target_url!r}>"
