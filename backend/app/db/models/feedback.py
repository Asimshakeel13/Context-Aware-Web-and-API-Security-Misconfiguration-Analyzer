"""Feedback model -- analyst correction / false-positive flag for a finding.

Lets an analyst mark a finding as a false positive and add a note, which can
later feed classifier tuning (spec section 21 & 36).
"""
from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.db.models.finding import Finding


class Feedback(Base, TimestampMixin):
    __tablename__ = "feedback"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )
    finding_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("findings.id", ondelete="CASCADE"), nullable=False, index=True
    )
    is_false_positive: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    note: Mapped[str | None] = mapped_column(Text, nullable=True)

    finding: Mapped[Finding] = relationship(back_populates="feedback")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Feedback finding={self.finding_id} fp={self.is_false_positive}>"
