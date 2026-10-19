from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class AIProposalCreate(BaseModel):
    expected_version: int = Field(ge=1)
    target_position: int = Field(ge=0)
    selected_text: str = Field(min_length=1, max_length=4000)
    instruction: str = Field(min_length=1, max_length=1000)
    idempotency_key: str = Field(min_length=8, max_length=128)


class AIProposalDecision(BaseModel):
    decision: str
    note: str | None = Field(default=None, max_length=2000)


class AIProposalResponse(BaseModel):
    id: UUID
    project_id: UUID
    manuscript_id: UUID
    target_version: int
    target_position: int
    context_manifest: dict[str, Any]
    suggestion: str | None
    provider: str
    model: str
    status: str
    reviewer_id: UUID | None
    decision_at: datetime | None
    decision_note: str | None
    created_at: datetime
    error_code: str | None = None
    updated_at: datetime
    manuscript: dict[str, Any] | None = None
