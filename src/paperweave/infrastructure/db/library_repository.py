"""SQLAlchemy adapter for project library records."""
from uuid import UUID
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from paperweave.infrastructure.db.models import ProjectRecord, SourceRecord, SourceFileRecord, SourceFileReferenceRecord
from paperweave.modules.library.errors import DuplicateFileError, DuplicateSourceError, ReferencedFileError
from paperweave.modules.library.domain import Source, SourceFile

class SqlAlchemyLibraryRepository:
    def __init__(self, session: Session) -> None: self.session = session
    def get_owned_project(self, owner_id: UUID, project_id: UUID):
        return self.session.scalar(select(ProjectRecord).where(ProjectRecord.id == project_id, ProjectRecord.owner_id == owner_id))
    def list_sources(self, project_id: UUID):
        return [self._source(row) for row in self.session.scalars(select(SourceRecord).where(SourceRecord.project_id == project_id).order_by(SourceRecord.created_at.desc()))]
    def list_files(self, source_id):
        return [self._file(row) for row in self.session.scalars(select(SourceFileRecord).where(SourceFileRecord.source_id == source_id).order_by(SourceFileRecord.version.desc()))]
    def find_doi(self, project_id: UUID, doi: str):
        row = self.session.scalar(select(SourceRecord).where(SourceRecord.project_id == project_id, SourceRecord.doi == doi))
        return self._source(row) if row else None
    def find_metadata_duplicate(self, project_id: UUID, title: str, authors: str | None, year: int | None):
        row = self.session.scalar(select(SourceRecord).where(
            SourceRecord.project_id == project_id,
            func.lower(SourceRecord.title) == title.strip().lower(),
            func.lower(func.coalesce(SourceRecord.authors, "")) == (authors or "").strip().lower(),
            SourceRecord.year.is_not_distinct_from(year),
        ))
        return self._source(row) if row else None
    def create_source(self, project_id, title, authors, year, doi):
        record = SourceRecord(project_id=project_id, title=title, authors=authors, year=year, doi=doi, metadata_provenance="manual")
        self.session.add(record)
        try:
            self.session.commit()
        except IntegrityError:
            self.session.rollback()
            duplicate = self.find_doi(project_id, doi) if doi else self.find_metadata_duplicate(project_id, title, authors, year)
            if duplicate: raise DuplicateSourceError(str(duplicate.id))
            raise
        self.session.refresh(record)
        return self._source(record)
    def get_source(self, project_id, source_id):
        row = self.session.scalar(select(SourceRecord).where(SourceRecord.project_id == project_id, SourceRecord.id == source_id))
        return self._source(row) if row else None
    def has_checksum(self, source_id, digest):
        return self.session.scalar(select(SourceFileRecord.id).where(SourceFileRecord.source_id == source_id, SourceFileRecord.sha256 == digest)) is not None
    def create_file(self, source_id, file_id, original_name, size, digest, key):
        self.session.scalar(select(SourceRecord).where(SourceRecord.id == source_id).with_for_update())
        version = (self.session.scalar(select(func.max(SourceFileRecord.version)).where(SourceFileRecord.source_id == source_id)) or 0) + 1
        record = SourceFileRecord(id=file_id, source_id=source_id, version=version, original_name=original_name, media_type="application/pdf", size_bytes=size, sha256=digest, storage_key=key)
        self.session.add(record)
        try: self.session.commit()
        except IntegrityError:
            self.session.rollback()
            if self.has_checksum(source_id, digest): raise DuplicateFileError("This file version already exists")
            raise
        self.session.refresh(record)
        return self._file(record)
    def get_file(self, project_id, source_id, file_id):
        row = self.session.scalar(select(SourceFileRecord).join(SourceRecord).where(SourceRecord.project_id == project_id, SourceRecord.id == source_id, SourceFileRecord.id == file_id))
        return self._file(row) if row else None
    def file_is_referenced(self, file_id):
        return self.session.scalar(select(SourceFileReferenceRecord.id).where(SourceFileReferenceRecord.file_id == file_id)) is not None
    def delete_file(self, file_id):
        record = self.session.get(SourceFileRecord, file_id)
        if record:
            self.session.delete(record)
            try: self.session.commit()
            except IntegrityError as exc:
                self.session.rollback()
                if self.file_is_referenced(file_id): raise ReferencedFileError from exc
                raise

    @staticmethod
    def _source(row):
        return Source(id=row.id, project_id=row.project_id, title=row.title, authors=row.authors, year=row.year, doi=row.doi, metadata_provenance=row.metadata_provenance, created_at=row.created_at)

    @staticmethod
    def _file(row):
        return SourceFile(id=row.id, source_id=row.source_id, version=row.version, original_name=row.original_name, media_type=row.media_type, size_bytes=row.size_bytes, sha256=row.sha256, created_at=row.created_at, storage_key=row.storage_key)
