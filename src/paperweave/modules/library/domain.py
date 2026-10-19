"""Domain records for user-curated bibliographic sources."""
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

@dataclass(frozen=True)
class Source:
    id: UUID
    project_id: UUID
    title: str
    authors: str | None
    year: int | None
    doi: str | None
    metadata_provenance: str
    created_at: datetime
    files: tuple["SourceFile", ...] = ()

@dataclass(frozen=True)
class SourceFile:
    id: UUID
    source_id: UUID
    version: int
    original_name: str
    media_type: str
    size_bytes: int
    sha256: str
    created_at: datetime
    storage_key: str
