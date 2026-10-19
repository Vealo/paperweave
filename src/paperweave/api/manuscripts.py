"""Owner-scoped manuscript API."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from paperweave.api.dependencies import get_current_user, get_manuscript_service, get_project_service
from paperweave.api.schemas.manuscripts import ManuscriptResponse, ManuscriptWriteRequest
from paperweave.modules.manuscripts.errors import ManuscriptAlreadyExistsError, ManuscriptConflictError
from paperweave.modules.manuscripts.service import ManuscriptService
from paperweave.modules.projects.service import ProjectService

router = APIRouter(prefix="/projects/{project_id}/manuscript", tags=["manuscripts"])
ManuscriptServiceDep = Annotated[ManuscriptService, Depends(get_manuscript_service)]
ProjectServiceDep = Annotated[ProjectService, Depends(get_project_service)]


def _require_project(projects: ProjectService, user_id: UUID, project_id: UUID) -> None:
    if projects.get(user_id, project_id) is None:
        raise HTTPException(status_code=404, detail="Project not found")


@router.get("", response_model=ManuscriptResponse)
def get_manuscript(
    project_id: UUID,
    service: ManuscriptServiceDep,
    projects: ProjectServiceDep,
    user=Depends(get_current_user),
) -> ManuscriptResponse:
    _require_project(projects, user.id, project_id)
    manuscript = service.get(project_id)
    if manuscript is None:
        raise HTTPException(status_code=404, detail="Manuscript not found")
    return ManuscriptResponse.model_validate(manuscript)


@router.post("", response_model=ManuscriptResponse, status_code=status.HTTP_201_CREATED)
def create_manuscript(
    payload: ManuscriptWriteRequest,
    project_id: UUID,
    service: ManuscriptServiceDep,
    projects: ProjectServiceDep,
    user=Depends(get_current_user),
) -> ManuscriptResponse:
    _require_project(projects, user.id, project_id)
    if payload.expected_version is not None:
        raise HTTPException(status_code=422, detail="expected_version is only valid when updating")
    try:
        manuscript = service.create(project_id, payload.content)
    except ManuscriptAlreadyExistsError as exc:
        raise HTTPException(status_code=409, detail="Project already has a manuscript") from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return ManuscriptResponse.model_validate(manuscript)


@router.put("", response_model=ManuscriptResponse)
def update_manuscript(
    payload: ManuscriptWriteRequest,
    project_id: UUID,
    service: ManuscriptServiceDep,
    projects: ProjectServiceDep,
    user=Depends(get_current_user),
) -> ManuscriptResponse:
    _require_project(projects, user.id, project_id)
    if payload.expected_version is None:
        raise HTTPException(status_code=422, detail="expected_version is required")
    try:
        manuscript = service.update(project_id, payload.expected_version, payload.content)
    except ManuscriptConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return ManuscriptResponse.model_validate(manuscript)
