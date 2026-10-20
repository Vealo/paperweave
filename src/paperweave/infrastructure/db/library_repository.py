"""SQLAlchemy adapter for project library records."""
from uuid import UUID
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from paperweave.infrastructure.db.models import FileArtifactRecord, ProjectRecord, SourceRecord, SourceFileRecord, SourceFileReferenceRecord
from paperweave.modules.library.errors import DuplicateFileError, DuplicateSourceError, ReferencedFileError
from paperweave.modules.library.domain import Source, SourceFile

class SqlAlchemyLibraryRepository:
    def __init__(self, session: Session, storage=None) -> None: self.session, self.storage = session, storage
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
    def find_file_idempotency_artifact(self, source_id, idempotency_key):
        owner_id = self.session.scalar(select(ProjectRecord.owner_id).join(SourceRecord, SourceRecord.project_id == ProjectRecord.id).where(SourceRecord.id == source_id))
        return self.session.scalar(select(FileArtifactRecord).where(FileArtifactRecord.owner_user_id == owner_id, FileArtifactRecord.idempotency_key == idempotency_key, FileArtifactRecord.kind == "document"))
    def reserve_file_artifact(self, source_id, file_id, original_name, size, digest, key, idempotency_key):
        owner_id = self.session.scalar(select(ProjectRecord.owner_id).join(SourceRecord, SourceRecord.project_id == ProjectRecord.id).where(SourceRecord.id == source_id))
        existing = self.session.scalar(select(FileArtifactRecord).where(FileArtifactRecord.owner_user_id == owner_id, FileArtifactRecord.idempotency_key == idempotency_key, FileArtifactRecord.kind == "document"))
        if existing is not None:
            return existing
        artifact = FileArtifactRecord(id=file_id, owner_user_id=owner_id, kind="document", domain_type="source_file", domain_id=file_id, domain_parent_id=source_id, backend=getattr(self.storage, "backend", "local"), bucket=getattr(self.storage, "bucket", ""), object_key=key, original_name=original_name, media_type="application/pdf", size_bytes=size, checksum_sha256=digest, version=1, lifecycle="pending_upload", idempotency_key=idempotency_key)
        self.session.add(artifact)
        try:
            self.session.commit()
        except IntegrityError:
            self.session.rollback()
            existing = self.session.scalar(select(FileArtifactRecord).where(FileArtifactRecord.owner_user_id == owner_id, FileArtifactRecord.idempotency_key == idempotency_key, FileArtifactRecord.kind == "document"))
            if existing is None:
                raise
            return existing
        return artifact

    def mark_artifact_pending_delete(self, artifact_id):
        artifact = self.session.get(FileArtifactRecord, artifact_id)
        if artifact:
            artifact.lifecycle = "pending_delete"
            self.session.commit()
    def create_file(self, source_id, file_id, original_name, size, digest, key):
        self.session.scalar(select(SourceRecord).where(SourceRecord.id == source_id).with_for_update())
        owner_id = self.session.scalar(select(ProjectRecord.owner_id).join(SourceRecord, SourceRecord.project_id == ProjectRecord.id).where(SourceRecord.id == source_id))
        version = (self.session.scalar(select(func.max(SourceFileRecord.version)).where(SourceFileRecord.source_id == source_id)) or 0) + 1
        artifact = self.session.get(FileArtifactRecord, file_id)
        if artifact is None:
            artifact = FileArtifactRecord(id=file_id, owner_user_id=owner_id, kind="document", domain_type="source_file", domain_id=file_id, domain_parent_id=source_id, backend=getattr(self.storage, "backend", "local"), bucket=getattr(self.storage, "bucket", ""), object_key=key, original_name=original_name, media_type="application/pdf", size_bytes=size, checksum_sha256=digest, version=version, lifecycle="pending_upload", idempotency_key=f"source-file-{file_id.hex}")
            self.session.add(artifact)
        artifact.version = version
        artifact.lifecycle = "active"
        record = SourceFileRecord(id=file_id, source_id=source_id, version=version, original_name=original_name, media_type="application/pdf", size_bytes=size, sha256=digest, storage_key=key, artifact_id=file_id)
        self.session.add(record)
        try:
            self.session.flush()
            self.session.query(SourceFileReferenceRecord).filter(
                SourceFileReferenceRecord.file_id.in_(
                    select(SourceFileRecord.id).where(
                        SourceFileRecord.source_id == source_id,
                        SourceFileRecord.id != file_id,
                    )
                )
            ).update({SourceFileReferenceRecord.review_state: "needs_review"}, synchronize_session=False)
            self.session.commit()
        except IntegrityError:
            self.session.rollback()
            if self.has_checksum(source_id, digest): raise DuplicateFileError("This file version already exists")
            raise
        self.session.refresh(record)
        return self._file(record)
    def file_is_referenced(self, file_id):
        return self.session.scalar(select(SourceFileReferenceRecord.id).where(SourceFileReferenceRecord.file_id == file_id)) is not None
    def delete_file(self, file_id):
        record = self.session.get(SourceFileRecord, file_id)
        artifact = self.session.get(FileArtifactRecord, record.artifact_id) if record and record.artifact_id else None
        if record:
            if artifact is not None:
                artifact.lifecycle = "pending_delete"
                record.artifact_id = None
            self.session.delete(record)
            try: self.session.commit()
            except IntegrityError as exc:
                self.session.rollback()
                if self.file_is_referenced(file_id): raise ReferencedFileError from exc
                raise
        return artifact

    def get_file(self, project_id, source_id, file_id):
        row = self.session.scalar(select(SourceFileRecord).join(SourceRecord).where(SourceRecord.project_id == project_id, SourceRecord.id == source_id, SourceFileRecord.id == file_id))
        return self._file(row) if row else None

    def resolve_file_after_write_error(self, project_id, source_id, file_id):
        self.session.rollback()
        return self.get_file(project_id, source_id, file_id)

    def mark_artifact_deleted(self, artifact_id):
        from datetime import datetime, timezone
        artifact = self.session.get(FileArtifactRecord, artifact_id)
        if artifact:
            artifact.lifecycle, artifact.deleted_at, artifact.last_cleanup_error = "deleted", datetime.now(timezone.utc), None
            self.session.commit()

    def mark_artifact_cleanup_failed(self, artifact_id, error_type):
        artifact = self.session.get(FileArtifactRecord, artifact_id)
        if artifact:
            artifact.lifecycle = "pending_delete"
            artifact.cleanup_attempts += 1
            artifact.last_cleanup_error = error_type[:500]
            self.session.commit()

    @staticmethod
    def _source(row):
        return Source(id=row.id, project_id=row.project_id, title=row.title, authors=row.authors, year=row.year, doi=row.doi, metadata_provenance=row.metadata_provenance, created_at=row.created_at)

    @staticmethod
    def _file(row):
        return SourceFile(id=row.id, source_id=row.source_id, version=row.version, original_name=row.original_name, media_type=row.media_type, size_bytes=row.size_bytes, sha256=row.sha256, created_at=row.created_at, storage_key=row.storage_key, backend=row.artifact.backend if row.artifact else "local")
