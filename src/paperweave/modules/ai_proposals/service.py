"""Application service for owner-reviewed manuscript AI proposals."""

from typing import Any
from uuid import UUID

from paperweave.integrations.llm.adapter import LLMAdapter
from paperweave.modules.ai_proposals.errors import InvalidSelectionError, ProposalAdapterError
from paperweave.modules.ai_proposals.selection import selected_text_at


class AIProposalService:
    def __init__(self, repository, adapter: LLMAdapter) -> None:
        self.repository = repository
        self.adapter = adapter

    def create(self, owner_id: UUID, project_id: UUID, *, expected_version: int,
               target_position: int, selected_text: str, instruction: str,
               idempotency_key: str):
        manifest = {
            "target_position": target_position,
            "selected_text": selected_text,
            "instruction": instruction,
            "target_version": expected_version,
        }
        prior = self.repository.get_by_key(owner_id, project_id, idempotency_key)
        if prior is not None:
            if prior["context_manifest"] != manifest:
                return "idempotency_conflict"
            return prior
        manuscript = self.repository.get_owned_manuscript(owner_id, project_id)
        if manuscript is None:
            return None
        if manuscript.version != expected_version:
            return "stale_target"
        try:
            actual = selected_text_at(manuscript.content, target_position, len(selected_text))
        except InvalidSelectionError:
            return "invalid_selection"
        if actual != selected_text:
            return "stale_target"
        try:
            suggestion = self.adapter.propose(selected_text=selected_text, instruction=instruction)
        except Exception as exc:
            self.repository.record_failure(owner_id, project_id, idempotency_key, manifest,
                                           self.adapter.provider, self.adapter.model, type(exc).__name__)
            raise ProposalAdapterError from None
        return self.repository.create(owner_id, project_id, idempotency_key, manifest,
                                      suggestion, self.adapter.provider, self.adapter.model)

    def get(self, owner_id: UUID, project_id: UUID, proposal_id: UUID):
        return self.repository.get(owner_id, project_id, proposal_id)

    def decide(self, owner_id: UUID, project_id: UUID, proposal_id: UUID, *, decision: str, note: str | None):
        return self.repository.decide(owner_id, project_id, proposal_id, decision, note)
