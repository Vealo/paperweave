from datetime import UTC, datetime

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, inspect, text

from paperweave.modules.identity.security import hash_session_token

from tests.conftest import OWNER_EMAIL, OWNER_PASSWORD, PROJECT_ROOT, TEST_ORIGIN
from paperweave.main import create_app


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


def test_cors_allows_only_the_configured_local_ui_origin(client: TestClient) -> None:
    allowed = client.options(
        "/api/v1/projects",
        headers={
            "Origin": TEST_ORIGIN,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )
    assert allowed.status_code == 200
    assert allowed.headers["access-control-allow-origin"] == TEST_ORIGIN
    assert allowed.headers["access-control-allow-credentials"] == "true"

    denied = client.options(
        "/api/v1/projects",
        headers={
            "Origin": "http://untrusted.example",
            "Access-Control-Request-Method": "POST",
        },
    )
    assert denied.status_code == 400


def test_authentication_owner_bootstrap_and_session_cookie(client: TestClient) -> None:
    assert client.get("/api/v1/auth/status").json() == {"owner_exists": True}
    current = client.get("/api/v1/auth/me")
    assert current.status_code == 200
    assert current.json()["email"] == OWNER_EMAIL
    assert current.json()["role"] == "owner"
    cookie = client.cookies.get("paperweave_session")
    assert cookie
    login = client.post(
        "/api/v1/auth/login",
        headers={"Origin": TEST_ORIGIN},
        json={"email": OWNER_EMAIL, "password": OWNER_PASSWORD},
    )
    assert login.status_code == 200
    set_cookie = login.headers["set-cookie"].lower()
    assert "httponly" in set_cookie
    assert "samesite=strict" in set_cookie
    assert "max-age=604800" in set_cookie
    assert client.post(
        "/api/v1/auth/bootstrap",
        headers={"Origin": TEST_ORIGIN},
        json={"email": "another@example.test", "display_name": "Other", "password": "test-password-123"},
    ).status_code == 409

    response = client.post("/api/v1/auth/logout", headers={"Origin": TEST_ORIGIN})
    assert response.status_code == 204
    assert client.get("/api/v1/auth/me").status_code == 401
    assert client.cookies.get("paperweave_session") is None


def test_project_routes_require_a_session_and_login_restores_it(client: TestClient) -> None:
    client.cookies.clear()
    assert client.get("/api/v1/projects").status_code == 401
    assert client.post(
        "/api/v1/projects", headers={"Origin": TEST_ORIGIN}, json={"name": "Private"}
    ).status_code == 401
    login = client.post(
        "/api/v1/auth/login",
        headers={"Origin": TEST_ORIGIN},
        json={"email": OWNER_EMAIL, "password": OWNER_PASSWORD},
    )
    assert login.status_code == 200
    assert client.get("/api/v1/projects").status_code == 200
    assert client.post(
        "/api/v1/auth/login",
        headers={"Origin": TEST_ORIGIN},
        json={"email": OWNER_EMAIL, "password": "wrong-password-123"},
    ).status_code == 401


def test_session_expires_after_twelve_hours_of_inactivity(client: TestClient, database_url: str) -> None:
    token = client.cookies.get("paperweave_session")
    assert token
    engine = create_engine(database_url)
    try:
        with engine.begin() as connection:
            connection.execute(
                text("UPDATE sessions SET last_activity_at=now() - interval '13 hours' WHERE token_hash=:hash"),
                {"hash": hash_session_token(token)},
            )
    finally:
        engine.dispose()
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401


def test_session_expires_after_seven_day_absolute_lifetime(client: TestClient, database_url: str) -> None:
    token = client.cookies.get("paperweave_session")
    assert token
    engine = create_engine(database_url)
    try:
        with engine.begin() as connection:
            connection.execute(
                text("UPDATE sessions SET expires_at=now() - interval '1 second' WHERE token_hash=:hash"),
                {"hash": hash_session_token(token)},
            )
    finally:
        engine.dispose()
    response = client.get("/api/v1/projects")
    assert response.status_code == 401
    assert response.json()["detail"] == "Session expired"


def test_owner_manages_users_and_project_access_is_isolated(client: TestClient, database_url: str) -> None:
    created = client.post(
        "/api/v1/auth/users",
        headers={"Origin": TEST_ORIGIN},
        json={
            "email": "member@example.test",
            "display_name": "Member",
            "password": "test-member-password-123",
        },
    )
    assert created.status_code == 201
    assert created.json()["role"] == "member"

    app = create_app(PROJECT_ROOT / "config.example.toml", database_url=database_url)
    with TestClient(app, base_url="http://127.0.0.1:18742") as member:
        member.headers.update({"Origin": TEST_ORIGIN})
        login = member.post(
            "/api/v1/auth/login",
            headers={"Origin": TEST_ORIGIN},
            json={"email": "member@example.test", "password": "test-member-password-123"},
        )
        assert login.status_code == 200
        assert member.post(
            "/api/v1/auth/users",
            headers={"Origin": TEST_ORIGIN},
            json={
                "email": "third@example.test",
                "display_name": "Third",
                "password": "test-third-password-123",
            },
        ).status_code == 403

        owner_project = client.post(
            "/api/v1/projects", json={"name": "Owner project", "description": "Private"}
        ).json()
        member_project_response = member.post("/api/v1/projects", json={"name": "Member project"})
        assert member_project_response.status_code == 201
        member_project = member_project_response.json()

        assert [item["id"] for item in client.get("/api/v1/projects").json()] == [owner_project["id"]]
        assert [item["id"] for item in member.get("/api/v1/projects").json()] == [member_project["id"]]
        assert member.get(f"/api/v1/projects/{owner_project['id']}").status_code == 404
        assert client.get(f"/api/v1/projects/{member_project['id']}").status_code == 404
        assert member.put(
            f"/api/v1/projects/{owner_project['id']}", json={"name": "stolen"}
        ).status_code == 404
        changed = client.put(
            f"/api/v1/projects/{owner_project['id']}",
            json={"name": "Updated project", "description": "Updated"},
        )
        assert changed.status_code == 200
        assert changed.json()["name"] == "Updated project"


def test_alembic_migration_created_the_expected_postgres_schema(database_url: str) -> None:
    engine = create_engine(database_url)
    try:
        inspector = inspect(engine)
        assert {"alembic_version", "projects", "users", "sessions"} <= set(inspector.get_table_names())
        columns = {column["name"]: column for column in inspector.get_columns("projects")}
        assert set(columns) == {"owner_id", "id", "name", "description", "created_at"}
        assert columns["owner_id"]["nullable"] is False
        assert columns["id"]["type"].__class__.__name__ == "UUID"
        assert columns["name"]["type"].length == 200
        assert columns["description"]["nullable"] is True
        assert columns["created_at"]["type"].timezone is True
        with engine.connect() as connection:
            revision = connection.execute(text("SELECT version_num FROM alembic_version")).scalar_one()
        assert revision == "20261019_0002"
    finally:
        engine.dispose()


def test_create_list_get_and_update_project_contract(client: TestClient) -> None:
    first_response = client.post(
        "/api/v1/projects", json={"name": "  First project  ", "description": "Notes"}
    )
    second_response = client.post("/api/v1/projects", json={"name": "First project"})

    assert first_response.status_code == 201
    assert second_response.status_code == 201
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
    changed = client.put(f"/api/v1/projects/{first['id']}", json={"name": "Renamed"})
    assert changed.status_code == 200
    assert changed.json()["name"] == "Renamed"


def test_create_validates_trimmed_name_and_description_length(client: TestClient) -> None:
    assert client.post("/api/v1/projects", json={"name": "  "}).status_code == 422
    assert client.post("/api/v1/projects", json={"name": "x" * 201}).status_code == 422
    assert client.post(
        "/api/v1/projects", json={"name": "Valid", "description": "x" * 5001}
    ).status_code == 422
    assert client.post("/api/v1/projects", json={"name": "Valid", "unknown": True}).status_code == 422
