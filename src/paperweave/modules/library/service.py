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

    def upload_pdf(self, owner_id: UUID, project_id: UUID, source_id: UUID, name: str, content_type: str, content: bytes):
        self._require_project(owner_id, project_id)
        if self.repository.get_source(project_id, source_id) is None: raise SourceNotFoundError
        if len(content) > MAX_PDF_BYTES: raise FileTooLargeError
        if content_type.lower().split(";")[0].strip() != "application/pdf" or not content.startswith(b"%PDF-"): raise InvalidPdfError
        digest = sha256(content).hexdigest()
        if self.repository.has_checksum(source_id, digest): raise DuplicateFileError
        basename = PurePath(name.replace("\\", "/")).name
        safe_name = "".join(char for char in basename if char >= " " and char != "\x7f" and char not in '"\\')[:255] or "document.pdf"
        file_id = uuid4()
        key = self.storage.put(file_id, content)
        try: return self.repository.create_file(source_id, file_id, safe_name, len(content), digest, key)
        except Exception:
            self.storage.delete(key)
            raise

    def read_file(self, owner_id: UUID, project_id: UUID, source_id: UUID, file_id: UUID):
        self._require_project(owner_id, project_id)
        record = self.repository.get_file(project_id, source_id, file_id)
        if record is None: raise SourceNotFoundError
        return record, self.storage.read(record.storage_key)

    def delete_file(self, owner_id: UUID, project_id: UUID, source_id: UUID, file_id: UUID, *, confirmed: bool):
        self._require_project(owner_id, project_id)
        record = self.repository.get_file(project_id, source_id, file_id)
        if record is None: raise SourceNotFoundError
        if not confirmed: raise ValueError("Explicit confirmation is required")
        if self.repository.file_is_referenced(file_id): raise ReferencedFileError
        self.repository.delete_file(file_id)
        self.storage.delete(record.storage_key)

    def _require_project(self, owner_id: UUID, project_id: UUID) -> None:
        if self.repository.get_owned_project(owner_id, project_id) is None: raise SourceNotFoundError
