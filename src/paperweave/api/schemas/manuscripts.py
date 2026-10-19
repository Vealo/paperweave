"""HTTP schemas for Tiptap manuscript documents."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ManuscriptWriteRequest(BaseModel):
    content: dict[str, Any]
    expected_version: int | None = Field(default=None, ge=1)


class ManuscriptResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    project_id: UUID
    content: dict[str, Any]
    version: int
    updated_at: datetime


class ManuscriptRevisionResponse(BaseModel):
    version: int
    content: dict[str, Any]
    created_at: datetime
