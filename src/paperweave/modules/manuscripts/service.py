"""Manuscript use cases."""

from typing import Any
from uuid import UUID

from paperweave.modules.manuscripts.domain import Manuscript
from paperweave.modules.manuscripts.errors import ManuscriptConflictError
from paperweave.modules.manuscripts.repository import ManuscriptRepository


def validate_document(content: dict[str, Any]) -> dict[str, Any]:
    if content.get("type") != "doc":
        raise ValueError("Document root must be a Tiptap doc node.")
    if "content" in content and not isinstance(content["content"], list):
        raise ValueError("Document content must be an ordered list of nodes.")
    return content


class ManuscriptService:
    def __init__(self, repository: ManuscriptRepository) -> None:
        self._repository = repository

    def get(self, project_id: UUID) -> Manuscript | None:
        return self._repository.get(project_id)

    def create(self, project_id: UUID, content: dict[str, Any]) -> Manuscript:
        return self._repository.create(project_id, validate_document(content))

    def update(self, project_id: UUID, expected_version: int, content: dict[str, Any]) -> Manuscript:
        updated = self._repository.update(project_id, expected_version, validate_document(content))
        if updated is None:
            current = self._repository.get(project_id)
            raise ManuscriptConflictError(current.version if current else None)
        return updated
