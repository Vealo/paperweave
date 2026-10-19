"""Owner-scoped manuscript API."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status

from paperweave.api.dependencies import get_current_user, get_library_service, get_manuscript_service, get_project_service
from paperweave.api.schemas.manuscripts import ManuscriptResponse, ManuscriptRevisionResponse, ManuscriptWriteRequest
from paperweave.modules.manuscripts.errors import ManuscriptAlreadyExistsError, ManuscriptConflictError
from paperweave.modules.manuscripts.service import ManuscriptService
from paperweave.modules.projects.service import ProjectService
from paperweave.modules.library.errors import SourceNotFoundError
from paperweave.modules.library.service import LibraryService
from paperweave.modules.manuscripts.docx_export import render_docx

router = APIRouter(prefix="/projects/{project_id}/manuscript", tags=["manuscripts"])
ManuscriptServiceDep = Annotated[ManuscriptService, Depends(get_manuscript_service)]
ProjectServiceDep = Annotated[ProjectService, Depends(get_project_service)]
LibraryServiceDep = Annotated[LibraryService, Depends(get_library_service)]


def _require_project(projects: ProjectService, user_id: UUID, project_id: UUID) -> None:
    if projects.get(user_id, project_id) is None:
        raise HTTPException(status_code=404, detail="Project not found")


@router.get("/versions", response_model=list[ManuscriptRevisionResponse])
def list_manuscript_versions(
    project_id: UUID,
    service: ManuscriptServiceDep,
    projects: ProjectServiceDep,
    user=Depends(get_current_user),
):
    _require_project(projects, user.id, project_id)
    versions = service.list_versions(project_id)
    if versions is None:
        raise HTTPException(status_code=404, detail="Manuscript not found")
    return versions


@router.get("/versions/{version}", response_model=ManuscriptRevisionResponse)
def get_manuscript_version(
    project_id: UUID,
    version: int,
    service: ManuscriptServiceDep,
    projects: ProjectServiceDep,
    user=Depends(get_current_user),
):
    _require_project(projects, user.id, project_id)
    revision = service.get_version(project_id, version)
    if revision is None:
        raise HTTPException(status_code=404, detail="Manuscript version not found")
    return revision


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


@router.get("/export.docx")
def export_manuscript_docx(
    project_id: UUID,
    service: ManuscriptServiceDep,
    projects: ProjectServiceDep,
    library: LibraryServiceDep,
    user=Depends(get_current_user),
):
    _require_project(projects, user.id, project_id)
    manuscript = service.get(project_id)
    if manuscript is None:
        raise HTTPException(status_code=404, detail="Manuscript not found")
    try:
        sources = library.list_sources(user.id, project_id)
        document = render_docx(manuscript.content, sources)
    except SourceNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Project not found") from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return Response(
        document,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": 'attachment; filename="paperweave-manuscript.docx"', "X-Content-Type-Options": "nosniff"},
    )
