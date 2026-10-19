"""Owner bootstrap, sign-in, sessions and owner-managed local accounts."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.exc import IntegrityError

from paperweave.api.dependencies import (
    SESSION_COOKIE, get_current_user, get_identity_repository, require_owner,
)
from paperweave.api.schemas.identity import (
    AuthStatusResponse, CredentialsRequest, OwnerSetupRequest, UserCreateRequest, UserResponse,
)
from paperweave.infrastructure.db.identity_repository import ABSOLUTE_TIMEOUT, IdentityRepository
from paperweave.modules.identity.security import hash_session_token, new_session_token, verify_password

router = APIRouter(prefix="/auth", tags=["identity"])
IdentityRepositoryDep = Annotated[IdentityRepository, Depends(get_identity_repository)]


def _set_session(response: Response, repository: IdentityRepository, user_id) -> None:
    token = new_session_token()
    repository.create_session(user_id, hash_session_token(token))
    response.set_cookie(
        SESSION_COOKIE, token, httponly=True, secure=False, samesite="strict",
        max_age=int(ABSOLUTE_TIMEOUT.total_seconds()), path="/api/v1",
    )


@router.get("/status", response_model=AuthStatusResponse)
def auth_status(repository: IdentityRepositoryDep) -> AuthStatusResponse:
    return AuthStatusResponse(owner_exists=repository.owner_exists())


@router.post("/bootstrap", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def bootstrap_owner(
    payload: OwnerSetupRequest, response: Response, repository: IdentityRepositoryDep
) -> UserResponse:
    user = repository.bootstrap_owner(payload.email, payload.display_name.strip(), payload.password)
    if user is None:
        raise HTTPException(status_code=409, detail="Owner setup is already complete")
    _set_session(response, repository, user.id)
    return UserResponse(id=str(user.id), email=user.email, display_name=user.display_name, role=user.role)


@router.post("/login", response_model=UserResponse)
def login(payload: CredentialsRequest, response: Response, repository: IdentityRepositoryDep) -> UserResponse:
    user = repository.authenticate(
        payload.email, lambda stored: verify_password(payload.password, stored)
    )
    if user is None:
        raise HTTPException(status_code=401, detail="Email or password is incorrect")
    _set_session(response, repository, user.id)
    return UserResponse(id=str(user.id), email=user.email, display_name=user.display_name, role=user.role)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(request: Request, response: Response, repository: IdentityRepositoryDep) -> Response:
    token = request.cookies.get(SESSION_COOKIE)
    if token:
        repository.revoke_session(hash_session_token(token))
    response.delete_cookie(SESSION_COOKIE, path="/api/v1", httponly=True, samesite="strict")
    response.status_code = status.HTTP_204_NO_CONTENT
    return response


@router.get("/me", response_model=UserResponse)
def current_user(user=Depends(get_current_user)) -> UserResponse:
    return UserResponse(id=str(user.id), email=user.email, display_name=user.display_name, role=user.role)


@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    payload: UserCreateRequest,
    repository: IdentityRepositoryDep,
    owner=Depends(require_owner),
) -> UserResponse:
    try:
        user = repository.create_member(payload.email, payload.display_name.strip(), payload.password)
    except IntegrityError as exc:
        raise HTTPException(status_code=409, detail="An account with this email already exists") from exc
    return UserResponse(id=str(user.id), email=user.email, display_name=user.display_name, role=user.role)
