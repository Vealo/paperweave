from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest

from paperweave.modules.projects.domain import Project
from paperweave.modules.projects.errors import ProjectValidationError
from paperweave.modules.projects.service import ProjectService


class MemoryProjectRepository:
    def __init__(self) -> None:
        self.projects: list[Project] = []

    def create(self, owner_id: UUID, name: str, description: str | None) -> Project:
        project = Project(uuid4(), owner_id, name, description, datetime.now(UTC))
        self.projects.append(project)
        return project

    def list(self, owner_id: UUID) -> list[Project]:
        return [project for project in self.projects if project.owner_id == owner_id]

    def get(self, owner_id: UUID, project_id: UUID) -> Project | None:
        return next(
            (project for project in self.projects if project.id == project_id and project.owner_id == owner_id),
            None,
        )

    def update(self, owner_id: UUID, project_id: UUID, name: str, description: str | None) -> Project | None:
        project = self.get(owner_id, project_id)
        if project is None:
            return None
        updated = Project(project.id, owner_id, name, description, project.created_at)
        self.projects[self.projects.index(project)] = updated
        return updated


def test_create_trims_name_and_keeps_duplicate_names_allowed() -> None:
    repository = MemoryProjectRepository()
    service = ProjectService(repository)
    owner_id = uuid4()

    first = service.create(owner_id, "  Pilot  ")
    second = service.create(owner_id, "Pilot")

    assert first.name == second.name == "Pilot"
    assert first.id != second.id
    assert service.get(owner_id, first.id) == first
    assert service.list(owner_id) == [first, second]


@pytest.mark.parametrize(
    ("name", "description"),
    [("   ", None), ("x" * 201, None), ("Valid", "x" * 5001)],
)
def test_create_rejects_invalid_project_values(name: str, description: str | None) -> None:
    service = ProjectService(MemoryProjectRepository())

    with pytest.raises(ProjectValidationError):
        service.create(uuid4(), name, description)
