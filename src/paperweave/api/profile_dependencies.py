"""Dependencies used by the profile API and its file operations."""

from collections.abc import Iterator
import os
from pathlib import Path

from fastapi import Request

from paperweave.infrastructure.db.identity_repository import IdentityRepository
from paperweave.infrastructure.storage.local import LocalFileStorage
from paperweave.modules.identity.profile import ProfileService


def get_profile_service(request: Request) -> Iterator[ProfileService]:
    with request.app.state.session_factory() as session:
        repository = IdentityRepository(session)
        root = Path(os.getenv("PW_FILE_STORAGE", "/app/data/files"))
        yield ProfileService(repository, LocalFileStorage(root))
