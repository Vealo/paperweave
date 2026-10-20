from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID, uuid4

from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import make_url

from paperweave.modules.identity.security import hash_session_token

from tests.conftest import OWNER_EMAIL, OWNER_PASSWORD, PROJECT_ROOT, TEST_ORIGIN
from paperweave.main import create_app


def test_live_and_ready_report_database_state(client: TestClient, database_url: str) -> None:
    assert client.get("/api/v1/health/live").status_code == 200
    ready = client.get("/api/v1/health/ready")
    assert ready.status_code == 200
    assert ready.json() == {"status": "ok", "database": "available", "storage": "available"}

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


def test_cors_preflight_allows_idempotency_key_for_uploads(client: TestClient) -> None:
    response = client.options(
        "/api/v1/auth/me/avatar",
        headers={
            "Origin": TEST_ORIGIN,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "idempotency-key, content-type",
        },
    )

    assert response.status_code == 200
    allowed_headers = response.headers.get("access-control-allow-headers", "").lower()
    assert "idempotency-key" in allowed_headers


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


def test_owner_manages_users_and_project_access_is_isolated(client: TestClient, database_url: str, tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("PW_FILE_STORAGE", str(tmp_path))
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
        private_source = client.post(
            f"/api/v1/projects/{owner_project['id']}/sources", json={"title": "Private source"}
        ).json()
        private_file = client.post(
            f"/api/v1/projects/{owner_project['id']}/sources/{private_source['id']}/files",
            files={"file": ("private.pdf", b"%PDF-1.7 private", "application/pdf")},
            headers={"Idempotency-Key": "private-pdf"},
        ).json()
        member_project_response = member.post("/api/v1/projects", json={"name": "Member project"})
        assert member_project_response.status_code == 201
        member_project = member_project_response.json()

        assert [item["id"] for item in client.get("/api/v1/projects").json()] == [owner_project["id"]]
        assert [item["id"] for item in member.get("/api/v1/projects").json()] == [member_project["id"]]
        assert member.get(f"/api/v1/projects/{owner_project['id']}").status_code == 404
        assert member.get(f"/api/v1/projects/{owner_project['id']}/sources").status_code == 404
        assert member.get(
            f"/api/v1/projects/{owner_project['id']}/sources/{private_source['id']}/files/{private_file['id']}"
        ).status_code == 404
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
        assert {"alembic_version", "projects", "users", "user_settings", "sessions", "file_artifacts", "manuscripts", "sources", "source_files", "source_file_references", "extraction_runs", "source_passages", "claims", "evidence_links", "review_decisions", "ai_proposals", "manuscript_revisions"} <= set(inspector.get_table_names())
        columns = {column["name"]: column for column in inspector.get_columns("projects")}
        assert set(columns) == {"owner_id", "id", "name", "description", "created_at"}
        assert columns["owner_id"]["nullable"] is False
        assert columns["id"]["type"].__class__.__name__ == "UUID"
        assert columns["name"]["type"].length == 200
        assert columns["description"]["nullable"] is True
        assert columns["created_at"]["type"].timezone is True
        reference_columns = {column["name"] for column in inspector.get_columns("source_file_references")}
        assert "review_state" in reference_columns
        extraction_columns = {column["name"] for column in inspector.get_columns("extraction_runs")}
        assert {"file_id", "processor", "processor_version", "status", "page_count", "error"} <= extraction_columns
        passage_columns = {column["name"] for column in inspector.get_columns("source_passages")}
        assert {"run_id", "file_id", "page_number", "text"} <= passage_columns
        with engine.connect() as connection:
            revision = connection.execute(text("SELECT version_num FROM alembic_version")).scalar_one()
        assert revision == "20261020_0011"
        user_settings_columns = {
            column["name"]: column for column in inspector.get_columns("user_settings")
        }
        assert user_settings_columns["theme"]["default"].startswith("'light'")
        assert any(
            constraint["name"] == "ck_user_settings_theme_light"
            for constraint in inspector.get_check_constraints("user_settings")
        )
        assert {"manuscript_id", "block_position", "text", "version", "manuscript_version"} <= {column["name"] for column in inspector.get_columns("claims")}
        assert {"claim_id", "claim_version", "passage_id", "passage_file_id", "relation", "review_state", "manuscript_version", "version"} <= {column["name"] for column in inspector.get_columns("evidence_links")}
        assert {"reviewer_id", "link_version", "decision", "note", "decided_at"} <= {column["name"] for column in inspector.get_columns("review_decisions")}
    finally:
        engine.dispose()


def test_user_settings_migration_backfills_existing_accounts(
    database_url: str, monkeypatch
) -> None:
    schema = f"migration_{uuid4().hex}"
    admin_engine = create_engine(database_url)
    schema_url = make_url(database_url).update_query_dict(
        {"options": f"-csearch_path={schema}"}
    )
    try:
        with admin_engine.begin() as connection:
            connection.execute(text(f'CREATE SCHEMA "{schema}"'))

        monkeypatch.setenv("TEST_DATABASE_URL", schema_url.render_as_string(hide_password=False))
        monkeypatch.setenv("PAPERWEAVE_CONFIG_FILE", str(PROJECT_ROOT / "config.example.toml"))
        alembic_config = Config(str(PROJECT_ROOT / "alembic.ini"))
        command.upgrade(alembic_config, "20261020_0008")

        existing_user_ids = [
            "00000000-0000-0000-0000-000000000987",
            "00000000-0000-0000-0000-000000000988",
            "00000000-0000-0000-0000-000000000989",
        ]
        with create_engine(schema_url).begin() as connection:
            for index, user_id in enumerate(existing_user_ids):
                connection.execute(
                    text(
                        "INSERT INTO users (id, email, display_name, password_hash, role) "
                        "VALUES (:id, :email, :name, :password_hash, 'member')"
                    ),
                    {
                        "id": user_id,
                        "email": f"existing-{index}@example.test",
                        "name": f"Existing User {index}",
                        "password_hash": f"hash-{index}",
                    },
                )

        command.upgrade(alembic_config, "20261020_0010")
        with create_engine(schema_url).begin() as connection:
            connection.execute(
                text("UPDATE user_settings SET theme=:theme WHERE user_id=:user_id"),
                [
                    {"user_id": existing_user_ids[0], "theme": "system"},
                    {"user_id": existing_user_ids[1], "theme": "dark"},
                    {"user_id": existing_user_ids[2], "theme": "light"},
                ],
            )

        command.upgrade(alembic_config, "head")
        with create_engine(schema_url).connect() as connection:
            settings = connection.execute(
                text(
                    "SELECT user_id, theme FROM user_settings "
                    "WHERE user_id IN (:owner, :user_1, :user_2, :user_3) ORDER BY user_id"
                ),
                {
                    "owner": "00000000-0000-0000-0000-000000000001",
                    "user_1": existing_user_ids[0],
                    "user_2": existing_user_ids[1],
                    "user_3": existing_user_ids[2],
                },
            ).all()
            users = connection.execute(
                text(
                    "SELECT email, display_name, password_hash, role, is_active FROM users "
                    "WHERE email LIKE 'existing-%' ORDER BY email"
                )
            ).all()
            revision = connection.execute(
                text("SELECT version_num FROM alembic_version")
            ).scalar_one()
        assert revision == "20261020_0011"
        assert [(row.user_id, row.theme) for row in settings] == sorted(
            [(UUID("00000000-0000-0000-0000-000000000001"), "light")]
            + [(UUID(user_id), "light") for user_id in existing_user_ids]
        )
        assert [(row.email, row.display_name, row.password_hash, row.role, row.is_active) for row in users] == [
            (f"existing-{index}@example.test", f"Existing User {index}", f"hash-{index}", "member", True)
            for index in range(3)
        ]

        command.downgrade(alembic_config, "20261020_0010")
        with create_engine(schema_url).connect() as connection:
            downgraded_revision = connection.execute(
                text("SELECT version_num FROM alembic_version")
            ).scalar_one()
            downgraded_themes = connection.execute(
                text("SELECT user_id, theme FROM user_settings ORDER BY user_id")
            ).all()
        assert downgraded_revision == "20261020_0010"
        assert all(row.theme == "light" for row in downgraded_themes)

        command.upgrade(alembic_config, "head")

        with create_engine(schema_url).begin() as connection:
            new_user_id = "00000000-0000-0000-0000-000000000990"
            connection.execute(
                text("INSERT INTO users (id, email, display_name, role) VALUES (:id, 'new@example.test', 'New User', 'member')"),
                {"id": new_user_id},
            )
            connection.execute(
                text("INSERT INTO user_settings (user_id) VALUES (:id)"),
                {"id": new_user_id},
            )
            default_theme = connection.execute(
                text("SELECT theme FROM user_settings WHERE user_id=:id"),
                {"id": new_user_id},
            ).scalar_one()
        assert default_theme == "light"
    finally:
        with admin_engine.begin() as connection:
            connection.execute(text(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE'))
        admin_engine.dispose()


def test_file_artifact_migration_backfills_existing_files_and_avatars(
    database_url: str, monkeypatch
) -> None:
    schema = f"artifact_migration_{uuid4().hex}"
    admin_engine = create_engine(database_url)
    schema_url = make_url(database_url).update_query_dict(
        {"options": f"-csearch_path={schema}"}
    )
    user_id, project_id, source_id, file_id = (str(uuid4()) for _ in range(4))
    try:
        with admin_engine.begin() as connection:
            connection.execute(text(f'CREATE SCHEMA "{schema}"'))

        monkeypatch.setenv("TEST_DATABASE_URL", schema_url.render_as_string(hide_password=False))
        monkeypatch.setenv("PAPERWEAVE_CONFIG_FILE", str(PROJECT_ROOT / "config.example.toml"))
        alembic_config = Config(str(PROJECT_ROOT / "alembic.ini"))
        command.upgrade(alembic_config, "20261020_0009")

        with create_engine(schema_url).begin() as connection:
            connection.execute(
                text(
                    "INSERT INTO users (id, email, display_name, role, avatar_key, avatar_media_type) "
                    "VALUES (:id, 'legacy@example.test', 'Legacy', 'member', 'avatars/legacy.png', 'image/png')"
                ),
                {"id": user_id},
            )
            connection.execute(
                text("INSERT INTO projects (id, owner_id, name) VALUES (:id, :owner, 'Legacy project')"),
                {"id": project_id, "owner": user_id},
            )
            connection.execute(
                text(
                    "INSERT INTO sources (id, project_id, title, metadata_provenance) "
                    "VALUES (:id, :project, 'Legacy source', 'manual')"
                ),
                {"id": source_id, "project": project_id},
            )
            connection.execute(
                text(
                    "INSERT INTO source_files "
                    "(id, source_id, version, original_name, media_type, size_bytes, sha256, storage_key) "
                    "VALUES (:id, :source, 3, 'paper.pdf', 'application/pdf', 1234, :sha, 'sources/legacy.pdf')"
                ),
                {"id": file_id, "source": source_id, "sha": "a" * 64},
            )

        command.upgrade(alembic_config, "head")
        with create_engine(schema_url).connect() as connection:
            file_artifact = connection.execute(
                text(
                    "SELECT owner_user_id, kind, domain_id, domain_parent_id, backend, object_key, "
                    "original_name, media_type, size_bytes, checksum_sha256, version "
                    "FROM file_artifacts WHERE id=:id"
                ),
                {"id": file_id},
            ).one()
            avatar = connection.execute(
                text(
                    "SELECT id, owner_user_id, object_key, media_type FROM file_artifacts "
                    "WHERE kind='avatar' AND domain_id=:user_id"
                ),
                {"user_id": user_id},
            ).one()
            source_artifact_id = connection.execute(
                text("SELECT artifact_id FROM source_files WHERE id=:id"), {"id": file_id}
            ).scalar_one()
            avatar_pointer = connection.execute(
                text("SELECT avatar_artifact_id FROM users WHERE id=:id"), {"id": user_id}
            ).scalar_one()

        assert str(file_artifact.owner_user_id) == user_id
        assert file_artifact.kind == "document"
        assert str(file_artifact.domain_id) == file_id
        assert str(file_artifact.domain_parent_id) == source_id
        assert file_artifact.backend == "local"
        assert file_artifact.object_key == "sources/legacy.pdf"
        assert file_artifact.original_name == "paper.pdf"
        assert file_artifact.media_type == "application/pdf"
        assert file_artifact.size_bytes == 1234
        assert file_artifact.checksum_sha256 == "a" * 64
        assert file_artifact.version == 3
        assert str(source_artifact_id) == file_id
        assert str(avatar.owner_user_id) == user_id
        assert avatar.object_key == "avatars/legacy.png"
        assert avatar.media_type == "image/png"
        assert avatar_pointer == avatar.id
    finally:
        with admin_engine.begin() as connection:
            connection.execute(text(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE'))
        admin_engine.dispose()


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
