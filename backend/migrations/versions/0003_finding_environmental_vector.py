"""finding environmental vector

Adds ``findings.final_vector`` (the CVSS v3.1 base vector plus the CR/IR/AR
security requirements the context-aware score was computed from) and
``findings.score_reasons``. Both are nullable: findings scored by the interim
multiplier formula have neither.

Revision ID: 0003
Revises: 0002
Create Date: 2026-10-25
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = '0003'
down_revision: str | None = '0002'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_JSON = sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), 'postgresql')


def upgrade() -> None:
    with op.batch_alter_table('findings', schema=None) as batch_op:
        batch_op.add_column(sa.Column('final_vector', sa.String(length=160), nullable=True))
        batch_op.add_column(sa.Column('score_reasons', _JSON, nullable=True))


def downgrade() -> None:
    with op.batch_alter_table('findings', schema=None) as batch_op:
        batch_op.drop_column('score_reasons')
        batch_op.drop_column('final_vector')
