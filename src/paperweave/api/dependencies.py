"""Request-scoped application service construction."""

from collections.abc import Iterator

from fastapi import Request
from paperweave.infrastructure.db.project_repository import SqlAlchemyProjectRepository
from paperweave.modules.projects.service import ProjectService


def get_project_service(request: Request) -> Iterator[ProjectService]:
    with request.app.state.session_factory() as session:
        yield ProjectService(SqlAlchemyProjectRepository(session))
