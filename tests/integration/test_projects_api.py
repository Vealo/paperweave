from datetime import UTC, datetime

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, inspect, text


def test_live_and_ready_report_database_state(client: TestClient, database_url: str) -> None:
    assert client.get("/api/v1/health/live").status_code == 200
    ready = client.get("/api/v1/health/ready")
    assert ready.status_code == 200
    assert ready.json() == {"status": "ok", "database": "available"}

    unavailable_engine = create_engine(
        database_url.replace("test-db:5432", "127.0.0.1:1"),
        connect_args={"connect_timeout": 1},
    )
    original_engine = client.app.state.engine
    client.app.state.engine = unavailable_engine
    try:
        assert client.get("/api/v1/health/live").status_code == 200
        unavailable = client.get("/api/v1/health/ready")
        assert unavailable.status_code == 503
        assert unavailable.json() == {"status": "not_ready", "database": "unavailable"}
    finally:
        client.app.state.engine = original_engine
        unavailable_engine.dispose()


def test_alembic_migration_created_the_expected_postgres_schema(database_url: str) -> None:
    engine = create_engine(database_url)
    try:
        inspector = inspect(engine)
        assert "alembic_version" in inspector.get_table_names()
        assert "projects" in inspector.get_table_names()
        columns = {column["name"]: column for column in inspector.get_columns("projects")}
        assert set(columns) == {"id", "name", "description", "created_at"}
        assert columns["id"]["type"].__class__.__name__ == "UUID"
        assert columns["name"]["type"].length == 200
        assert columns["description"]["nullable"] is True
        assert columns["created_at"]["type"].timezone is True
        with engine.connect() as connection:
            revision = connection.execute(text("SELECT version_num FROM alembic_version")).scalar_one()
        assert revision == "20261019_0001"
    finally:
        engine.dispose()


def test_create_list_and_get_project_contract(client: TestClient) -> None:
    first_response = client.post(
        "/api/v1/projects", json={"name": "  First project  ", "description": "Notes"}
    )
    second_response = client.post("/api/v1/projects", json={"name": "First project"})

    assert first_response.status_code == 201
    assert second_response.status_code == 201  # Duplicate names are allowed.
    first = first_response.json()
    second = second_response.json()
    assert first["name"] == "First project"
    assert first["description"] == "Notes"
    assert first["id"] != second["id"]
    assert datetime.fromisoformat(first["created_at"].replace("Z", "+00:00")).utcoffset() == UTC.utcoffset(None)

    listed = client.get("/api/v1/projects")
    assert listed.status_code == 200
    assert [item["id"] for item in listed.json()] == [second["id"], first["id"]]

    detail = client.get(f"/api/v1/projects/{first['id']}")
    assert detail.status_code == 200
    assert detail.json() == first
    assert client.get("/api/v1/projects/00000000-0000-0000-0000-000000000099").status_code == 404
    assert client.get("/api/v1/projects/not-a-uuid").status_code == 422


def test_create_validates_trimmed_name_and_description_length(client: TestClient) -> None:
    assert client.post("/api/v1/projects", json={"name": "  "}).status_code == 422
    assert client.post("/api/v1/projects", json={"name": "x" * 201}).status_code == 422
    assert client.post(
        "/api/v1/projects", json={"name": "Valid", "description": "x" * 5001}
    ).status_code == 422
    assert client.post("/api/v1/projects", json={"name": "Valid", "unknown": True}).status_code == 422
