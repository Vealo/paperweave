"""SQLAlchemy persistence for manuscript claims and evidence review."""
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from paperweave.infrastructure.db.models import (
    ClaimRecord, EvidenceLinkRecord, ManuscriptRecord, ProjectRecord,
    ReviewDecisionRecord, SourceFileRecord, SourceFileReferenceRecord,
    SourcePassageRecord, SourceRecord,
)


class EvidenceRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def _owned_manuscript(self, owner_id: UUID, project_id: UUID):
        return self.session.scalar(select(ManuscriptRecord).join(ProjectRecord).where(
            ProjectRecord.owner_id == owner_id, ProjectRecord.id == project_id,
            ManuscriptRecord.project_id == project_id))

    def list_claims(self, owner_id: UUID, project_id: UUID):
        manuscript = self._owned_manuscript(owner_id, project_id)
        if not manuscript:
            return None
        claims = self.session.scalars(select(ClaimRecord).where(
            ClaimRecord.manuscript_id == manuscript.id).order_by(ClaimRecord.created_at))
        return [{"id": c.id, "manuscript_id": c.manuscript_id, "block_position": c.block_position,
                 "text": c.text, "version": c.version, "manuscript_version": c.manuscript_version,
                 "links": self._links(c.id)} for c in claims]

    def create_claim(self, owner_id: UUID, project_id: UUID, block_position: int, text: str):
        manuscript = self._owned_manuscript(owner_id, project_id)
        if not manuscript:
            return None
        claim = ClaimRecord(manuscript_id=manuscript.id, block_position=block_position,
                            text=text.strip(), version=1, manuscript_version=manuscript.version)
        self.session.add(claim)
        self.session.commit()
        self.session.refresh(claim)
        return {"id": claim.id, "manuscript_id": claim.manuscript_id, "block_position": claim.block_position,
                "text": claim.text, "version": claim.version, "manuscript_version": claim.manuscript_version, "links": []}

    def update_claim(self, owner_id: UUID, project_id: UUID, claim_id: UUID, expected_version: int, text: str):
        manuscript = self._owned_manuscript(owner_id, project_id)
        if not manuscript:
            return None
        claim = self.session.scalar(select(ClaimRecord).where(
            ClaimRecord.id == claim_id, ClaimRecord.manuscript_id == manuscript.id,
            ClaimRecord.version == expected_version))
        if not claim:
            return None
        claim.text = text.strip()
        claim.version += 1
        claim.manuscript_version = manuscript.version
        self.session.execute(update(EvidenceLinkRecord).where(EvidenceLinkRecord.claim_id == claim_id)
                             .values(review_state="needs_review", version=EvidenceLinkRecord.version + 1))
        self.session.commit()
        self.session.refresh(claim)
        return {"id": claim.id, "manuscript_id": claim.manuscript_id, "block_position": claim.block_position,
                "text": claim.text, "version": claim.version, "manuscript_version": claim.manuscript_version,
                "links": self._links(claim.id)}

    def create_link(self, owner_id: UUID, project_id: UUID, claim_id: UUID, passage_id: UUID,
                    relation: str, rationale: str | None):
        manuscript = self._owned_manuscript(owner_id, project_id)
        if not manuscript:
            return None
        claim = self.session.scalar(select(ClaimRecord).where(
            ClaimRecord.id == claim_id, ClaimRecord.manuscript_id == manuscript.id))
        passage = self.session.scalar(select(SourcePassageRecord).join(SourceFileRecord,
            SourcePassageRecord.file_id == SourceFileRecord.id).join(SourceRecord,
            SourceFileRecord.source_id == SourceRecord.id).join(ProjectRecord,
            ProjectRecord.id == SourceRecord.project_id).where(
                SourcePassageRecord.id == passage_id, SourceRecord.project_id == project_id,
                ProjectRecord.owner_id == owner_id))
        if not claim or not passage:
            return None
        if claim.manuscript_version != manuscript.version:
            return None
        existing = self.session.scalar(select(EvidenceLinkRecord).where(
            EvidenceLinkRecord.claim_id == claim.id,
            EvidenceLinkRecord.passage_id == passage.id,
            EvidenceLinkRecord.review_state != "retracted"))
        if existing:
            return self._link(existing.id)
        link = EvidenceLinkRecord(claim_id=claim.id, claim_version=claim.version,
            passage_id=passage.id, passage_file_id=passage.file_id, relation=relation,
            rationale=rationale, review_state="unreviewed", manuscript_version=manuscript.version)
        self.session.add(link)
        self.session.flush()
        self.session.add(SourceFileReferenceRecord(file_id=passage.file_id, reference_type="evidence",
            reference_id=link.id, review_state="active"))
        self.session.commit()
        return self._link(link.id)

    def retract_link(self, owner_id: UUID, project_id: UUID, link_id: UUID):
        manuscript = self._owned_manuscript(owner_id, project_id)
        if not manuscript:
            return None
        link = self.session.scalar(select(EvidenceLinkRecord).join(ClaimRecord).where(
            EvidenceLinkRecord.id == link_id, ClaimRecord.manuscript_id == manuscript.id))
        if not link:
            return None
        if link.review_state != "retracted":
            link.review_state = "retracted"
            link.version += 1
            self.session.commit()
        return self._link(link.id)

    def review(self, owner_id: UUID, project_id: UUID, link_id: UUID, decision: str, note: str | None):
        manuscript = self._owned_manuscript(owner_id, project_id)
        if not manuscript:
            return None
        link = self.session.scalar(select(EvidenceLinkRecord).join(ClaimRecord).where(
            EvidenceLinkRecord.id == link_id, ClaimRecord.manuscript_id == manuscript.id))
        if not link:
            return None
        claim = self.session.get(ClaimRecord, link.claim_id)
        passage_ref = self.session.scalar(select(SourceFileReferenceRecord).where(
            SourceFileReferenceRecord.reference_type == "evidence",
            SourceFileReferenceRecord.reference_id == link.id))
        if claim.manuscript_version != manuscript.version:
            claim.manuscript_version = manuscript.version
            claim.version += 1
            link.version += 1
        link.claim_version = claim.version
        link.manuscript_version = manuscript.version
        link.review_state = "needs_review"
        if passage_ref:
            passage_ref.review_state = "active"
        user_id = owner_id
        self.session.add(ReviewDecisionRecord(evidence_link_id=link.id, reviewer_id=user_id,
            link_version=link.version, decision=decision, note=note))
        link.review_state = "verified" if decision == "verified" else "rejected"
        link.version += 1
        self.session.commit()
        return self._link(link.id)

    def _links(self, claim_id: UUID):
        links = self.session.scalars(select(EvidenceLinkRecord).where(EvidenceLinkRecord.claim_id == claim_id)
                                     .order_by(EvidenceLinkRecord.created_at))
        return [self._link(row.id) for row in links]

    def _link(self, link_id: UUID):
        row = self.session.get(EvidenceLinkRecord, link_id)
        if not row:
            return None
        decision = self.session.scalar(select(ReviewDecisionRecord).where(
            ReviewDecisionRecord.evidence_link_id == link_id).order_by(ReviewDecisionRecord.decided_at.desc()))
        passage = self.session.get(SourcePassageRecord, row.passage_id)
        evidence_ref = self.session.scalar(select(SourceFileReferenceRecord).where(
            SourceFileReferenceRecord.reference_type == "evidence",
            SourceFileReferenceRecord.reference_id == row.id))
        source = self.session.scalar(select(SourceRecord).join(SourceFileRecord,
            SourceFileRecord.source_id == SourceRecord.id).join(SourceFileReferenceRecord,
            SourceFileReferenceRecord.file_id == SourceFileRecord.id).where(
                SourceFileReferenceRecord.reference_type == "passage",
                SourceFileRecord.id == row.passage_file_id,
                SourceFileReferenceRecord.reference_id == row.passage_id))
        return {"id": row.id, "claim_id": row.claim_id, "claim_version": row.claim_version,
            "passage_id": row.passage_id, "passage_file_id": row.passage_file_id, "version": row.version,
            "passage_page": passage.page_number if passage else None,
            "passage_text": passage.text if passage else None,
            "source_title": source.title if source else "Источник недоступен",
            "relation": row.relation, "rationale": row.rationale,
            "review_state": "needs_review" if evidence_ref and evidence_ref.review_state == "needs_review" else row.review_state,
            "manuscript_version": row.manuscript_version,
            "reviewer_id": decision.reviewer_id if decision else None,
            "decision": decision.decision if decision else None,
            "decided_at": decision.decided_at if decision else None,
            "note": decision.note if decision else None}
