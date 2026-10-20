"""Profile image validation and storage orchestration."""

import logging
from uuid import UUID, uuid4

from paperweave.infrastructure.db.identity_repository import IdentityRepository
from paperweave.infrastructure.db.models import UserRecord

MAX_AVATAR_BYTES = 5 * 1024 * 1024
logger = logging.getLogger(__name__)
AVATAR_FORMATS = {
    "image/png": (".png", lambda data: data.startswith(b"\x89PNG\r\n\x1a\n")),
    "image/jpeg": (".jpg", lambda data: data.startswith(b"\xff\xd8\xff")),
    "image/webp": (".webp", lambda data: len(data) >= 12 and data[:4] == b"RIFF" and data[8:12] == b"WEBP"),
}


class AvatarTooLargeError(ValueError):
    """Raised when an uploaded avatar exceeds the local size limit."""


class InvalidAvatarError(ValueError):
    """Raised when avatar media type and image signature are unsupported."""


class ProfileService:
    def __init__(self, repository: IdentityRepository, storage) -> None:
        self.repository = repository
        self.storage = storage

    def update_avatar(self, user_id: UUID, media_type: str, content: bytes) -> UserRecord:
        if len(content) > MAX_AVATAR_BYTES:
            raise AvatarTooLargeError("Avatar exceeds 5 MiB")
        normalized_type = media_type.split(";", 1)[0].strip().lower()
        image_format = AVATAR_FORMATS.get(normalized_type)
        if not content or image_format is None or not image_format[1](content):
            raise InvalidAvatarError("Only valid PNG, JPEG and WebP images are supported")

        extension = image_format[0]
        file_id = uuid4()
        storage_key = self.storage.put_avatar(file_id, content, extension)
        try:
            user, previous_key = self.repository.update_avatar(user_id, storage_key, normalized_type)
        except Exception:
            self.storage.delete(storage_key)
            raise
        if previous_key:
            try:
                self.storage.delete(previous_key)
            except OSError as exc:
                logger.warning(
                    "Не удалось удалить заменённый файл аватара",
                    extra={"event": "profile.avatar.previous_file_cleanup_failed", "event_fields": {"error_type": type(exc).__name__}},
                )
        return user

    def read_avatar(self, storage_key: str | None, media_type: str | None) -> tuple[str, bytes] | None:
        if not storage_key or media_type not in AVATAR_FORMATS:
            return None
        return media_type, self.storage.read(storage_key)

    def remove_avatar(self, user_id: UUID) -> UserRecord:
        user, previous_key = self.repository.clear_avatar(user_id)
        if previous_key:
            try:
                self.storage.delete(previous_key)
            except OSError as exc:
                logger.warning(
                    "Не удалось удалить файл аватара",
                    extra={"event": "profile.avatar.file_cleanup_failed", "event_fields": {"error_type": type(exc).__name__}},
                )
        return user
