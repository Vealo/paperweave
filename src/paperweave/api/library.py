"""Owner-scoped project source library endpoints."""
from typing import Annotated
from uuid import UUID
from urllib.parse import quote
from fastapi import APIRouter, Depends, File, HTTPException, Response, UploadFile, status
from paperweave.api.dependencies import get_current_user, get_library_service
from paperweave.api.schemas.library import SourceCreateRequest, SourceResponse, SourceFileResponse
from paperweave.modules.library.errors import DuplicateFileError, DuplicateSourceError, FileTooLargeError, InvalidPdfError, ReferencedFileError, SourceNotFoundError
from paperweave.modules.library.service import LibraryService, MAX_PDF_BYTES

router = APIRouter(prefix="/projects/{project_id}/sources", tags=["library"])
Service = Annotated[LibraryService, Depends(get_library_service)]


def render_source(source, files=None):
    return SourceResponse(id=source.id, project_id=source.project_id, title=source.title, authors=source.authors, year=source.year, doi=source.doi, metadata_provenance=source.metadata_provenance, created_at=source.created_at, files=[SourceFileResponse.model_validate(f) for f in (files if files is not None else source.files)])

@router.get("", response_model=list[SourceResponse])
def list_sources(project_id: UUID, service: Service, user=Depends(get_current_user)):
    try: return [render_source(row) for row in service.list_sources(user.id, project_id)]
    except SourceNotFoundError as exc: raise HTTPException(404, "Project not found") from exc

@router.post("", response_model=SourceResponse, status_code=status.HTTP_201_CREATED)
def create_source(project_id: UUID, payload: SourceCreateRequest, service: Service, user=Depends(get_current_user)):
    try: return render_source(service.create_source(user.id, project_id, payload.title, payload.authors, payload.year, payload.doi))
    except DuplicateSourceError as exc: raise HTTPException(409, {"message": str(exc), "existing_source_id": exc.source_id}) from exc
    except SourceNotFoundError as exc: raise HTTPException(404, "Project not found") from exc

@router.post("/{source_id}/files", response_model=SourceFileResponse, status_code=201)
async def upload_source_file(project_id: UUID, source_id: UUID, service: Service, file: UploadFile = File(...), user=Depends(get_current_user)):
    content = await file.read(MAX_PDF_BYTES + 1)
    try: record = service.upload_pdf(user.id, project_id, source_id, file.filename or "document.pdf", file.content_type or "", content)
    except SourceNotFoundError as exc: raise HTTPException(404, "Source not found") from exc
    except FileTooLargeError as exc: raise HTTPException(413, "PDF exceeds 25 MiB") from exc
    except InvalidPdfError as exc: raise HTTPException(415, "Only valid PDF files are supported") from exc
    except DuplicateFileError as exc: raise HTTPException(409, "This file version already exists") from exc
    return SourceFileResponse.model_validate(record)

@router.get("/{source_id}/files/{file_id}")
def download_source_file(project_id: UUID, source_id: UUID, file_id: UUID, service: Service, user=Depends(get_current_user)):
    try: record, content = service.read_file(user.id, project_id, source_id, file_id)
    except SourceNotFoundError as exc: raise HTTPException(404, "File not found") from exc
    encoded_name = quote(record.original_name, safe="")
    return Response(content, media_type="application/pdf", headers={"Content-Disposition": f"attachment; filename*=UTF-8''{encoded_name}", "X-Content-Type-Options": "nosniff"})

@router.delete("/{source_id}/files/{file_id}", status_code=204)
def delete_source_file(project_id: UUID, source_id: UUID, file_id: UUID, confirmed: bool, service: Service, user=Depends(get_current_user)):
    try: service.delete_file(user.id, project_id, source_id, file_id, confirmed=confirmed)
    except SourceNotFoundError as exc: raise HTTPException(404, "File not found") from exc
    except ReferencedFileError as exc: raise HTTPException(409, "File is referenced and must be retained") from exc
    except ValueError as exc: raise HTTPException(400, str(exc)) from exc
    return Response(status_code=204)
