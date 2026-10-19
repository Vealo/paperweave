"""SQLAlchemy adapter implementing the Projects persistence port."""

from datetime import timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from paperweave.infrastructure.db.models import ProjectRecord
from paperweave.modules.projects.domain import Project
from paperweave.modules.projects.repository import ProjectRepository


class SqlAlchemyProjectRepository(ProjectRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    def create(self, name: str, description: str | None) -> Project:
        record = ProjectRecord(name=name, description=description)
        self._session.add(record)
        self._session.flush()
        self._session.refresh(record)
        self._session.commit()
        return self._to_domain(record)

    def list(self) -> list[Project]:
        records = self._session.scalars(
            select(ProjectRecord).order_by(ProjectRecord.created_at.desc(), ProjectRecord.id.desc())
        ).all()
        return [self._to_domain(record) for record in records]

    def get(self, project_id: UUID) -> Project | None:
        record = self._session.get(ProjectRecord, project_id)
        return self._to_domain(record) if record is not None else None

    @staticmethod
    def _to_domain(record: ProjectRecord) -> Project:
        return Project(
            id=record.id,
            name=record.name,
            description=record.description,
            created_at=record.created_at.astimezone(timezone.utc),
        )
