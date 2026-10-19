"""SQLAlchemy adapter for versioned manuscript persistence."""

from datetime import timezone
from typing import Any
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from paperweave.infrastructure.db.models import ManuscriptRecord
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
            self._session.commit()
        except IntegrityError as exc:
            self._session.rollback()
            raise ManuscriptAlreadyExistsError from exc
        self._session.refresh(record)
        return self._to_domain(record)

    def update(self, project_id: UUID, expected_version: int, content: dict[str, Any]) -> Manuscript | None:
        result = self._session.execute(
            update(ManuscriptRecord)
            .where(ManuscriptRecord.project_id == project_id, ManuscriptRecord.version == expected_version)
            .values(content=content, version=expected_version + 1)
            .returning(ManuscriptRecord.id)
        )
        record_id = result.scalar_one_or_none()
        if record_id is None:
            self._session.rollback()
            return None
        self._session.commit()
        record = self._session.get(ManuscriptRecord, record_id)
        assert record is not None
        return self._to_domain(record)

    @staticmethod
    def _to_domain(record: ManuscriptRecord) -> Manuscript:
        return Manuscript(
            id=record.id,
            project_id=record.project_id,
            content=record.content,
            version=record.version,
            updated_at=record.updated_at.astimezone(timezone.utc),
        )
