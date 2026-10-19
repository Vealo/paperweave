"""Fixtures for tests that exercise the explicitly isolated Compose database."""

from collections.abc import Iterator
import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text

from paperweave.api.dependencies import SESSION_COOKIE
from paperweave.infrastructure.db.identity_repository import BOOTSTRAP_OWNER_ID
from paperweave.main import create_app

PROJECT_ROOT = Path(__file__).resolve().parents[1]
TEST_ORIGIN = "http://127.0.0.1:18742"
OWNER_EMAIL = "owner@example.test"
OWNER_PASSWORD = "test-owner-password-123"


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
        connection.execute(text("DELETE FROM sessions"))
        connection.execute(text("DELETE FROM projects"))
        connection.execute(
            text(
                "UPDATE users SET email='owner@local.invalid', "
                "display_name='PaperWeave owner setup', password_hash=NULL, role='owner' "
                "WHERE id=:id"
            ),
            {"id": BOOTSTRAP_OWNER_ID},
        )
    cleanup_engine.dispose()

    app = create_app(PROJECT_ROOT / "config.example.toml", database_url=database_url)
    with TestClient(app) as test_client:
        test_client.headers.update({"Origin": TEST_ORIGIN})
        response = test_client.post(
            "/api/v1/auth/bootstrap",
            json={"email": OWNER_EMAIL, "display_name": "Test Owner", "password": OWNER_PASSWORD},
        )
        assert response.status_code == 201
        assert SESSION_COOKIE in test_client.cookies
        yield test_client
