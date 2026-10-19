"""Project application use cases and invariant validation."""

from uuid import UUID

from paperweave.modules.projects.domain import Project
from paperweave.modules.projects.errors import ProjectValidationError
from paperweave.modules.projects.repository import ProjectRepository


class ProjectService:
    def __init__(self, repository: ProjectRepository) -> None:
        self._repository = repository

    def create(self, owner_id: UUID, name: str, description: str | None = None) -> Project:
        normalized_name = name.strip()
        if not 1 <= len(normalized_name) <= 200:
            raise ProjectValidationError("name must contain 1 to 200 characters after trimming")
        if description is not None and len(description) > 5000:
            raise ProjectValidationError("description must contain at most 5000 characters")
        return self._repository.create(owner_id, normalized_name, description)

    def list(self, owner_id: UUID) -> list[Project]:
        return self._repository.list(owner_id)

    def get(self, owner_id: UUID, project_id: UUID) -> Project | None:
        return self._repository.get(owner_id, project_id)

    def update(
        self, owner_id: UUID, project_id: UUID, name: str, description: str | None
    ) -> Project | None:
        normalized_name = name.strip()
        if not 1 <= len(normalized_name) <= 200:
            raise ProjectValidationError("name must contain 1 to 200 characters after trimming")
        if description is not None and len(description) > 5000:
            raise ProjectValidationError("description must contain at most 5000 characters")
        return self._repository.update(owner_id, project_id, normalized_name, description)
