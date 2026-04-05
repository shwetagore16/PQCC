"""
alembic/env.py — Async Alembic migration environment.
Supports both online (connected) and offline (SQL script) modes.
"""

from __future__ import annotations

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config

from app.core.config import get_settings

# ── Alembic config object ────────────────────────────────────────────────────
config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# ── Import ALL models so Alembic can auto-detect changes ─────────────────────
from app.db.base import Base  # noqa: E402 — must be after imports
from app.db.models import asset, tls_scan, cbom  # noqa: F401 — side-effect imports

target_metadata = Base.metadata

# ── Inject the DB URL from settings ─────────────────────────────────────────
settings = get_settings()
config.set_main_option("sqlalchemy.url", settings.SYNC_DATABASE_URL)


# ── Offline mode (generate SQL script) ──────────────────────────────────────

def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


# ── Online mode (connected, async) ───────────────────────────────────────────

def do_run_migrations(connection: Any) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


# ── Entry point ───────────────────────────────────────────────────────────────

from typing import Any  # noqa: E402

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
