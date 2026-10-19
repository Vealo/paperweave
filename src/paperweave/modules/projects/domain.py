"""Transport-independent research project entity."""

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True, slots=True)
class Project:
    id: UUID
    name: str
    description: str | None
    created_at: datetime
