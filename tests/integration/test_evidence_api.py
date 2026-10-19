"""Claim identity, typed evidence and explicit author review lifecycle."""
from io import BytesIO

from fastapi.testclient import TestClient
from pypdf import PdfWriter


def _pdf_with_text(text: str = "Evidence passage text") -> bytes:
    from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject
    writer = PdfWriter()
    page = writer.add_blank_page(width=300, height=300)
    stream = DecodedStreamObject()
    safe_text = text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    stream.set_data(f"BT /F1 12 Tf 40 100 Td ({safe_text}) Tj ET".encode())
    page[NameObject("/Contents")] = writer._add_object(stream)
    font = DictionaryObject({NameObject("/Type"): NameObject("/Font"), NameObject("/Subtype"): NameObject("/Type1"), NameObject("/BaseFont"): NameObject("/Helvetica")})
    page[NameObject("/Resources")] = writer._add_object(DictionaryObject({NameObject("/Font"): DictionaryObject({NameObject("/F1"): writer._add_object(font)})}))
    output = BytesIO()
    writer.write(output)
    return output.getvalue()


def _evidence_fixture(client: TestClient, tmp_path, monkeypatch):
    monkeypatch.setenv("PW_FILE_STORAGE", str(tmp_path))
    project = client.post("/api/v1/projects", json={"name": "Evidence project"}).json()
    project_id = project["id"]
    manuscript_url = f"/api/v1/projects/{project_id}/manuscript"
    manuscript = client.post(manuscript_url, json={"content": {"type": "doc", "content": [{"type": "paragraph", "content": [{"type": "text", "text": "The claim text"}]}]}}).json()
    sources_url = f"/api/v1/projects/{project_id}/sources"
    source = client.post(sources_url, json={"title": "Evidence paper"}).json()
    uploaded = client.post(f"{sources_url}/{source['id']}/files", files={"file": ("evidence.pdf", _pdf_with_text(), "application/pdf")}).json()
    document_url = f"{sources_url}/{source['id']}/files/{uploaded['id']}"
    run = client.post(f"{document_url}/extractions")
    assert run.status_code == 201
    passage = client.get(f"{document_url}/passages").json()[0]
    return project_id, manuscript_url, manuscript, passage


def test_claim_typed_link_requires_explicit_owner_review_and_invalidates_on_manuscript_change(client: TestClient, tmp_path, monkeypatch):
    project_id, manuscript_url, manuscript, passage = _evidence_fixture(client, tmp_path, monkeypatch)
    claims_url = f"/api/v1/projects/{project_id}/claims"
    claim_response = client.post(claims_url, json={"text": "The claim text", "block_position": 1})
    assert claim_response.status_code == 201
    claim = claim_response.json()
    assert claim["version"] == 1

    unsupported = client.post(f"{claims_url}/{claim['id']}/links", json={"passage_id": passage["id"], "relation": "proves"})
    assert unsupported.status_code == 422
    link_response = client.post(f"{claims_url}/{claim['id']}/links", json={"passage_id": passage["id"], "relation": "supports"})
    assert link_response.status_code == 201
    link = link_response.json()
    assert link["review_state"] == "unreviewed"
    assert link["version"] == 1
    assert link["passage_file_id"] == passage["file_id"]
    assert link["source_title"] == "Evidence paper"
    assert link["reviewer_id"] is None

    reviewed = client.post(f"{claims_url}/links/{link['id']}/review", json={"decision": "verified", "note": "Checked against page text"})
    assert reviewed.status_code == 200
    assert reviewed.json()["review_state"] == "verified"
    assert reviewed.json()["version"] == 2
    assert reviewed.json()["reviewer_id"]
    assert reviewed.json()["note"] == "Checked against page text"

    changed = client.put(manuscript_url, json={"content": {"type": "doc", "content": [{"type": "paragraph", "content": [{"type": "text", "text": "Revised claim"}]}]}, "expected_version": manuscript["version"]})
    assert changed.status_code == 200
    listed = client.get(claims_url).json()
    assert listed[0]["links"][0]["review_state"] == "needs_review"
    refreshed = client.post(f"{claims_url}/links/{link['id']}/review", json={"decision": "verified", "note": "Rechecked current manuscript version"})
    assert refreshed.status_code == 200
    assert refreshed.json()["review_state"] == "verified"
    assert refreshed.json()["manuscript_version"] == changed.json()["version"]
    assert client.get(claims_url).json()[0]["manuscript_version"] == changed.json()["version"]


def test_editing_claim_marks_its_evidence_for_review(client: TestClient, tmp_path, monkeypatch):
    project_id, _, _, passage = _evidence_fixture(client, tmp_path, monkeypatch)
    claims_url = f"/api/v1/projects/{project_id}/claims"
    claim = client.post(claims_url, json={"text": "An initial claim", "block_position": 0}).json()
    link = client.post(f"{claims_url}/{claim['id']}/links", json={"passage_id": passage["id"], "relation": "contextualizes"}).json()
    update = client.put(f"{claims_url}/{claim['id']}", json={"text": "A revised claim", "expected_version": claim["version"]})
    assert update.status_code == 200
    assert update.json()["version"] == 2
    assert update.json()["links"][0]["review_state"] == "needs_review"
    assert link["claim_version"] == 1
    refreshed = client.post(f"{claims_url}/links/{link['id']}/review", json={"decision": "verified"})
    assert refreshed.status_code == 200
    assert refreshed.json()["claim_version"] == 2


def test_unlink_retracts_link_and_keeps_review_history(client: TestClient, tmp_path, monkeypatch):
    project_id, _, _, passage = _evidence_fixture(client, tmp_path, monkeypatch)
    claims_url = f"/api/v1/projects/{project_id}/claims"
    claim = client.post(claims_url, json={"text": "A claim", "block_position": 0}).json()
    link = client.post(f"{claims_url}/{claim['id']}/links", json={"passage_id": passage["id"], "relation": "supports"}).json()
    reviewed = client.post(f"{claims_url}/links/{link['id']}/review", json={"decision": "verified"})
    assert reviewed.status_code == 200
    unlinked = client.delete(f"{claims_url}/links/{link['id']}")
    assert unlinked.status_code == 200
    assert unlinked.json()["review_state"] == "retracted"
    assert unlinked.json()["decision"] == "verified"
    replacement = client.post(f"{claims_url}/{claim['id']}/links", json={"passage_id": passage["id"], "relation": "contextualizes"})
    assert replacement.status_code == 201
    assert replacement.json()["id"] != link["id"]


def test_replacing_source_file_marks_existing_evidence_stale(client: TestClient, tmp_path, monkeypatch):
    project_id, _, _, passage = _evidence_fixture(client, tmp_path, monkeypatch)
    sources_url = f"/api/v1/projects/{project_id}/sources"
    source = client.get(sources_url).json()[0]
    claims_url = f"/api/v1/projects/{project_id}/claims"
    claim = client.post(claims_url, json={"text": "A claim", "block_position": 0}).json()
    link = client.post(f"{claims_url}/{claim['id']}/links", json={"passage_id": passage["id"], "relation": "supports"}).json()
    replacement = client.post(f"{sources_url}/{source['id']}/files", files={"file": ("replacement.pdf", _pdf_with_text("Replacement source text"), "application/pdf")})
    assert replacement.status_code == 201
    listed = client.get(claims_url).json()
    assert listed[0]["links"][0]["review_state"] == "needs_review"
