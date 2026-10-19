from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest

from paperweave.modules.projects.domain import Project
from paperweave.modules.projects.errors import ProjectValidationError
from paperweave.modules.projects.service import ProjectService


class MemoryProjectRepository:
    def __init__(self) -> None:
        self.projects: list[Project] = []

    def create(self, name: str, description: str | None) -> Project:
        project = Project(uuid4(), name, description, datetime.now(UTC))
        self.projects.append(project)
        return project

    def list(self) -> list[Project]:
        return list(self.projects)

    def get(self, project_id: UUID) -> Project | None:
        return next((project for project in self.projects if project.id == project_id), None)


def test_create_trims_name_and_keeps_duplicate_names_allowed() -> None:
    repository = MemoryProjectRepository()
    service = ProjectService(repository)

    first = service.create("  Pilot  ")
    second = service.create("Pilot")

    assert first.name == second.name == "Pilot"
    assert first.id != second.id
    assert service.get(first.id) == first


@pytest.mark.parametrize(
    ("name", "description"),
    [("   ", None), ("x" * 201, None), ("Valid", "x" * 5001)],
)
def test_create_rejects_invalid_project_values(name: str, description: str | None) -> None:
    service = ProjectService(MemoryProjectRepository())

    with pytest.raises(ProjectValidationError):
        service.create(name, description)
