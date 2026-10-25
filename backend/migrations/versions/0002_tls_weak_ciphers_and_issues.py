"""tls weak ciphers and issues

Adds the TLS_INFO fields from the data model (docs/project/project-summary.md):
``weak_ciphers`` and ``issues``. Existing rows get ``[]``.

Revision ID: 0002
Revises: 0001
Create Date: 2026-10-25
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = '0002'
down_revision: str | None = '0001'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_JSON = sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), 'postgresql')


def upgrade() -> None:
    with op.batch_alter_table('tls_info', schema=None) as batch_op:
        for column in ('weak_ciphers', 'issues'):
            # Server default only to backfill existing rows; the model sets [] itself.
            batch_op.add_column(sa.Column(column, _JSON, nullable=False,
                                          server_default=sa.text("'[]'")))
    with op.batch_alter_table('tls_info', schema=None) as batch_op:
        for column in ('weak_ciphers', 'issues'):
            batch_op.alter_column(column, server_default=None)


def downgrade() -> None:
    with op.batch_alter_table('tls_info', schema=None) as batch_op:
        batch_op.drop_column('issues')
        batch_op.drop_column('weak_ciphers')
