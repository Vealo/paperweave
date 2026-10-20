"""Application service for explicit, repeatable source-file extraction."""
from uuid import UUID

from paperweave.integrations.documents.pdf_text import PROCESSOR, PROCESSOR_VERSION, extract_pdf_pages
from paperweave.modules.library.errors import SourceNotFoundError


class DocumentService:
    def __init__(self, repository, storage) -> None:
        self.repository, self.storage = repository, storage

    def extract(self, owner_id: UUID, project_id: UUID, source_id: UUID, file_id: UUID):
        file = self.repository.get_owned_file(owner_id, project_id, source_id, file_id)
        if file is None:
            raise SourceNotFoundError
        run = self.repository.create_run(file.id, PROCESSOR, PROCESSOR_VERSION)
        try:
            pages = extract_pdf_pages(self.storage.read(file.storage_key, backend=file.artifact.backend if file.artifact else "local"))
        except Exception as exc:
            return self.repository.fail_run(run.id, f"PDF extraction failed: {type(exc).__name__}")
        failed = [page for page in pages if page.error]
        nonempty = [page for page in pages if page.text]
        if failed and nonempty:
            status, error = "partial", "; ".join(page.error for page in failed)
        elif failed:
            status, error = "failed", "; ".join(page.error for page in failed)
        elif nonempty:
            status, error = "complete", None
        else:
            status, error = "empty", None
        return self.repository.complete_run(run.id, pages, status, error)

    def list_runs(self, owner_id: UUID, project_id: UUID, source_id: UUID, file_id: UUID):
        self._require_file(owner_id, project_id, source_id, file_id)
        return self.repository.list_runs(file_id)

    def list_passages(self, owner_id: UUID, project_id: UUID, source_id: UUID, file_id: UUID):
        self._require_file(owner_id, project_id, source_id, file_id)
        return self.repository.list_passages(file_id)

    def _require_file(self, owner_id, project_id, source_id, file_id):
        if self.repository.get_owned_file(owner_id, project_id, source_id, file_id) is None:
            raise SourceNotFoundError
