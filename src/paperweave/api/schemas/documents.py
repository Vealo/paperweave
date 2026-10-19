"""HTTP response shapes for document extraction and passages."""
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ExtractionRunResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    file_id: UUID
    processor: str
    processor_version: str
    status: str
    page_count: int
    error: str | None
    created_at: datetime
    completed_at: datetime | None


class SourcePassageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    run_id: UUID
    file_id: UUID
    page_number: int
    text: str
    review_state: str
    created_at: datetime
