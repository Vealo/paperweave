"""Persistence adapter for extraction runs and passages."""
from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from paperweave.infrastructure.db.models import (
    ExtractionRunRecord, ProjectRecord, SourceFileRecord, SourceFileReferenceRecord,
    SourcePassageRecord, SourceRecord,
)
from paperweave.modules.documents.domain import ExtractionRun, SourcePassage


class SqlAlchemyDocumentRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_owned_file(self, owner_id: UUID, project_id: UUID, source_id: UUID, file_id: UUID):
        return self.session.scalar(
            select(SourceFileRecord).join(SourceRecord).join(ProjectRecord).where(
                ProjectRecord.owner_id == owner_id, ProjectRecord.id == project_id,
                SourceRecord.id == source_id, SourceFileRecord.id == file_id,
            )
        )

    def create_run(self, file_id: UUID, processor: str, processor_version: str) -> ExtractionRun:
        record = ExtractionRunRecord(file_id=file_id, processor=processor,
                                     processor_version=processor_version, status="running", page_count=0)
        self.session.add(record)
        self.session.commit()
        self.session.refresh(record)
        return self._run(record)

    def complete_run(self, run_id: UUID, pages, status: str, error: str | None = None) -> ExtractionRun:
        record = self.session.get(ExtractionRunRecord, run_id)
        assert record is not None
        for page in pages:
            if page.text:
                passage = SourcePassageRecord(id=uuid4(), run_id=run_id, file_id=record.file_id,
                                              page_number=page.page_number, text=page.text)
                self.session.add(passage)
                self.session.add(SourceFileReferenceRecord(file_id=record.file_id,
                    reference_type="passage", reference_id=passage.id, review_state="unreviewed"))
        record.page_count = len(pages)
        record.status = status
        record.error = error
        record.completed_at = datetime.now(timezone.utc)
        self.session.commit()
        self.session.refresh(record)
        return self._run(record)

    def fail_run(self, run_id: UUID, error: str) -> ExtractionRun:
        return self.complete_run(run_id, [], "failed", error)

    def list_runs(self, file_id: UUID) -> list[ExtractionRun]:
        records = self.session.scalars(select(ExtractionRunRecord).where(
            ExtractionRunRecord.file_id == file_id).order_by(ExtractionRunRecord.created_at.desc()))
        return [self._run(row) for row in records]

    def list_passages(self, file_id: UUID) -> list[SourcePassage]:
        rows = self.session.execute(
            select(SourcePassageRecord, SourceFileReferenceRecord.review_state)
            .join(SourceFileReferenceRecord, SourceFileReferenceRecord.reference_id == SourcePassageRecord.id)
            .where(SourcePassageRecord.file_id == file_id,
                   SourceFileReferenceRecord.reference_type == "passage")
            .order_by(SourcePassageRecord.page_number, SourcePassageRecord.created_at)
        )
        return [SourcePassage(id=p.id, run_id=p.run_id, file_id=p.file_id, page_number=p.page_number,
                              text=p.text, review_state=state, created_at=p.created_at) for p, state in rows]

    @staticmethod
    def _run(row: ExtractionRunRecord) -> ExtractionRun:
        return ExtractionRun(row.id, row.file_id, row.processor, row.processor_version,
                             row.status, row.page_count, row.error, row.created_at, row.completed_at)
