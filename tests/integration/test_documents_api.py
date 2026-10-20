"""Local PDF extraction provenance and retry behavior."""
from io import BytesIO
from pathlib import Path
from uuid import uuid4

from fastapi.testclient import TestClient
from pypdf import PdfWriter


def _project_source_file(client: TestClient, tmp_path: Path, monkeypatch, pdf: bytes):
    monkeypatch.setenv("PW_FILE_STORAGE", str(tmp_path))
    project = client.post("/api/v1/projects", json={"name": "Documents project"}).json()
    root = f"/api/v1/projects/{project['id']}/sources"
    source = client.post(root, json={"title": "A paper"}).json()
    uploaded = client.post(f"{root}/{source['id']}/files",
                           files={"file": ("paper.pdf", pdf, "application/pdf")},
                           headers={"Idempotency-Key": f"documents-original-{uuid4()}"})
    assert uploaded.status_code == 201
    base = f"{root}/{source['id']}/files/{uploaded.json()['id']}"
    return project, source, uploaded.json(), base


def _pdf_with_text(text: str | None = "Extracted passage for human review") -> bytes:
    writer = PdfWriter()
    page = writer.add_blank_page(width=300, height=300)
    if text:
        from pypdf.generic import DecodedStreamObject, NameObject
        # A compact text stream is enough to exercise the parser without OCR fixtures.
        stream = DecodedStreamObject()
        escaped = text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
        stream.set_data(f"BT /F1 12 Tf 40 100 Td ({escaped}) Tj ET".encode())
        page[NameObject("/Contents")] = writer._add_object(stream)
        from pypdf.generic import DictionaryObject, NameObject as N
        resources = DictionaryObject()
        font = DictionaryObject({N("/Type"): N("/Font"), N("/Subtype"): N("/Type1"), N("/BaseFont"): N("/Helvetica")})
        resources[N("/Font")] = DictionaryObject({N("/F1"): writer._add_object(font)})
        page[N("/Resources")] = writer._add_object(resources)
    output = BytesIO()
    writer.write(output)
    return output.getvalue()


def test_extraction_persists_provenance_and_explicit_retry(client: TestClient, tmp_path: Path, monkeypatch) -> None:
    project, source, file, endpoint = _project_source_file(client, tmp_path, monkeypatch, _pdf_with_text())
    first = client.post(f"{endpoint}/extractions")
    assert first.status_code == 201
    assert first.json()["status"] == "complete"
    assert first.json()["processor"] == "pypdf-text-layer"
    assert first.json()["processor_version"]
    assert first.json()["file_id"] == file["id"]
    passages = client.get(f"{endpoint}/passages").json()
    assert len(passages) == 1
    assert passages[0]["file_id"] == file["id"]
    assert passages[0]["run_id"] == first.json()["id"]
    assert passages[0]["page_number"] == 1
    assert passages[0]["review_state"] == "unreviewed"
    assert "Extracted passage" in passages[0]["text"]

    second = client.post(f"{endpoint}/extractions")
    assert second.status_code == 201
    assert second.json()["id"] != first.json()["id"]
    runs = client.get(f"{endpoint}/extractions").json()
    assert [run["id"] for run in runs] == [second.json()["id"], first.json()["id"]]
    assert len(client.get(f"{endpoint}/passages").json()) == 2


def test_empty_and_malformed_pdfs_are_not_verified_evidence(client: TestClient, tmp_path: Path, monkeypatch) -> None:
    _, _, _, empty_endpoint = _project_source_file(client, tmp_path, monkeypatch, _pdf_with_text(None))
    empty = client.post(f"{empty_endpoint}/extractions")
    assert empty.json()["status"] == "empty"
    assert client.get(f"{empty_endpoint}/passages").json() == []

    _, _, file, broken_endpoint = _project_source_file(client, tmp_path / "broken", monkeypatch, b"%PDF-1.7\nnot a document")
    failed = client.post(f"{broken_endpoint}/extractions")
    assert failed.status_code == 201
    assert failed.json()["status"] == "failed"
    assert "PDF extraction failed" in failed.json()["error"]
    downloaded = client.get(broken_endpoint)
    assert downloaded.status_code == 200
    assert downloaded.content == b"%PDF-1.7\nnot a document"
    assert file["id"] == failed.json()["file_id"]


def test_partial_page_error_is_visible_and_keeps_successful_passage(
    client: TestClient, tmp_path: Path, monkeypatch
) -> None:
    _, _, _, endpoint = _project_source_file(client, tmp_path, monkeypatch, _pdf_with_text())
    from paperweave.modules.documents import service as document_service
    from paperweave.integrations.documents.pdf_text import PageText

    monkeypatch.setattr(document_service, "extract_pdf_pages", lambda _content: [
        PageText(1, "Readable page text"), PageText(2, "", "Page 2 could not be read")
    ])
    partial = client.post(f"{endpoint}/extractions")
    assert partial.status_code == 201
    assert partial.json()["status"] == "partial"
    assert "Page 2" in partial.json()["error"]
    passages = client.get(f"{endpoint}/passages").json()
    assert len(passages) == 1
    assert passages[0]["page_number"] == 1
    assert passages[0]["text"] == "Readable page text"


def test_new_file_version_marks_prior_passage_for_review(client: TestClient, tmp_path: Path, monkeypatch) -> None:
    original_pdf = _pdf_with_text()
    project, source, file, endpoint = _project_source_file(client, tmp_path, monkeypatch, original_pdf)
    assert client.post(f"{endpoint}/extractions").json()["status"] == "complete"
    base = f"/api/v1/projects/{project['id']}/sources/{source['id']}/files"
    newer = client.post(base, files={"file": ("paper-v2.pdf", _pdf_with_text("New version text"), "application/pdf")}, headers={"Idempotency-Key": "documents-version-two"})
    assert newer.status_code == 201
    passages = client.get(f"{endpoint}/passages").json()
    assert passages and all(passage["review_state"] == "needs_review" for passage in passages)
    assert client.get(endpoint).content == original_pdf
