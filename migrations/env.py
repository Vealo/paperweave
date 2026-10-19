"""Alembic environment wired to the validated local TOML configuration."""

from __future__ import annotations

import os

from alembic import context
from sqlalchemy import engine_from_config, pool
from sqlalchemy.engine import URL

from paperweave.config import load_config
from paperweave.infrastructure.db.base import Base
from paperweave.infrastructure.db.connection import build_database_url
from paperweave.infrastructure.db import models  # noqa: F401


config = context.config
settings = load_config(os.getenv("PAPERWEAVE_CONFIG_FILE", "config.toml"))
database_url = os.getenv("TEST_DATABASE_URL") or build_database_url(settings)
rendered_database_url = (
    database_url.render_as_string(hide_password=False)
    if isinstance(database_url, URL)
    else database_url
)
config.set_main_option("sqlalchemy.url", rendered_database_url.replace("%", "%%"))
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata, compare_type=True)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
