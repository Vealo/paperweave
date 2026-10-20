"""Profile image validation and storage orchestration."""

import logging
import warnings
from hashlib import sha256
from pathlib import PurePath
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


class IdempotencyConflictError(ValueError):
    """An idempotency key was reused for a different or completed operation."""


class ProfileService:
    def __init__(self, repository: IdentityRepository, storage) -> None:
        self.repository = repository
        self.storage = storage

    def update_avatar(self, user_id: UUID, media_type: str, content: bytes, idempotency_key: str | None = None) -> UserRecord:
        if len(content) > MAX_AVATAR_BYTES:
            raise AvatarTooLargeError("Avatar exceeds 5 MiB")
        # The upload's MIME header is untrusted; Pillow identifies the format from the file data.
        normalized_content = self._normalize_avatar(content)
        current_user = self.repository.get_user(user_id)
        if current_user is None:
            raise LookupError("User not found")
        previous_key_before_write = current_user.avatar_key
        file_id = uuid4()
        digest = sha256(normalized_content).hexdigest()
        if hasattr(self.repository, "reserve_avatar_artifact"):
            idem = self._idempotency_key(idempotency_key, "avatar")
            storage_key = self.storage.avatar_key(file_id, ".png")
            artifact = self.repository.reserve_avatar_artifact(
                user_id, file_id, self.storage.backend, self.storage.bucket, storage_key,
                len(normalized_content), digest, NORMALIZED_AVATAR_MEDIA_TYPE, idem,
            )
            if artifact.checksum_sha256 != digest or artifact.kind != "avatar":
                raise IdempotencyConflictError("Idempotency key was already used for different content")
            file_id, storage_key = artifact.id, artifact.object_key
            if artifact.lifecycle == "active":
                user = self.repository.get_user(user_id)
                if user is not None and user.avatar_artifact_id == artifact.id:
                    return user
                raise IdempotencyConflictError("Idempotency key belongs to a completed avatar upload")
            if artifact.lifecycle != "pending_upload":
                raise IdempotencyConflictError("Idempotency key belongs to an inactive artifact")
            try:
                self.storage.put_avatar(file_id, normalized_content, ".png")
                if not self.storage.verify(storage_key, len(normalized_content), digest):
                    raise OSError("Stored avatar failed checksum verification")
                user, previous_artifact = self.repository.activate_avatar_artifact(user_id, file_id)
            except Exception as write_error:
                try:
                    recovered_user, active_key = self.repository.resolve_avatar_after_write_error(user_id)
                    if recovered_user is not None and active_key == storage_key:
                        return recovered_user
                except Exception:
                    logger.error("Не удалось проверить ссылку на аватар после ошибки", extra={"event": "profile.avatar.commit_outcome_unknown"})
                    raise write_error
                try:
                    self.storage.delete(storage_key, backend=self.storage.backend)
                    self.repository.mark_artifact_deleted(file_id)
                except Exception as cleanup_error:
                    self.repository.mark_artifact_cleanup_failed(file_id, type(cleanup_error).__name__)
                raise
            if previous_artifact is not None:
                self._delete_artifact(previous_artifact)
            return user

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

    def read_avatar(self, storage_key: str | None, media_type: str | None, artifact_id: UUID | None = None) -> tuple[str, bytes] | None:
        if not storage_key or media_type not in AVATAR_MEDIA_TYPES:
            return None
        artifact = self.repository.get_artifact(artifact_id) if artifact_id and hasattr(self.repository, "get_artifact") else None
        return media_type, self.storage.read(storage_key, backend=artifact.backend if artifact else None)

    def upload_image(self, user_id: UUID, original_name: str, content: bytes, idempotency_key: str | None = None):
        if len(content) > MAX_AVATAR_BYTES:
            raise AvatarTooLargeError("Image exceeds 5 MiB")
        normalized = self._normalize_avatar(content)
        artifact_id = uuid4()
        key = self.storage.image_key(artifact_id)
        digest = sha256(normalized).hexdigest()
        basename = PurePath(original_name.replace("\\", "/")).name
        safe_name = "".join(char for char in basename if char >= " " and char != "\x7f" and char not in '"\\')[:255] or "image.png"
        idem = self._idempotency_key(idempotency_key, "image")
        artifact = self.repository.reserve_user_image(user_id, artifact_id, self.storage.backend, self.storage.bucket,
                                           key, safe_name, len(normalized), digest, NORMALIZED_AVATAR_MEDIA_TYPE, idem)
        if artifact.checksum_sha256 != digest or artifact.original_name != safe_name:
            raise IdempotencyConflictError("Idempotency key was already used for different content")
        artifact_id, key = artifact.id, artifact.object_key
        if artifact.lifecycle == "active":
            return artifact
        if artifact.lifecycle != "pending_upload":
            raise IdempotencyConflictError("Idempotency key belongs to an inactive artifact")
        try:
            self.storage.put_image(artifact_id, normalized)
            if not self.storage.verify(key, len(normalized), digest):
                raise OSError("Stored image failed checksum verification")
            return self.repository.activate_user_image(artifact_id, user_id)
        except Exception as exc:
            try:
                recovered = self.repository.resolve_user_image_after_write_error(artifact_id, user_id)
                if recovered is not None:
                    return recovered
            except Exception:
                logger.error("Не удалось проверить сохранение изображения профиля", extra={"event": "profile.image.commit_outcome_unknown"})
                raise exc
            try:
                self.storage.delete(key, backend=self.storage.backend)
                self.repository.mark_artifact_deleted(artifact_id)
            except Exception as cleanup_error:
                self.repository.mark_artifact_cleanup_failed(artifact_id, type(cleanup_error).__name__)
            raise

    def read_user_image(self, user_id: UUID, artifact_id: UUID):
        artifact = self.repository.get_owned_artifact(artifact_id, user_id, "image")
        if artifact is None:
            return None
        return artifact, self.storage.read(artifact.object_key, backend=artifact.backend)

    def remove_user_image(self, user_id: UUID, artifact_id: UUID) -> bool:
        artifact = self.repository.mark_user_artifact_pending_delete(artifact_id, user_id, "image")
        if artifact is None:
            return False
        self._delete_artifact(artifact)
        return True

    def remove_avatar(self, user_id: UUID) -> UserRecord:
        if hasattr(self.repository, "clear_avatar_artifact"):
            user, previous_artifact = self.repository.clear_avatar_artifact(user_id)
            if previous_artifact is not None:
                self._delete_artifact(previous_artifact)
            return user
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

    def _delete_artifact(self, artifact) -> None:
        try:
            self.storage.delete(artifact.object_key, backend=artifact.backend)
            self.repository.mark_artifact_deleted(artifact.id)
        except Exception as exc:
            self.repository.mark_artifact_cleanup_failed(artifact.id, type(exc).__name__)
            logger.warning("Не удалось удалить заменённый объект аватара", extra={
                "event": "profile.avatar.previous_object_cleanup_failed",
                "event_fields": {"artifact_id": str(artifact.id), "error_type": type(exc).__name__},
            })

    @staticmethod
    def _idempotency_key(value: str | None, prefix: str) -> str:
        key = (value or uuid4().hex).strip()
        if not key or len(key) > 119:
            raise IdempotencyConflictError("Idempotency-Key must contain 1 to 119 characters")
        return f"{prefix}:{key}"
