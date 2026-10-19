"""Domain records returned by the document extraction use cases."""
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class ExtractionRun:
    id: UUID
    file_id: UUID
    processor: str
    processor_version: str
    status: str
    page_count: int
    error: str | None
    created_at: datetime
    completed_at: datetime | None


@dataclass(frozen=True)
class SourcePassage:
    id: UUID
    run_id: UUID
    file_id: UUID
    page_number: int
    text: str
    review_state: str
    created_at: datetime
