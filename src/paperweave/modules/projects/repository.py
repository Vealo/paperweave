"""Persistence port for project use cases."""

from typing import Protocol
from uuid import UUID

from paperweave.modules.projects.domain import Project


class ProjectRepository(Protocol):
    def create(self, name: str, description: str | None) -> Project: ...

    def list(self) -> list[Project]: ...

    def get(self, project_id: UUID) -> Project | None: ...
