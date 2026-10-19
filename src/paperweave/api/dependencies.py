"""Request-scoped application service and identity dependencies."""

from collections.abc import Iterator
import os
from pathlib import Path

from fastapi import Depends, HTTPException, Request, status
from paperweave.infrastructure.db.identity_repository import IdentityRepository
from paperweave.infrastructure.db.project_repository import SqlAlchemyProjectRepository
from paperweave.infrastructure.db.manuscript_repository import SqlAlchemyManuscriptRepository
from paperweave.modules.identity.security import hash_session_token
from paperweave.modules.projects.service import ProjectService
from paperweave.modules.manuscripts.service import ManuscriptService
from paperweave.infrastructure.db.library_repository import SqlAlchemyLibraryRepository
from paperweave.infrastructure.storage.local import LocalFileStorage
from paperweave.modules.library.service import LibraryService

SESSION_COOKIE = "paperweave_session"


def get_identity_repository(request: Request) -> Iterator[IdentityRepository]:
    with request.app.state.session_factory() as session:
        yield IdentityRepository(session)


def get_current_user(request: Request):
    token = request.cookies.get(SESSION_COOKIE)
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    with request.app.state.session_factory() as session:
        user = IdentityRepository(session).resolve_session(hash_session_token(token))
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session expired")
    return user


def require_owner(user=Depends(get_current_user)):
    if user.role != "owner":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Owner access required")
    return user


def get_project_service(request: Request) -> Iterator[ProjectService]:
    with request.app.state.session_factory() as session:
        yield ProjectService(SqlAlchemyProjectRepository(session))


def get_manuscript_service(request: Request) -> Iterator[ManuscriptService]:
    with request.app.state.session_factory() as session:
        yield ManuscriptService(SqlAlchemyManuscriptRepository(session))


def get_library_service(request: Request) -> Iterator[LibraryService]:
    with request.app.state.session_factory() as session:
        root = Path(os.getenv("PW_FILE_STORAGE", "/app/data/files"))
        yield LibraryService(SqlAlchemyLibraryRepository(session), LocalFileStorage(root))
