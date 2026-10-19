"""HTTP endpoints for owner-scoped research projects."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from paperweave.api.dependencies import get_current_user, get_project_service
from paperweave.api.schemas.projects import ProjectCreateRequest, ProjectResponse, ProjectUpdateRequest
from paperweave.modules.projects.errors import ProjectValidationError
from paperweave.modules.projects.service import ProjectService

router = APIRouter(prefix="/projects", tags=["projects"])
ProjectServiceDep = Annotated[ProjectService, Depends(get_project_service)]


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
def create_project(
    payload: ProjectCreateRequest,
    service: ProjectServiceDep,
    user=Depends(get_current_user),
) -> ProjectResponse:
    try:
        project = service.create(user.id, payload.name, payload.description)
    except ProjectValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return ProjectResponse.model_validate(project)


@router.get("", response_model=list[ProjectResponse])
def list_projects(
    service: ProjectServiceDep, user=Depends(get_current_user)
) -> list[ProjectResponse]:
    return [ProjectResponse.model_validate(project) for project in service.list(user.id)]


@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(
    project_id: UUID,
    service: ProjectServiceDep,
    user=Depends(get_current_user),
) -> ProjectResponse:
    project = service.get(user.id, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return ProjectResponse.model_validate(project)


@router.put("/{project_id}", response_model=ProjectResponse)
def update_project(
    project_id: UUID,
    payload: ProjectUpdateRequest,
    service: ProjectServiceDep,
    user=Depends(get_current_user),
) -> ProjectResponse:
    try:
        project = service.update(user.id, project_id, payload.name, payload.description)
    except ProjectValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return ProjectResponse.model_validate(project)
