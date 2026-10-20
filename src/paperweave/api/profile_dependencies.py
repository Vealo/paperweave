"""Dependencies used by the profile API and its file operations."""

from collections.abc import Iterator
from fastapi import Request

from paperweave.infrastructure.db.identity_repository import IdentityRepository
from paperweave.infrastructure.storage.factory import create_storage
from paperweave.modules.identity.profile import ProfileService


def get_profile_service(request: Request) -> Iterator[ProfileService]:
    with request.app.state.session_factory() as session:
        repository = IdentityRepository(session)
        yield ProfileService(repository, create_storage(request.app.state.config))
