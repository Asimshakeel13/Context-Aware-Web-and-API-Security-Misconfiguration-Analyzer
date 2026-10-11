"""Alembic migration environment.

Migrations run synchronously (psycopg2) even though the app is async -- this is
the standard, simplest setup. The database URL comes from, in order:

1. the ``ALEMBIC_SQLALCHEMY_URL`` env var (used for local SQLite verification), or
2. ``settings.sync_database_url`` (the real PostgreSQL, sync driver).

All models are imported via ``app.database.models`` so ``target_metadata`` sees
every table for autogenerate.
"""
from __future__ import annotations

import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

# Import the metadata with every model registered.
from app.config import settings
from app.database.models import Base  # noqa: F401  (registers all tables)

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def _database_url() -> str:
    return os.environ.get("ALEMBIC_SQLALCHEMY_URL") or settings.sync_database_url


def run_migrations_offline() -> None:
    """Emit SQL to the script output without a live DB connection."""
    context.configure(
        url=_database_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations against a live DB connection."""
    section = config.get_section(config.config_ini_section, {})
    section["sqlalchemy.url"] = _database_url()
    connectable = engine_from_config(
        section,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            render_as_batch=connection.dialect.name == "sqlite",
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
