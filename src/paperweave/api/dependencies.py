"""Request-scoped application service and identity dependencies."""

from collections.abc import Iterator

from fastapi import Depends, HTTPException, Request, status
from paperweave.infrastructure.db.identity_repository import IdentityRepository
from paperweave.infrastructure.db.project_repository import SqlAlchemyProjectRepository
from paperweave.modules.identity.security import hash_session_token
from paperweave.modules.projects.service import ProjectService

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
