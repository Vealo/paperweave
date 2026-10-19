"""Fixtures for tests that exercise the explicitly isolated Compose database."""

from collections.abc import Iterator
import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text

from paperweave.main import create_app


PROJECT_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="session")
def database_url() -> str:
    value = os.getenv("TEST_DATABASE_URL")
    if not value:
        pytest.fail("TEST_DATABASE_URL is required; run tests through the isolated Compose profile")
    if "test-db" not in value:
        pytest.fail("TEST_DATABASE_URL must target the isolated Compose test-db service")
    return value


@pytest.fixture
def client(database_url: str) -> Iterator[TestClient]:
    cleanup_engine = create_engine(database_url)
    with cleanup_engine.begin() as connection:
        connection.execute(text("DELETE FROM projects"))
    cleanup_engine.dispose()

    app = create_app(PROJECT_ROOT / "config.example.toml", database_url=database_url)
    with TestClient(app) as test_client:
        yield test_client
