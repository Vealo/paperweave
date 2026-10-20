"""Profile image validation and storage orchestration."""

import logging
import warnings
from io import BytesIO
from uuid import UUID, uuid4

from PIL import Image, ImageOps, UnidentifiedImageError

from paperweave.infrastructure.db.identity_repository import IdentityRepository
from paperweave.infrastructure.db.models import UserRecord

MAX_AVATAR_BYTES = 5 * 1024 * 1024
MAX_AVATAR_DIMENSION = 8192
MAX_AVATAR_PIXELS = 20_000_000
NORMALIZED_AVATAR_MEDIA_TYPE = "image/png"
logger = logging.getLogger(__name__)
AVATAR_FORMATS = {"PNG", "JPEG", "WEBP"}
AVATAR_MEDIA_TYPES = {"image/png", "image/jpeg", "image/webp"}


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
        # The upload's MIME header is untrusted; Pillow identifies the format from the file data.
        normalized_content = self._normalize_avatar(content)
        current_user = self.repository.get_user(user_id)
        if current_user is None:
            raise LookupError("User not found")
        previous_key_before_write = current_user.avatar_key
        file_id = uuid4()
        storage_key = self.storage.put_avatar(file_id, normalized_content, ".png")
        try:
            user, previous_key = self.repository.update_avatar(
                user_id, storage_key, NORMALIZED_AVATAR_MEDIA_TYPE
            )
        except Exception as write_error:
            try:
                recovered_user, active_key = self.repository.resolve_avatar_after_write_error(
                    user_id
                )
            except Exception as recovery_error:
                logger.error(
                    "Не удалось проверить ссылку на аватар после ошибки записи профиля",
                    extra={
                        "event": "profile.avatar.commit_outcome_unknown",
                        "event_fields": {"error_type": type(recovery_error).__name__},
                    },
                )
                # Keep the candidate: the database may have committed its reference.
                raise write_error from recovery_error
            if active_key == storage_key and recovered_user is not None:
                if previous_key_before_write:
                    try:
                        self.storage.delete(previous_key_before_write)
                    except OSError as cleanup_error:
                        logger.warning(
                            "Не удалось удалить заменённый файл аватара",
                            extra={
                                "event": "profile.avatar.previous_file_cleanup_failed",
                                "event_fields": {"error_type": type(cleanup_error).__name__},
                            },
                        )
                return recovered_user
            try:
                self.storage.delete(storage_key)
            except OSError as cleanup_error:
                logger.error(
                    "Не удалось удалить новый файл аватара после ошибки записи профиля",
                    extra={
                        "event": "profile.avatar.rollback_cleanup_failed",
                        "event_fields": {"error_type": type(cleanup_error).__name__},
                    },
                )
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

    @staticmethod
    def _normalize_avatar(content: bytes) -> bytes:
        if not content:
            raise InvalidAvatarError("Only valid PNG, JPEG and WebP images are supported")
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("error", Image.DecompressionBombWarning)
                with Image.open(BytesIO(content)) as source:
                    if source.format not in AVATAR_FORMATS:
                        raise InvalidAvatarError(
                            "Only valid PNG, JPEG and WebP images are supported"
                        )
                    width, height = source.size
                    if (
                        width <= 0
                        or height <= 0
                        or width > MAX_AVATAR_DIMENSION
                        or height > MAX_AVATAR_DIMENSION
                        or width * height > MAX_AVATAR_PIXELS
                    ):
                        raise AvatarTooLargeError("Avatar dimensions exceed the allowed limit")
                    source.load()
                    oriented = ImageOps.exif_transpose(source)
                    mode = "RGBA" if "A" in oriented.getbands() else "RGB"
                    clean_image = oriented.convert(mode)
                    output = BytesIO()
                    clean_image.save(
                        output,
                        format="PNG",
                        optimize=True,
                        exif=b"",
                        icc_profile=None,
                    )
                    return output.getvalue()
        except (AvatarTooLargeError, InvalidAvatarError):
            raise
        except (
            UnidentifiedImageError,
            OSError,
            SyntaxError,
            ValueError,
            Image.DecompressionBombError,
            Image.DecompressionBombWarning,
        ) as exc:
            raise InvalidAvatarError(
                "Image data is invalid or could not be safely decoded"
            ) from exc

    def read_avatar(self, storage_key: str | None, media_type: str | None) -> tuple[str, bytes] | None:
        if not storage_key or media_type not in AVATAR_MEDIA_TYPES:
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
