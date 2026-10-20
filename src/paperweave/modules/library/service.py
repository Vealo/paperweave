"""Use cases for manually curated sources and PDF versions."""
from hashlib import sha256
from dataclasses import replace
from pathlib import PurePath
from uuid import UUID, uuid4
from paperweave.modules.library.errors import DuplicateFileError, DuplicateSourceError, FileTooLargeError, InvalidPdfError, ReferencedFileError, SourceNotFoundError

MAX_PDF_BYTES = 25 * 1024 * 1024

class LibraryService:
    def __init__(self, repository, storage) -> None:
        self.repository, self.storage = repository, storage

    def list_sources(self, owner_id: UUID, project_id: UUID):
        self._require_project(owner_id, project_id)
        return [replace(source, files=tuple(self.repository.list_files(source.id))) for source in self.repository.list_sources(project_id)]

    def create_source(self, owner_id: UUID, project_id: UUID, title: str, authors: str | None, year: int | None, doi: str | None):
        self._require_project(owner_id, project_id)
        normalized_doi = doi.strip().lower().removeprefix("https://doi.org/").removeprefix("http://doi.org/") if doi else None
        normalized_doi = normalized_doi or None
        if normalized_doi:
            duplicate = self.repository.find_doi(project_id, normalized_doi)
            if duplicate: raise DuplicateSourceError(str(duplicate.id))
        else:
            duplicate = self.repository.find_metadata_duplicate(project_id, title, authors, year)
            if duplicate: raise DuplicateSourceError(str(duplicate.id))
        return self.repository.create_source(project_id, title.strip(), authors, year, normalized_doi)

    def upload_pdf(self, owner_id: UUID, project_id: UUID, source_id: UUID, name: str, content_type: str, content: bytes,
                   idempotency_key: str | None = None):
        self._require_project(owner_id, project_id)
        if self.repository.get_source(project_id, source_id) is None: raise SourceNotFoundError
        if len(content) > MAX_PDF_BYTES: raise FileTooLargeError
        if content_type.lower().split(";")[0].strip() != "application/pdf" or not content.startswith(b"%PDF-"): raise InvalidPdfError
        digest = sha256(content).hexdigest()
        raw_idem = (idempotency_key or uuid4().hex).strip()
        if not raw_idem or len(raw_idem) > 119: raise DuplicateFileError("Idempotency-Key must contain 1 to 119 characters")
        idem = f"document:{raw_idem}"
        existing_idempotent = self.repository.find_file_idempotency_artifact(source_id, idem) if hasattr(self.repository, "find_file_idempotency_artifact") else None
        if existing_idempotent is None and self.repository.has_checksum(source_id, digest): raise DuplicateFileError
        basename = PurePath(name.replace("\\", "/")).name
        safe_name = "".join(char for char in basename if char >= " " and char != "\x7f" and char not in '"\\')[:255] or "document.pdf"
        file_id = uuid4()
        key = self.storage.document_key(file_id)
        reserved = hasattr(self.repository, "reserve_file_artifact")
        if reserved:
            artifact = self.repository.reserve_file_artifact(source_id, file_id, safe_name, len(content), digest, key, idem)
            if artifact.domain_parent_id != source_id:
                raise DuplicateFileError("Idempotency-Key was already used for another source")
            if artifact.checksum_sha256 != digest or artifact.original_name != safe_name:
                raise DuplicateFileError("Idempotency-Key was already used for different content")
            file_id, key = artifact.id, artifact.object_key
            if artifact.lifecycle == "active":
                existing = self.repository.get_file(project_id, source_id, file_id)
                if existing is not None:
                    return existing
                raise DuplicateFileError("Idempotency-Key belongs to another completed operation")
            if artifact.lifecycle != "pending_upload":
                raise DuplicateFileError("Idempotency-Key belongs to an inactive artifact")
        elif existing_idempotent is None and self.repository.has_checksum(source_id, digest):
            raise DuplicateFileError
        object_written = False
        try:
            key = self.storage.put(file_id, content)
            object_written = True
            if not self.storage.verify(key, len(content), digest):
                raise OSError("Stored document failed checksum verification")
            return self.repository.create_file(source_id, file_id, safe_name, len(content), digest, key)
        except Exception:
            if object_written and reserved:
                try:
                    resolver = getattr(self.repository, "resolve_file_after_write_error", self.repository.get_file)
                    committed = resolver(project_id, source_id, file_id)
                except Exception:
                    # The commit result is unknown. Keep the uploaded bytes and DB reservation.
                    raise
                if committed is not None:
                    return committed
            if reserved:
                self.repository.mark_artifact_pending_delete(file_id)
            try:
                self.storage.delete(key, backend=self.storage.backend)
                if reserved:
                    self.repository.mark_artifact_deleted(file_id)
            except Exception as cleanup_error:
                if reserved:
                    self.repository.mark_artifact_cleanup_failed(file_id, type(cleanup_error).__name__)
            raise

    def read_file(self, owner_id: UUID, project_id: UUID, source_id: UUID, file_id: UUID):
        self._require_project(owner_id, project_id)
        record = self.repository.get_file(project_id, source_id, file_id)
        if record is None: raise SourceNotFoundError
        return record, self.storage.read(record.storage_key, backend=record.backend)

    def delete_file(self, owner_id: UUID, project_id: UUID, source_id: UUID, file_id: UUID, *, confirmed: bool):
        self._require_project(owner_id, project_id)
        record = self.repository.get_file(project_id, source_id, file_id)
        if record is None: raise SourceNotFoundError
        if not confirmed: raise ValueError("Explicit confirmation is required")
        if self.repository.file_is_referenced(file_id): raise ReferencedFileError
        artifact = self.repository.delete_file(file_id)
        try:
            self.storage.delete(record.storage_key, backend=artifact.backend if artifact else record.backend)
            if artifact is not None:
                self.repository.mark_artifact_deleted(artifact.id)
        except Exception as exc:
            if artifact is not None:
                self.repository.mark_artifact_cleanup_failed(artifact.id, type(exc).__name__)
            raise

    def _require_project(self, owner_id: UUID, project_id: UUID) -> None:
        if self.repository.get_owned_project(owner_id, project_id) is None: raise SourceNotFoundError
