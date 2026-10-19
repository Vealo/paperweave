from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field

class SourceCreateRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    title: str = Field(min_length=1, max_length=500)
    authors: str | None = Field(default=None, max_length=4000)
    year: int | None = Field(default=None, ge=1000, le=2200)
    doi: str | None = Field(default=None, max_length=255)

class SourceFileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    version: int
    original_name: str
    media_type: str
    size_bytes: int
    sha256: str
    created_at: datetime

class SourceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    project_id: UUID
    title: str
    authors: str | None
    year: int | None
    doi: str | None
    metadata_provenance: str
    created_at: datetime
    files: list[SourceFileResponse]
