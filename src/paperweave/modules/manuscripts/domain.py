"""Versioned Tiptap manuscript document."""

from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID


@dataclass(frozen=True)
class Manuscript:
    id: UUID
    project_id: UUID
    content: dict[str, Any]
    version: int
    updated_at: datetime
