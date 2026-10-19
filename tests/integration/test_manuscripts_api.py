"""Owner-scoped versioned manuscript persistence tests."""

from io import BytesIO
from zipfile import ZipFile

from fastapi.testclient import TestClient

from tests.conftest import PROJECT_ROOT
from paperweave.main import create_app


def _new_project(client: TestClient, name: str = "Manuscript project") -> str:
    response = client.post("/api/v1/projects", json={"name": name})
    assert response.status_code == 201
    return response.json()["id"]


def test_manuscript_create_round_trip_and_optimistic_version(client: TestClient) -> None:
    project_id = _new_project(client)
    content = {
        "type": "doc",
        "content": [
            {"type": "heading", "attrs": {"level": 2}, "content": [{"type": "text", "text": "Introduction"}]},
            {"type": "paragraph", "content": [{"type": "text", "text": "First block"}]},
        ],
    }
    endpoint = f"/api/v1/projects/{project_id}/manuscript"

    created = client.post(endpoint, json={"content": content})
    assert created.status_code == 201
    assert created.json()["content"] == content
    assert created.json()["version"] == 1

    replacement = {"type": "doc", "content": [{"type": "paragraph", "content": [{"type": "text", "text": "New version"}]}]}
    updated = client.put(endpoint, json={"content": replacement, "expected_version": 1})
    assert updated.status_code == 200
    assert updated.json()["content"] == replacement
    assert updated.json()["version"] == 2

    stale = client.put(endpoint, json={"content": content, "expected_version": 1})
    assert stale.status_code == 409
    assert "current version is 2" in stale.json()["detail"]
    fetched = client.get(endpoint)
    assert fetched.json()["version"] == 2
    assert fetched.json()["content"] == replacement
    assert client.post(endpoint, json={"content": content}).status_code == 409


def test_manuscript_requires_auth_and_is_hidden_for_unknown_or_foreign_project(
    client: TestClient, database_url: str
) -> None:
    project_id = _new_project(client)
    endpoint = f"/api/v1/projects/{project_id}/manuscript"
    token = client.cookies.get("paperweave_session")
    client.cookies.clear()
    assert client.get(endpoint).status_code == 401
    assert client.get(endpoint + "/export.docx").status_code == 401
    assert token
    client.cookies.set("paperweave_session", token)
    assert client.get(f"/api/v1/projects/00000000-0000-0000-0000-000000000099/manuscript").status_code == 404

    member = client.post(
        "/api/v1/auth/users",
        json={"email": "writer@example.test", "display_name": "Writer", "password": "test-writer-password-123"},
    )
    assert member.status_code == 201
    other_app = create_app(PROJECT_ROOT / "config.example.toml", database_url=database_url)
    with TestClient(other_app, base_url="http://127.0.0.1:18742") as other:
        other.headers.update({"Origin": "http://127.0.0.1:18742"})
        assert other.post(
            "/api/v1/auth/login",
            json={"email": "writer@example.test", "password": "test-writer-password-123"},
        ).status_code == 200
        assert other.get(endpoint).status_code == 404
        assert other.get(endpoint + "/export.docx").status_code == 404


def test_manuscript_survives_application_restart(client: TestClient, database_url: str) -> None:
    project_id = _new_project(client, "Restart project")
    endpoint = f"/api/v1/projects/{project_id}/manuscript"
    content = {"type": "doc", "content": [{"type": "paragraph", "content": [{"type": "text", "text": "Persisted"}]}]}
    created = client.post(endpoint, json={"content": content})
    assert created.status_code == 201
    token = client.cookies.get("paperweave_session")
    assert token

    restarted_app = create_app(PROJECT_ROOT / "config.example.toml", database_url=database_url)
    with TestClient(restarted_app, base_url="http://127.0.0.1:18742") as restarted:
        restarted.headers.update({"Origin": "http://127.0.0.1:18742"})
        restarted.cookies.set("paperweave_session", token)
        response = restarted.get(endpoint)
    assert response.status_code == 200
    assert response.json()["content"] == content
    assert response.json()["version"] == 1


def test_docx_export_resolves_citations_and_does_not_create_revision(client: TestClient) -> None:
    project_id = _new_project(client, "DOCX project")
    source_response = client.post(f"/api/v1/projects/{project_id}/sources", json={"title": "A curated source"})
    assert source_response.status_code == 201
    source_id = source_response.json()["id"]
    content = {"type": "doc", "content": [{"type": "heading", "attrs": {"level": 2}, "content": [{"type": "text", "text": "Results"}]}, {"type": "paragraph", "content": [{"type": "text", "text": "Finding "}, {"type": "citation", "attrs": {"sourceId": source_id}}, {"type": "text", "text": " confirmed by "}, {"type": "citation", "attrs": {"sourceId": source_id}}]}]}
    manuscript_url = f"/api/v1/projects/{project_id}/manuscript"
    saved = client.post(manuscript_url, json={"content": content})
    assert saved.status_code == 201

    response = client.get(manuscript_url + "/export.docx")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/vnd.openxmlformats-officedocument.wordprocessingml.document")
    with ZipFile(BytesIO(response.content)) as archive:
        assert {"[Content_Types].xml", "word/document.xml", "word/styles.xml"} <= set(archive.namelist())
        xml = archive.read("word/document.xml").decode()
    assert "Finding " in xml and "[1]" in xml
    assert "Список литературы" in xml and "Автор не указан. A curated source. год не указан." in xml
    assert "DOI не указан" in xml
    assert xml.count("Список литературы") == 1 and xml.count("A curated source") == 1
    assert client.get(manuscript_url).json()["version"] == 1
    assert len(client.get(manuscript_url + "/versions").json()) == 1


def test_docx_export_rejects_missing_citation_source(client: TestClient) -> None:
    project_id = _new_project(client, "Invalid citation project")
    content = {"type": "doc", "content": [{"type": "paragraph", "content": [{"type": "citation", "attrs": {"sourceId": "00000000-0000-0000-0000-000000000099"}}]}]}
    manuscript_url = f"/api/v1/projects/{project_id}/manuscript"
    assert client.post(manuscript_url, json={"content": content}).status_code == 201
    response = client.get(manuscript_url + "/export.docx")
    assert response.status_code == 422
    assert "not available in this project" in response.json()["detail"]
