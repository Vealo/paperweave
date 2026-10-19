"""HTTP contracts for manuscript claims and reviewed evidence."""
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field


class ClaimCreate(BaseModel):
    text: str = Field(min_length=1, max_length=4000)
    block_position: int = Field(ge=0)


class ClaimUpdate(BaseModel):
    text: str = Field(min_length=1, max_length=4000)
    expected_version: int = Field(ge=1)


class EvidenceLinkCreate(BaseModel):
    passage_id: UUID
    relation: str
    rationale: str | None = Field(default=None, max_length=4000)


class ReviewRequest(BaseModel):
    decision: str
    note: str | None = Field(default=None, max_length=4000)


class EvidenceLinkResponse(BaseModel):
    id: UUID
    claim_id: UUID
    claim_version: int
    passage_id: UUID
    passage_file_id: UUID
    version: int
    passage_page: int | None
    passage_text: str | None
    source_title: str
    relation: str
    rationale: str | None
    review_state: str
    manuscript_version: int
    reviewer_id: UUID | None
    decision: str | None
    decided_at: datetime | None
    note: str | None


class ClaimResponse(BaseModel):
    id: UUID
    manuscript_id: UUID
    block_position: int
    text: str
    version: int
    manuscript_version: int
    links: list[EvidenceLinkResponse]
