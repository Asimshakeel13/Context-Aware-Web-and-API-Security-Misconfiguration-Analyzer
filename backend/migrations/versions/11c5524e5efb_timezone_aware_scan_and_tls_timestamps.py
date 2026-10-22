"""timezone-aware scan and tls timestamps

The scan runner and TLS probe write UTC-aware datetimes; asyncpg rejects those
for TIMESTAMP WITHOUT TIME ZONE columns. Existing naive values are interpreted
as UTC.

Revision ID: 11c5524e5efb
Revises: f24db017e48b
Create Date: 2026-10-22 17:35:05.484855
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = '11c5524e5efb'
down_revision: str | None = 'f24db017e48b'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_COLUMNS = [
    ('scans', 'started_at'),
    ('scans', 'completed_at'),
    ('tls_info', 'cert_not_after'),
]


def upgrade() -> None:
    for table, column in _COLUMNS:
        with op.batch_alter_table(table, schema=None) as batch_op:
            batch_op.alter_column(
                column,
                existing_type=sa.DateTime(),
                type_=sa.DateTime(timezone=True),
                existing_nullable=True,
                postgresql_using=f"{column} AT TIME ZONE 'UTC'",
            )


def downgrade() -> None:
    for table, column in reversed(_COLUMNS):
        with op.batch_alter_table(table, schema=None) as batch_op:
            batch_op.alter_column(
                column,
                existing_type=sa.DateTime(timezone=True),
                type_=sa.DateTime(),
                existing_nullable=True,
                postgresql_using=f"{column} AT TIME ZONE 'UTC'",
            )
