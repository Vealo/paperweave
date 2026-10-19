"""SQLAlchemy adapter for versioned manuscript persistence."""

from datetime import timezone
from typing import Any
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from paperweave.infrastructure.db.models import ClaimRecord, EvidenceLinkRecord, ManuscriptRecord, ManuscriptRevisionRecord
from paperweave.modules.manuscripts.domain import Manuscript
from paperweave.modules.manuscripts.errors import ManuscriptAlreadyExistsError
from paperweave.modules.manuscripts.repository import ManuscriptRepository


class SqlAlchemyManuscriptRepository(ManuscriptRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    def get(self, project_id: UUID) -> Manuscript | None:
        record = self._session.scalar(select(ManuscriptRecord).where(ManuscriptRecord.project_id == project_id))
        return self._to_domain(record) if record else None

    def create(self, project_id: UUID, content: dict[str, Any]) -> Manuscript:
        record = ManuscriptRecord(project_id=project_id, content=content, version=1)
        self._session.add(record)
        try:
            self._session.flush()
            self._session.add(ManuscriptRevisionRecord(manuscript_id=record.id, version=1, content=content))
            self._session.commit()
        except IntegrityError as exc:
            self._session.rollback()
            raise ManuscriptAlreadyExistsError from exc
        self._session.refresh(record)
        return self._to_domain(record)

    def update(self, project_id: UUID, expected_version: int, content: dict[str, Any]) -> Manuscript | None:
        current = self._session.scalar(select(ManuscriptRecord).where(
            ManuscriptRecord.project_id == project_id))
        if current is None:
            return None
        record = update_manuscript_content(self._session, current.id, expected_version, content)
        if record is None:
            self._session.rollback()
            return None
        self._session.commit()
        self._session.refresh(record)
        return self._to_domain(record)

    def list_versions(self, project_id: UUID):
        manuscript = self.get(project_id)
        if manuscript is None:
            return None
        records = self._session.scalars(select(ManuscriptRevisionRecord).where(
            ManuscriptRevisionRecord.manuscript_id == manuscript.id
        ).order_by(ManuscriptRevisionRecord.version.desc()))
        return [{"version": row.version, "content": row.content, "created_at": row.created_at}
                for row in records]

    def get_version(self, project_id: UUID, version: int):
        manuscript = self.get(project_id)
        if manuscript is None:
            return None
        row = self._session.scalar(select(ManuscriptRevisionRecord).where(
            ManuscriptRevisionRecord.manuscript_id == manuscript.id,
            ManuscriptRevisionRecord.version == version))
        return {"version": row.version, "content": row.content, "created_at": row.created_at} if row else None

    @staticmethod
    def _to_domain(record: ManuscriptRecord) -> Manuscript:
        return Manuscript(
            id=record.id,
            project_id=record.project_id,
            content=record.content,
            version=record.version,
            updated_at=record.updated_at.astimezone(timezone.utc),
        )


def update_manuscript_content(session: Session, manuscript_id: UUID, expected_version: int,
                              content: dict[str, Any]) -> ManuscriptRecord | None:
    """Update an expected revision and invalidate evidence in the caller's transaction."""
    current = session.scalar(select(ManuscriptRecord).where(
        ManuscriptRecord.id == manuscript_id, ManuscriptRecord.version == expected_version
    ).with_for_update())
    if current is None:
        return None
    result = session.execute(
        update(ManuscriptRecord)
        .where(ManuscriptRecord.id == manuscript_id, ManuscriptRecord.version == expected_version)
        .values(content=content, version=expected_version + 1)
        .returning(ManuscriptRecord.id)
    )
    record_id = result.scalar_one_or_none()
    if record_id is None:
        return None
    session.add(ManuscriptRevisionRecord(
        manuscript_id=record_id, version=expected_version + 1, content=content,
    ))
    session.execute(
        update(EvidenceLinkRecord)
        .where(EvidenceLinkRecord.manuscript_version == expected_version,
               EvidenceLinkRecord.claim_id.in_(select(ClaimRecord.id).where(
                   ClaimRecord.manuscript_id == record_id
               )))
        .values(review_state="needs_review", version=EvidenceLinkRecord.version + 1)
    )
    session.flush()
    return session.get(ManuscriptRecord, record_id, populate_existing=True)
