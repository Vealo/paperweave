"""Database URL construction from validated application configuration."""

from sqlalchemy.engine import URL

from paperweave.config import AppConfig


def build_database_url(config: AppConfig) -> URL:
    database = config.database
    return URL.create(
        "postgresql+psycopg",
        username=database.user,
        password=database.password,
        host=database.host,
        port=database.port,
        database=database.name,
    )
