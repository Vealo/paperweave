"""Owner bootstrap, sign-in, sessions and owner-managed local accounts."""

from typing import Annotated
from urllib.parse import quote
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Request, Response, UploadFile, status
from sqlalchemy.exc import IntegrityError

from paperweave.api.dependencies import (
    SESSION_COOKIE, get_current_user, get_identity_repository, require_owner,
)
from paperweave.api.profile_dependencies import get_profile_service
from paperweave.api.schemas.identity import (
    AuthStatusResponse, CredentialsRequest, OwnerSetupRequest, PasswordChangeRequest,
    UserAdminUpdateRequest, UserCreateRequest, UserProfileUpdateRequest, UserResponse, UserSettingsResponse,
    UserSettingsUpdateRequest,
)
from paperweave.infrastructure.db.identity_repository import ABSOLUTE_TIMEOUT, IdentityRepository
from paperweave.modules.identity.profile import AvatarTooLargeError, InvalidAvatarError, MAX_AVATAR_BYTES, ProfileService
from paperweave.modules.identity.security import hash_session_token, new_session_token, verify_password

router = APIRouter(prefix="/auth", tags=["identity"])
IdentityRepositoryDep = Annotated[IdentityRepository, Depends(get_identity_repository)]
ProfileServiceDep = Annotated[ProfileService, Depends(get_profile_service)]


def _user_response(user, request: Request) -> UserResponse:
    avatar_url = None
    if user.avatar_key:
        avatar_url = f"{request.url_for('get_user_avatar', user_id=user.id)}?version={quote(user.avatar_key, safe='')}"
    return UserResponse(
        id=str(user.id), email=user.email, display_name=user.display_name,
        role=user.role, avatar_url=avatar_url, is_active=user.is_active,
    )


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
    payload: OwnerSetupRequest, request: Request, response: Response, repository: IdentityRepositoryDep
) -> UserResponse:
    user = repository.bootstrap_owner(payload.email, payload.display_name.strip(), payload.password)
    if user is None:
        raise HTTPException(status_code=409, detail="Owner setup is already complete")
    _set_session(response, repository, user.id)
    return _user_response(user, request)


@router.post("/login", response_model=UserResponse)
def login(payload: CredentialsRequest, request: Request, response: Response, repository: IdentityRepositoryDep) -> UserResponse:
    user = repository.authenticate(
        payload.email, lambda stored: verify_password(payload.password, stored)
    )
    if user is None:
        raise HTTPException(status_code=401, detail="Email or password is incorrect")
    _set_session(response, repository, user.id)
    return _user_response(user, request)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(request: Request, response: Response, repository: IdentityRepositoryDep) -> Response:
    token = request.cookies.get(SESSION_COOKIE)
    if token:
        repository.revoke_session(hash_session_token(token))
    response.delete_cookie(SESSION_COOKIE, path="/api/v1", httponly=True, samesite="strict")
    response.status_code = status.HTTP_204_NO_CONTENT
    return response


@router.get("/me", response_model=UserResponse)
def current_user(request: Request, user=Depends(get_current_user)) -> UserResponse:
    return _user_response(user, request)


@router.patch("/me", response_model=UserResponse)
def update_my_profile(
    payload: UserProfileUpdateRequest,
    request: Request,
    repository: IdentityRepositoryDep,
    user=Depends(get_current_user),
) -> UserResponse:
    if payload.email is not None and payload.email != user.email:
        if not payload.current_password or not verify_password(payload.current_password, user.password_hash):
            raise HTTPException(status_code=403, detail="Current password is required to change email")
    try:
        updated = repository.update_profile(
            user.id, display_name=payload.display_name, email=payload.email
        )
    except IntegrityError as exc:
        raise HTTPException(status_code=409, detail="An account with this email already exists") from exc
    return _user_response(updated, request)


@router.post("/me/password", status_code=status.HTTP_204_NO_CONTENT)
def change_my_password(
    payload: PasswordChangeRequest,
    request: Request,
    response: Response,
    repository: IdentityRepositoryDep,
    user=Depends(get_current_user),
) -> Response:
    if not verify_password(payload.current_password, user.password_hash):
        raise HTTPException(status_code=403, detail="Current password is incorrect")
    repository.change_password(user.id, payload.new_password)
    response.delete_cookie(SESSION_COOKIE, path="/api/v1", httponly=True, samesite="strict")
    response.status_code = status.HTTP_204_NO_CONTENT
    return response


def _settings_response(settings) -> UserSettingsResponse:
    return UserSettingsResponse(user_id=str(settings.user_id), theme=settings.theme)


@router.get("/me/settings", response_model=UserSettingsResponse)
def get_my_settings(repository: IdentityRepositoryDep, user=Depends(get_current_user)) -> UserSettingsResponse:
    return _settings_response(repository.get_settings(user.id))


@router.patch("/me/settings", response_model=UserSettingsResponse)
def update_my_settings(
    payload: UserSettingsUpdateRequest,
    repository: IdentityRepositoryDep,
    user=Depends(get_current_user),
) -> UserSettingsResponse:
    return _settings_response(repository.update_settings(user.id, theme=payload.theme))


@router.post("/me/avatar", response_model=UserResponse)
async def upload_my_avatar(
    request: Request,
    profile: ProfileServiceDep,
    file: UploadFile = File(...),
    user=Depends(get_current_user),
) -> UserResponse:
    content = await file.read(MAX_AVATAR_BYTES + 1)
    try:
        updated = profile.update_avatar(user.id, file.content_type or "", content)
    except AvatarTooLargeError as exc:
        raise HTTPException(status_code=413, detail="Avatar exceeds 5 MiB") from exc
    except InvalidAvatarError as exc:
        raise HTTPException(status_code=415, detail="Use a valid PNG, JPEG or WebP image") from exc
    return _user_response(updated, request)


@router.delete("/me/avatar", response_model=UserResponse)
def remove_my_avatar(
    request: Request, profile: ProfileServiceDep, user=Depends(get_current_user)
) -> UserResponse:
    return _user_response(profile.remove_avatar(user.id), request)


@router.get("/me/avatar", name="get_my_avatar")
def get_my_avatar(profile: ProfileServiceDep, user=Depends(get_current_user)) -> Response:
    return _avatar_response(profile, user)


def _avatar_response(profile: ProfileService, user) -> Response:
    try:
        avatar = profile.read_avatar(user.avatar_key, user.avatar_media_type)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Profile avatar not found") from exc
    if avatar is None:
        raise HTTPException(status_code=404, detail="Profile avatar not found")
    media_type, content = avatar
    return Response(
        content=content,
        media_type=media_type,
        headers={"Cache-Control": "private, no-store", "X-Content-Type-Options": "nosniff"},
    )


@router.get("/users/{user_id}/avatar", name="get_user_avatar")
def get_user_avatar(
    user_id: UUID,
    profile: ProfileServiceDep,
    repository: IdentityRepositoryDep,
    viewer=Depends(get_current_user),
) -> Response:
    if viewer.id != user_id and viewer.role != "owner":
        raise HTTPException(status_code=404, detail="Profile avatar not found")
    user = repository.get_user(user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="Profile avatar not found")
    return _avatar_response(profile, user)


@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    payload: UserCreateRequest,
    request: Request,
    repository: IdentityRepositoryDep,
    owner=Depends(require_owner),
) -> UserResponse:
    try:
        user = repository.create_member(payload.email, payload.display_name.strip(), payload.password)
    except IntegrityError as exc:
        raise HTTPException(status_code=409, detail="An account with this email already exists") from exc
    return _user_response(user, request)


@router.get("/users", response_model=list[UserResponse])
def list_users(
    request: Request, repository: IdentityRepositoryDep, owner=Depends(require_owner)
) -> list[UserResponse]:
    return [_user_response(user, request) for user in repository.list_users()]


@router.get("/users/{user_id}", response_model=UserResponse)
def get_user(
    user_id: UUID, request: Request, repository: IdentityRepositoryDep, owner=Depends(require_owner)
) -> UserResponse:
    user = repository.get_user(user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return _user_response(user, request)


@router.patch("/users/{user_id}", response_model=UserResponse)
def update_user(
    user_id: UUID,
    payload: UserAdminUpdateRequest,
    request: Request,
    repository: IdentityRepositoryDep,
    owner=Depends(require_owner),
) -> UserResponse:
    target = repository.get_user(user_id)
    if target is None:
        raise HTTPException(status_code=404, detail="User not found")
    if target.role != "member":
        raise HTTPException(status_code=403, detail="Owner profile cannot be changed through user management")
    try:
        updated = repository.update_profile(
            user_id, display_name=payload.display_name, email=payload.email
        )
        if payload.is_active is not None:
            updated = repository.set_user_active(user_id, payload.is_active)
    except IntegrityError as exc:
        raise HTTPException(status_code=409, detail="An account with this email already exists") from exc
    return _user_response(updated, request)


@router.delete("/users/{user_id}", response_model=UserResponse)
def deactivate_user(
    user_id: UUID, request: Request, repository: IdentityRepositoryDep, owner=Depends(require_owner)
) -> UserResponse:
    target = repository.get_user(user_id)
    if target is None:
        raise HTTPException(status_code=404, detail="User not found")
    if target.role != "member":
        raise HTTPException(status_code=403, detail="Owner profile cannot be deactivated")
    return _user_response(repository.set_user_active(user_id, False), request)


@router.post("/users/{user_id}/avatar", response_model=UserResponse)
async def upload_user_avatar(
    user_id: UUID,
    request: Request,
    profile: ProfileServiceDep,
    repository: IdentityRepositoryDep,
    file: UploadFile = File(...),
    owner=Depends(require_owner),
) -> UserResponse:
    user = repository.get_user(user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    content = await file.read(MAX_AVATAR_BYTES + 1)
    try:
        updated = profile.update_avatar(user.id, file.content_type or "", content)
    except AvatarTooLargeError as exc:
        raise HTTPException(status_code=413, detail="Avatar exceeds 5 MiB") from exc
    except InvalidAvatarError as exc:
        raise HTTPException(status_code=415, detail="Use a valid PNG, JPEG or WebP image") from exc
    return _user_response(updated, request)


@router.delete("/users/{user_id}/avatar", response_model=UserResponse)
def remove_user_avatar(
    user_id: UUID,
    request: Request,
    profile: ProfileServiceDep,
    repository: IdentityRepositoryDep,
    owner=Depends(require_owner),
) -> UserResponse:
    target = repository.get_user(user_id)
    if target is None:
        raise HTTPException(status_code=404, detail="User not found")
    if target.role != "member":
        raise HTTPException(status_code=403, detail="Owner avatar cannot be changed through user management")
    return _user_response(profile.remove_avatar(user_id), request)
