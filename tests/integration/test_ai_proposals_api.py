"""Local-only mock AI proposal lifecycle contract."""

from sqlalchemy import select
from fastapi import Request

from paperweave.api.ai_proposals import get_ai_proposal_service
from paperweave.infrastructure.db.ai_proposal_repository import AIProposalRepository
from paperweave.infrastructure.db.models import AIProposalRecord
from paperweave.modules.ai_proposals.service import AIProposalService


def _project_and_manuscript(client, text: str = "Original claim"):
    project = client.post("/api/v1/projects", json={"name": "AI test", "description": None}).json()
    content = {"type": "doc", "content": [{"type": "paragraph", "content": [{"type": "text", "text": text}]}]}
    manuscript = client.post(f"/api/v1/projects/{project['id']}/manuscript", json={"content": content}).json()
    return project, manuscript, content


def _proposal_payload(text: str = "Original", **overrides):
    values = {
        "expected_version": 1,
        "target_position": 1,
        "selected_text": text,
        "instruction": "Clarify the wording",
        "idempotency_key": "key-ai-proposal-0001",
    }
    values.update(overrides)
    return values


def test_preview_shows_exact_manifest_and_is_idempotent(client):
    project, _, _ = _project_and_manuscript(client)
    url = f"/api/v1/projects/{project['id']}/ai-proposals"
    response = client.post(url, json=_proposal_payload())
    assert response.status_code == 201
    proposal = response.json()
    assert proposal["provider"] == "mock"
    assert proposal["model"] == "paperweave-deterministic-mock"
    assert proposal["context_manifest"] == {
        "target_version": 1,
        "target_position": 1,
        "selected_text": "Original",
        "instruction": "Clarify the wording",
    }
    retry = client.post(url, json=_proposal_payload())
    assert retry.status_code == 201
    assert retry.json()["id"] == proposal["id"]
    conflict = client.post(url, json=_proposal_payload(instruction="Different instruction"))
    assert conflict.status_code == 409
    assert conflict.json()["detail"] == "idempotency_conflict"


def test_reject_preserves_manuscript_and_decision_is_idempotent(client):
    project, manuscript, original = _project_and_manuscript(client)
    url = f"/api/v1/projects/{project['id']}/ai-proposals"
    proposal = client.post(url, json=_proposal_payload()).json()
    decision_url = f"{url}/{proposal['id']}/decision"
    rejected = client.post(decision_url, json={"decision": "rejected"})
    assert rejected.status_code == 200
    assert rejected.json()["status"] == "rejected"
    assert rejected.json()["reviewer_id"]
    assert rejected.json()["decision_at"]
    retry = client.post(decision_url, json={"decision": "rejected"})
    assert retry.status_code == 200
    current = client.get(f"/api/v1/projects/{project['id']}/manuscript").json()
    assert current["id"] == manuscript["id"]
    assert current["version"] == 1
    assert current["content"] == original


def test_accept_creates_new_version_and_keeps_original_in_proposal_manifest(client):
    project, _, _ = _project_and_manuscript(client)
    url = f"/api/v1/projects/{project['id']}/ai-proposals"
    proposal = client.post(url, json=_proposal_payload()).json()
    accepted = client.post(f"{url}/{proposal['id']}/decision", json={"decision": "accepted"})
    assert accepted.status_code == 200
    body = accepted.json()
    assert body["status"] == "accepted"
    assert body["context_manifest"]["selected_text"] == "Original"
    assert body["manuscript"]["version"] == 2
    assert body["manuscript"]["content"]["content"][0]["content"][0]["text"] == "[Демо-предложение] Original claim"
    previous = client.get(f"/api/v1/projects/{project['id']}/manuscript/versions/1")
    assert previous.status_code == 200
    assert previous.json()["content"]["content"][0]["content"][0]["text"] == "Original claim"
    retry = client.post(f"{url}/{proposal['id']}/decision", json={"decision": "accepted"})
    assert retry.status_code == 200
    assert retry.json()["manuscript"]["version"] == 2


def test_stale_target_is_marked_and_never_applied(client):
    project, _, _ = _project_and_manuscript(client)
    url = f"/api/v1/projects/{project['id']}/ai-proposals"
    proposal = client.post(url, json=_proposal_payload()).json()
    changed = {"type": "doc", "content": [{"type": "paragraph", "content": [{"type": "text", "text": "New text"}]}]}
    assert client.put(f"/api/v1/projects/{project['id']}/manuscript", json={"content": changed, "expected_version": 1}).status_code == 200
    decision = client.post(f"{url}/{proposal['id']}/decision", json={"decision": "accepted"})
    assert decision.status_code == 409
    assert decision.json()["detail"] == "stale_target"
    current = client.get(f"/api/v1/projects/{project['id']}/manuscript").json()
    assert current["version"] == 2
    assert current["content"] == changed


def test_adapter_timeout_is_explicit_and_does_not_change_manuscript(client):
    class TimeoutAdapter:
        provider = "mock"
        model = "timeout-test"

        def propose(self, *, selected_text: str, instruction: str) -> str:
            raise TimeoutError("simulated timeout")

    def override_service(request: Request):
        with request.app.state.session_factory() as session:
            yield AIProposalService(AIProposalRepository(session), TimeoutAdapter())

    project, _, original = _project_and_manuscript(client)
    client.app.dependency_overrides[get_ai_proposal_service] = override_service
    try:
        response = client.post(f"/api/v1/projects/{project['id']}/ai-proposals", json=_proposal_payload())
    finally:
        client.app.dependency_overrides.pop(get_ai_proposal_service, None)
    assert response.status_code == 503, response.text
    current = client.get(f"/api/v1/projects/{project['id']}/manuscript").json()
    assert current["version"] == 1
    assert current["content"] == original
    with client.app.state.session_factory() as session:
        row = session.scalar(select(AIProposalRecord).where(AIProposalRecord.project_id == project["id"]))
        assert row.status == "failed"
        assert row.error_code == "TimeoutError"


def test_wrong_owner_cannot_read_proposal(client):
    project, _, _ = _project_and_manuscript(client)
    proposal = client.post(f"/api/v1/projects/{project['id']}/ai-proposals", json=_proposal_payload()).json()
    created = client.post("/api/v1/auth/users", json={
        "email": "member@example.test", "display_name": "Member", "password": "member-password-123"
    })
    assert created.status_code == 201
    client.post("/api/v1/auth/logout")
    assert client.post("/api/v1/auth/login", json={
        "email": "member@example.test", "password": "member-password-123"
    }).status_code == 200
    assert client.get(f"/api/v1/projects/{project['id']}/ai-proposals/{proposal['id']}").status_code == 404
