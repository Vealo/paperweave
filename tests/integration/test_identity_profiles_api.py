"""Integration coverage for profile CRUD, access control and user settings."""

from collections.abc import Iterator
from contextlib import contextmanager
from uuid import UUID

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text

from paperweave.api.dependencies import SESSION_COOKIE
from paperweave.main import create_app
from tests.conftest import OWNER_EMAIL, OWNER_PASSWORD, PROJECT_ROOT, TEST_ORIGIN


MEMBER_EMAIL = "member-profile@example.test"
MEMBER_PASSWORD = "test-member-profile-password-123"


@contextmanager
def _new_client(database_url: str) -> Iterator[TestClient]:
    app = create_app(PROJECT_ROOT / "config.example.toml", database_url=database_url)
    with TestClient(app, base_url=TEST_ORIGIN) as client:
        client.headers.update({"Origin": TEST_ORIGIN})
        yield client


def _create_member(client: TestClient, *, email: str = MEMBER_EMAIL) -> dict:
    response = client.post(
        "/api/v1/auth/users",
        json={
            "email": email,
            "display_name": "Profile Member",
            "password": MEMBER_PASSWORD,
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def _login(client: TestClient, email: str, password: str) -> dict:
    response = client.post(
        "/api/v1/auth/login", json={"email": email, "password": password}
    )
    assert response.status_code == 200, response.text
    return response.json()


def test_profile_read_update_and_email_requires_current_password(client: TestClient) -> None:
    current = client.get("/api/v1/auth/me")
    assert current.status_code == 200
    original = current.json()

    renamed = client.patch("/api/v1/auth/me", json={"display_name": "Updated Owner"})
    assert renamed.status_code == 200, renamed.text
    assert renamed.json()["display_name"] == "Updated Owner"
    assert renamed.json()["email"] == original["email"]

    no_reauthentication = client.patch(
        "/api/v1/auth/me", json={"email": "updated-owner@example.test"}
    )
    assert no_reauthentication.status_code == 403

    wrong_password = client.patch(
        "/api/v1/auth/me",
        json={"email": "updated-owner@example.test", "current_password": "incorrect"},
    )
    assert wrong_password.status_code == 403

    updated = client.patch(
        "/api/v1/auth/me",
        json={
            "email": " UPDATED-OWNER@example.test ",
            "current_password": OWNER_PASSWORD,
        },
    )
    assert updated.status_code == 200, updated.text
    assert updated.json()["email"] == "updated-owner@example.test"
    assert client.get("/api/v1/auth/me").json()["id"] == original["id"]


def test_password_change_requires_old_password_and_revokes_all_sessions(
    client: TestClient, database_url: str
) -> None:
    with _new_client(database_url) as second_owner_session:
        _login(second_owner_session, OWNER_EMAIL, OWNER_PASSWORD)

        rejected = client.post(
            "/api/v1/auth/me/password",
            json={"current_password": "incorrect", "new_password": "new-owner-password-123"},
        )
        assert rejected.status_code == 403
        assert second_owner_session.get("/api/v1/auth/me").status_code == 200

        changed = client.post(
            "/api/v1/auth/me/password",
            json={
                "current_password": OWNER_PASSWORD,
                "new_password": "new-owner-password-123",
            },
        )
        assert changed.status_code == 204
        assert client.cookies.get(SESSION_COOKIE) is None
        assert second_owner_session.get("/api/v1/auth/me").status_code == 401

        assert client.post(
            "/api/v1/auth/login",
            json={"email": OWNER_EMAIL, "password": OWNER_PASSWORD},
        ).status_code == 401
        assert client.post(
            "/api/v1/auth/login",
            json={"email": OWNER_EMAIL, "password": "new-owner-password-123"},
        ).status_code == 200


def test_owner_manages_member_profiles_and_deactivation_preserves_data(
    client: TestClient, database_url: str
) -> None:
    member = _create_member(client)
    user_url = f"/api/v1/auth/users/{member['id']}"
    assert client.get("/api/v1/auth/users").status_code == 200
    assert client.get(user_url).json()["id"] == member["id"]

    changed = client.patch(
        user_url,
        json={"display_name": "Edited Member", "email": "edited-member@example.test"},
    )
    assert changed.status_code == 200, changed.text
    assert changed.json()["display_name"] == "Edited Member"
    assert changed.json()["email"] == "edited-member@example.test"
    assert changed.json()["role"] == "member"

    assert client.delete(
        f"/api/v1/auth/users/{client.get('/api/v1/auth/me').json()['id']}"
    ).status_code == 403

    with _new_client(database_url) as member_client:
        _login(member_client, "edited-member@example.test", MEMBER_PASSWORD)
        assert member_client.get("/api/v1/auth/users").status_code == 403
        project = member_client.post(
            "/api/v1/projects", json={"name": "Preserved member project"}
        )
        assert project.status_code == 201, project.text
        project_id = project.json()["id"]

        deactivated = client.delete(user_url)
        assert deactivated.status_code == 200, deactivated.text
        assert deactivated.json()["is_active"] is False
        assert member_client.get("/api/v1/auth/me").status_code == 401
        with create_engine(database_url).connect() as connection:
            assert connection.execute(
                text("SELECT owner_id FROM projects WHERE id=:project_id"),
                {"project_id": UUID(project_id)},
            ).scalar_one() == UUID(member["id"])
            assert connection.execute(
                text("SELECT count(*) FROM sessions WHERE user_id=:user_id"),
                {"user_id": UUID(member["id"])},
            ).scalar_one() == 0
            assert connection.execute(
                text("SELECT is_active FROM users WHERE id=:user_id"),
                {"user_id": UUID(member["id"])},
            ).scalar_one() is False
            assert connection.execute(
                text("SELECT theme FROM user_settings WHERE user_id=:user_id"),
                {"user_id": UUID(member["id"])},
            ).scalar_one() == "system"

        reactivated = client.patch(user_url, json={"is_active": True})
        assert reactivated.status_code == 200, reactivated.text
        assert reactivated.json()["is_active"] is True
        assert member_client.post(
            "/api/v1/auth/login",
            json={"email": "edited-member@example.test", "password": MEMBER_PASSWORD},
        ).status_code == 200


def test_inactive_account_rejects_a_stale_session_on_protected_routes(
    client: TestClient, database_url: str
) -> None:
    member = _create_member(client)
    with _new_client(database_url) as member_client:
        _login(member_client, member["email"], MEMBER_PASSWORD)

        # Keep the session row to exercise the defensive resolver check used by
        # every protected API route, independently of the normal revoke flow.
        with create_engine(database_url).begin() as connection:
            connection.execute(
                text("UPDATE users SET is_active=false WHERE id=:user_id"),
                {"user_id": UUID(member["id"])},
            )

        assert member_client.get("/api/v1/auth/me").status_code == 401
        assert member_client.get("/api/v1/projects").status_code == 401
        with create_engine(database_url).connect() as connection:
            assert connection.execute(
                text("SELECT count(*) FROM sessions WHERE user_id=:user_id"),
                {"user_id": UUID(member["id"])},
            ).scalar_one() == 0


def test_user_settings_have_defaults_and_are_isolated(
    client: TestClient, database_url: str
) -> None:
    member = _create_member(client)
    with _new_client(database_url) as member_client:
        _login(member_client, member["email"], MEMBER_PASSWORD)
        member_settings = member_client.get("/api/v1/auth/me/settings")
        assert member_settings.status_code == 200, member_settings.text
        assert member_settings.json() == {"user_id": member["id"], "theme": "system"}

        owner_settings_before = client.get("/api/v1/auth/me/settings")
        assert owner_settings_before.status_code == 200, owner_settings_before.text
        owner_theme_before = owner_settings_before.json()["theme"]

        updated = member_client.patch(
            "/api/v1/auth/me/settings", json={"theme": "dark"}
        )
        assert updated.status_code == 200, updated.text
        assert updated.json()["theme"] == "dark"
        assert client.get("/api/v1/auth/me/settings").json()["theme"] == owner_theme_before

        with create_engine(database_url).connect() as connection:
            rows = connection.execute(
                text("SELECT user_id, theme FROM user_settings WHERE user_id IN (:owner, :member)"),
                {
                    "owner": UUID(client.get("/api/v1/auth/me").json()["id"]),
                    "member": UUID(member["id"]),
                },
            ).all()
        assert {row.user_id: row.theme for row in rows}[UUID(member["id"])] == "dark"
