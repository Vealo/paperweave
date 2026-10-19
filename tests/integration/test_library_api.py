"""Project-scoped manual bibliography and PDF version tests."""
from pathlib import Path
from uuid import uuid4
from fastapi.testclient import TestClient
from paperweave.infrastructure.db.models import SourceFileReferenceRecord


def _project(client: TestClient) -> str:
    response = client.post("/api/v1/projects", json={"name": "Library project"})
    assert response.status_code == 201
    return response.json()["id"]


def test_manual_source_pdf_version_and_duplicate_rules(client: TestClient, tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("PW_FILE_STORAGE", str(tmp_path))
    project_id = _project(client)
    endpoint = f"/api/v1/projects/{project_id}/sources"
    created = client.post(endpoint, json={"title": "A paper", "authors": "A. Author", "year": 2024, "doi": "https://doi.org/10.1234/ABC"})
    assert created.status_code == 201
    source = created.json()
    assert source["metadata_provenance"] == "manual"
    assert source["doi"] == "10.1234/abc"
    duplicate = client.post(endpoint, json={"title": "Another title", "doi": "10.1234/abc"})
    assert duplicate.status_code == 409
    assert duplicate.json()["detail"]["existing_source_id"] == source["id"]
    duplicate_without_doi = client.post(endpoint, json={"title": " A PAPER ", "authors": "a. author", "year": 2024})
    assert duplicate_without_doi.status_code == 409
    assert duplicate_without_doi.json()["detail"]["existing_source_id"] == source["id"]

    pdf = b"%PDF-1.7\nminimal"
    uploaded = client.post(f"{endpoint}/{source['id']}/files", files={"file": ("../paper.pdf", pdf, "application/pdf")})
    assert uploaded.status_code == 201
    assert uploaded.json()["version"] == 1
    assert uploaded.json()["original_name"] == "paper.pdf"
    listed = client.get(endpoint).json()
    assert listed[0]["files"][0]["id"] == uploaded.json()["id"]
    repeated = client.post(f"{endpoint}/{source['id']}/files", files={"file": ("same.pdf", pdf, "application/pdf")})
    assert repeated.status_code == 409
    download = client.get(f"{endpoint}/{source['id']}/files/{uploaded.json()['id']}")
    assert download.status_code == 200
    assert download.content == pdf
    with client.app.state.session_factory() as session:
        reference = SourceFileReferenceRecord(file_id=uploaded.json()["id"], reference_type="passage", reference_id=uuid4())
        session.add(reference)
        session.commit()
    file_url = f"{endpoint}/{source['id']}/files/{uploaded.json()['id']}"
    assert client.delete(file_url + "?confirmed=false").status_code == 400
    assert client.delete(file_url + "?confirmed=true").status_code == 409
    with client.app.state.session_factory() as session:
        session.delete(session.get(SourceFileReferenceRecord, reference.id))
        session.commit()
    assert client.delete(file_url + "?confirmed=true").status_code == 204


def test_pdf_upload_rejects_mime_signature_and_size(client: TestClient, tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("PW_FILE_STORAGE", str(tmp_path))
    project_id = _project(client)
    endpoint = f"/api/v1/projects/{project_id}/sources"
    source = client.post(endpoint, json={"title": "Source"}).json()
    invalid = client.post(f"{endpoint}/{source['id']}/files", files={"file": ("bad.pdf", b"not a pdf", "application/pdf")})
    assert invalid.status_code == 415
    too_large = client.post(f"{endpoint}/{source['id']}/files", files={"file": ("large.pdf", b"%PDF-" + b"x" * (25 * 1024 * 1024), "application/pdf")})
    assert too_large.status_code == 413
