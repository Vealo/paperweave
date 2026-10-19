"""Owner-scoped document extraction endpoints."""
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from paperweave.api.dependencies import get_current_user, get_document_service
from paperweave.api.schemas.documents import ExtractionRunResponse, SourcePassageResponse
from paperweave.modules.documents.service import DocumentService
from paperweave.modules.library.errors import SourceNotFoundError

router = APIRouter(prefix="/projects/{project_id}/sources/{source_id}/files/{file_id}", tags=["documents"])
Service = Annotated[DocumentService, Depends(get_document_service)]


@router.post("/extractions", response_model=ExtractionRunResponse, status_code=status.HTTP_201_CREATED)
def extract_file(project_id: UUID, source_id: UUID, file_id: UUID, service: Service,
                 user=Depends(get_current_user)):
    try:
        return service.extract(user.id, project_id, source_id, file_id)
    except SourceNotFoundError as exc:
        raise HTTPException(404, "File not found") from exc


@router.get("/extractions", response_model=list[ExtractionRunResponse])
def list_extractions(project_id: UUID, source_id: UUID, file_id: UUID, service: Service,
                     user=Depends(get_current_user)):
    try:
        return service.list_runs(user.id, project_id, source_id, file_id)
    except SourceNotFoundError as exc:
        raise HTTPException(404, "File not found") from exc


@router.get("/passages", response_model=list[SourcePassageResponse])
def list_passages(project_id: UUID, source_id: UUID, file_id: UUID, service: Service,
                  user=Depends(get_current_user)):
    try:
        return service.list_passages(user.id, project_id, source_id, file_id)
    except SourceNotFoundError as exc:
        raise HTTPException(404, "File not found") from exc
