"""Persistence adapter for owner-scoped AI proposals and manuscript decisions."""

from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from paperweave.infrastructure.db.manuscript_repository import update_manuscript_content
from paperweave.infrastructure.db.models import AIProposalRecord, ManuscriptRecord, ProjectRecord


class AIProposalRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_owned_manuscript(self, owner_id: UUID, project_id: UUID):
        return self.session.scalar(select(ManuscriptRecord).join(ProjectRecord).where(
            ProjectRecord.owner_id == owner_id, ProjectRecord.id == project_id,
            ManuscriptRecord.project_id == project_id))

    def get_by_key(self, owner_id: UUID, project_id: UUID, key: str):
        row = self.session.scalar(select(AIProposalRecord).join(ProjectRecord).where(
            AIProposalRecord.project_id == project_id,
            ProjectRecord.owner_id == owner_id,
            AIProposalRecord.idempotency_key == key))
        return self._response(row) if row else None

    def create(self, owner_id: UUID, project_id: UUID, key: str, manifest: dict,
               suggestion: str, provider: str, model: str):
        manuscript = self.get_owned_manuscript(owner_id, project_id)
        if manuscript is None:
            return None
        row = AIProposalRecord(
            id=uuid4(), project_id=project_id, manuscript_id=manuscript.id,
            idempotency_key=key, target_version=manifest["target_version"],
            target_position=manifest["target_position"], context_manifest=manifest,
            suggestion=suggestion, provider=provider, model=model, status="pending",
        )
        self.session.add(row)
        try:
            self.session.commit()
        except IntegrityError:
            self.session.rollback()
            return self.get_by_key(owner_id, project_id, key)
        self.session.refresh(row)
        return self._response(row)

    def record_failure(self, owner_id: UUID, project_id: UUID, key: str, manifest: dict,
                       provider: str, model: str, error_code: str) -> None:
        manuscript = self.get_owned_manuscript(owner_id, project_id)
        if manuscript is None:
            return
        self.session.add(AIProposalRecord(
            id=uuid4(), project_id=project_id, manuscript_id=manuscript.id,
            idempotency_key=key, target_version=manifest["target_version"],
            target_position=manifest["target_position"], context_manifest=manifest,
            suggestion=None, provider=provider, model=model, status="failed",
            error_code=error_code[:80],
        ))
        try:
            self.session.commit()
        except IntegrityError:
            self.session.rollback()

    def get(self, owner_id: UUID, project_id: UUID, proposal_id: UUID):
        row = self._owned_proposal(owner_id, project_id, proposal_id)
        return self._response(row) if row else None

    def decide(self, owner_id: UUID, project_id: UUID, proposal_id: UUID,
               decision: str, note: str | None):
        row = self._owned_proposal(owner_id, project_id, proposal_id, lock=True)
        if row is None:
            return None
        if row.status in {"accepted", "rejected"}:
            if row.status != decision:
                return "already_decided"
            manuscript = self.get_owned_manuscript(owner_id, project_id)
            return self._response(row, manuscript)
        if row.status != "pending":
            return row.status
        manuscript = self.get_owned_manuscript(owner_id, project_id)
        if manuscript is None:
            return None
        if manuscript.version != row.target_version:
            row.status = "stale"
            self.session.commit()
            return "stale_target"
        original = row.context_manifest["selected_text"]
        from paperweave.modules.ai_proposals.errors import InvalidSelectionError
        from paperweave.modules.ai_proposals.selection import replace_selected_text
        try:
            content = replace_selected_text(
                manuscript.content, row.target_position, original, row.suggestion or "")
        except InvalidSelectionError:
            row.status = "stale"
            self.session.commit()
            return "stale_target"
        if decision == "accepted":
            updated = update_manuscript_content(
                self.session, manuscript.id, row.target_version, content)
            if updated is None:
                row.status = "stale"
                self.session.commit()
                return "stale_target"
        row.status = decision
        row.reviewer_id = owner_id
        row.decision_at = datetime.now(timezone.utc)
        row.decision_note = note
        self.session.commit()
        current = self.session.get(ManuscriptRecord, manuscript.id, populate_existing=True)
        return self._response(row, current)

    def _owned_proposal(self, owner_id: UUID, project_id: UUID, proposal_id: UUID, lock: bool = False):
        query = select(AIProposalRecord).join(ProjectRecord).where(
            AIProposalRecord.id == proposal_id, AIProposalRecord.project_id == project_id,
            ProjectRecord.id == project_id, ProjectRecord.owner_id == owner_id)
        if lock:
            query = query.with_for_update()
        return self.session.scalar(query)

    @staticmethod
    def _response(row: AIProposalRecord, manuscript: ManuscriptRecord | None = None):
        return {
            "id": row.id, "project_id": row.project_id, "manuscript_id": row.manuscript_id,
            "target_version": row.target_version, "target_position": row.target_position,
            "context_manifest": row.context_manifest, "suggestion": row.suggestion,
            "provider": row.provider, "model": row.model, "status": row.status,
            "reviewer_id": row.reviewer_id, "decision_at": row.decision_at,
            "decision_note": row.decision_note, "created_at": row.created_at,
            "updated_at": row.updated_at, "error_code": row.error_code,
            "manuscript": ({"id": manuscript.id, "project_id": manuscript.project_id,
                            "content": manuscript.content, "version": manuscript.version,
                            "updated_at": manuscript.updated_at} if manuscript else None),
        }
