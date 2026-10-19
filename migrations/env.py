"""Alembic environment wired to the validated local TOML configuration."""

from __future__ import annotations

import os

from alembic import context
from sqlalchemy import engine_from_config, pool
from sqlalchemy.engine import URL

from paperweave.config import load_config


config = context.config
settings = load_config(os.getenv("PAPERWEAVE_CONFIG_FILE", "config.toml"))
database_url = URL.create(
    "postgresql+psycopg",
    username=settings.database.user,
    password=settings.database.password,
    host=settings.database.host,
    port=settings.database.port,
    database=settings.database.name,
)
config.set_main_option("sqlalchemy.url", database_url.render_as_string(hide_password=False).replace("%", "%%"))
target_metadata = None


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
