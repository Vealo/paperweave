"""Persistence port for project use cases."""

from typing import Protocol
from uuid import UUID

from paperweave.modules.projects.domain import Project


class ProjectRepository(Protocol):
    def create(self, owner_id: UUID, name: str, description: str | None) -> Project: ...

    def list(self, owner_id: UUID) -> list[Project]: ...

    def get(self, owner_id: UUID, project_id: UUID) -> Project | None: ...

    def update(
        self, owner_id: UUID, project_id: UUID, name: str, description: str | None
    ) -> Project | None: ...
