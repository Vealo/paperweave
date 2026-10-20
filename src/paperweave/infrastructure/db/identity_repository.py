"""Database adapter for owner accounts and server-side sessions."""

from collections.abc import Callable
from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from paperweave.infrastructure.db.models import FileArtifactRecord, SessionRecord, UserRecord, UserSettingsRecord
from paperweave.modules.identity.security import hash_password

BOOTSTRAP_OWNER_ID = UUID("00000000-0000-0000-0000-000000000001")
IDLE_TIMEOUT = timedelta(hours=12)
ABSOLUTE_TIMEOUT = timedelta(days=7)


class IdentityRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def owner_exists(self) -> bool:
        owner = self._session.get(UserRecord, BOOTSTRAP_OWNER_ID)
        return owner is not None and owner.password_hash is not None

    def bootstrap_owner(self, email: str, display_name: str, password: str) -> UserRecord | None:
        owner = self._session.scalar(
            select(UserRecord).where(UserRecord.id == BOOTSTRAP_OWNER_ID).with_for_update()
        )
        if owner is None or owner.password_hash is not None:
            return None
        if self._session.scalar(
            select(UserRecord.id).where(
                UserRecord.email == email, UserRecord.id != BOOTSTRAP_OWNER_ID
            )
        ) is not None:
            return None
        owner.email = email
        owner.display_name = display_name
        owner.password_hash = hash_password(password)
        self._ensure_settings(owner.id)
        self._session.commit()
        return owner

    def authenticate(
        self, email: str, password_check: Callable[[str | None], bool]
    ) -> UserRecord | None:
        user = self._session.scalar(select(UserRecord).where(UserRecord.email == email))
        if user is None or not user.is_active or not password_check(user.password_hash):
            return None
        return user

    def create_member(self, email: str, display_name: str, password: str) -> UserRecord:
        user = UserRecord(
            id=uuid4(),
            email=email,
            display_name=display_name,
            password_hash=hash_password(password),
            role="member",
        )
        self._session.add(user)
        self._session.add(UserSettingsRecord(user_id=user.id))
        self._session.commit()
        return user

    def get_user(self, user_id: UUID) -> UserRecord | None:
        return self._session.get(UserRecord, user_id)

    def list_users(self) -> list[UserRecord]:
        return list(self._session.scalars(select(UserRecord).order_by(UserRecord.created_at, UserRecord.id)))

    def update_profile(self, user_id: UUID, *, display_name: str | None, email: str | None) -> UserRecord:
        user = self._session.get(UserRecord, user_id)
        if user is None:
            raise LookupError("User not found")
        if display_name is not None:
            user.display_name = display_name
        if email is not None:
            user.email = email
        self._session.commit()
        return user

    def change_password(self, user_id: UUID, password: str) -> None:
        user = self._session.get(UserRecord, user_id)
        if user is None:
            raise LookupError("User not found")
        user.password_hash = hash_password(password)
        self._session.execute(delete(SessionRecord).where(SessionRecord.user_id == user_id))
        self._session.commit()

    def set_user_active(self, user_id: UUID, is_active: bool) -> UserRecord:
        user = self._session.get(UserRecord, user_id)
        if user is None:
            raise LookupError("User not found")
        user.is_active = is_active
        if not is_active:
            self._session.execute(delete(SessionRecord).where(SessionRecord.user_id == user_id))
        self._session.commit()
        return user

    def get_settings(self, user_id: UUID) -> UserSettingsRecord:
        settings = self._session.get(UserSettingsRecord, user_id)
        if settings is None:
            settings = UserSettingsRecord(user_id=user_id)
            self._session.add(settings)
            self._session.commit()
        return settings

    def update_settings(
        self, user_id: UUID, *, theme: str
    ) -> UserSettingsRecord:
        settings = self.get_settings(user_id)
        settings.theme = theme
        self._session.commit()
        return settings

    def _ensure_settings(self, user_id: UUID) -> None:
        if self._session.get(UserSettingsRecord, user_id) is None:
            self._session.add(UserSettingsRecord(user_id=user_id))

    def update_avatar(self, user_id: UUID, storage_key: str, media_type: str) -> tuple[UserRecord, str | None]:
        user = self._session.get(UserRecord, user_id)
        if user is None:
            raise LookupError("User not found")
        previous_key = user.avatar_key
        user.avatar_key = storage_key
        user.avatar_media_type = media_type
        self._session.commit()
        return user, previous_key

    def find_idempotent_artifact(self, user_id: UUID, idempotency_key: str, kind: str) -> FileArtifactRecord | None:
        return self._session.scalar(select(FileArtifactRecord).where(
            FileArtifactRecord.owner_user_id == user_id,
            FileArtifactRecord.idempotency_key == idempotency_key,
            FileArtifactRecord.kind == kind,
        ))

    def reserve_avatar_artifact(self, user_id: UUID, artifact_id: UUID, backend: str, bucket: str, key: str,
                                size_bytes: int, checksum: str, media_type: str,
                                idempotency_key: str) -> FileArtifactRecord:
        existing = self.find_idempotent_artifact(user_id, idempotency_key, "avatar")
        if existing is not None:
            return existing
        artifact = FileArtifactRecord(
            id=artifact_id, owner_user_id=user_id, kind="avatar", domain_type="user", domain_id=user_id,
            backend=backend, bucket=bucket, object_key=key, original_name="avatar.png", media_type=media_type,
            size_bytes=size_bytes, checksum_sha256=checksum, version=1, lifecycle="pending_upload",
            idempotency_key=idempotency_key,
        )
        self._session.add(artifact)
        try:
            self._session.commit()
        except IntegrityError:
            self._session.rollback()
            existing = self.find_idempotent_artifact(user_id, idempotency_key, "avatar")
            if existing is None:
                raise
            return existing
        return artifact

    def activate_avatar_artifact(self, user_id: UUID, artifact_id: UUID) -> tuple[UserRecord, FileArtifactRecord | None]:
        user = self._session.scalar(select(UserRecord).where(UserRecord.id == user_id).with_for_update())
        candidate = self._session.get(FileArtifactRecord, artifact_id)
        if user is None or candidate is None or candidate.owner_user_id != user_id:
            raise LookupError("Avatar artifact not found")
        previous = self._session.get(FileArtifactRecord, user.avatar_artifact_id) if user.avatar_artifact_id else None
        user.avatar_artifact_id = artifact_id
        user.avatar_key = candidate.object_key
        user.avatar_media_type = candidate.media_type
        candidate.lifecycle = "active"
        if previous is not None:
            previous.lifecycle = "pending_delete"
        self._session.commit()
        return user, previous

    def mark_artifact_deleted(self, artifact_id: UUID) -> None:
        artifact = self._session.get(FileArtifactRecord, artifact_id)
        if artifact is not None:
            artifact.lifecycle = "deleted"
            artifact.deleted_at = datetime.now(timezone.utc)
            artifact.last_cleanup_error = None
            self._session.commit()

    def mark_artifact_cleanup_failed(self, artifact_id: UUID, error_type: str) -> None:
        artifact = self._session.get(FileArtifactRecord, artifact_id)
        if artifact is not None:
            artifact.lifecycle = "pending_delete"
            artifact.cleanup_attempts += 1
            artifact.last_cleanup_error = error_type[:500]
            self._session.commit()

    def get_artifact(self, artifact_id: UUID) -> FileArtifactRecord | None:
        return self._session.get(FileArtifactRecord, artifact_id)

    def reserve_user_image(self, user_id: UUID, artifact_id: UUID, backend: str, bucket: str, key: str,
                           original_name: str, size_bytes: int, checksum: str, media_type: str,
                           idempotency_key: str) -> FileArtifactRecord:
        existing = self.find_idempotent_artifact(user_id, idempotency_key, "image")
        if existing is not None:
            return existing
        artifact = FileArtifactRecord(
            id=artifact_id, owner_user_id=user_id, kind="image", domain_type="user", domain_id=user_id,
            backend=backend, bucket=bucket, object_key=key, original_name=original_name,
            media_type=media_type, size_bytes=size_bytes, checksum_sha256=checksum, version=1,
            lifecycle="pending_upload", idempotency_key=idempotency_key,
        )
        self._session.add(artifact)
        try:
            self._session.commit()
        except IntegrityError:
            self._session.rollback()
            existing = self.find_idempotent_artifact(user_id, idempotency_key, "image")
            if existing is None:
                raise
            return existing
        return artifact

    def activate_user_image(self, artifact_id: UUID, user_id: UUID) -> FileArtifactRecord:
        artifact = self._session.get(FileArtifactRecord, artifact_id)
        if artifact is None or artifact.owner_user_id != user_id or artifact.kind != "image":
            raise LookupError("Image artifact not found")
        artifact.lifecycle = "active"
        self._session.commit()
        return artifact

    def resolve_user_image_after_write_error(self, artifact_id: UUID, user_id: UUID) -> FileArtifactRecord | None:
        self._session.rollback()
        artifact = self._session.get(FileArtifactRecord, artifact_id, populate_existing=True)
        if artifact and artifact.owner_user_id == user_id and artifact.kind == "image" and artifact.lifecycle == "active":
            return artifact
        return None

    def get_owned_artifact(self, artifact_id: UUID, user_id: UUID, kind: str) -> FileArtifactRecord | None:
        return self._session.scalar(select(FileArtifactRecord).where(
            FileArtifactRecord.id == artifact_id,
            FileArtifactRecord.owner_user_id == user_id,
            FileArtifactRecord.kind == kind,
            FileArtifactRecord.lifecycle == "active",
        ))

    def mark_user_artifact_pending_delete(self, artifact_id: UUID, user_id: UUID, kind: str) -> FileArtifactRecord | None:
        artifact = self._session.scalar(select(FileArtifactRecord).where(
            FileArtifactRecord.id == artifact_id,
            FileArtifactRecord.owner_user_id == user_id,
            FileArtifactRecord.kind == kind,
            FileArtifactRecord.lifecycle.in_(("active", "pending_delete", "deleted")),
        ))
        if artifact is None:
            return None
        artifact.lifecycle = "pending_delete"
        self._session.commit()
        return artifact

    def resolve_avatar_after_write_error(
        self, user_id: UUID
    ) -> tuple[UserRecord | None, str | None]:
        """Re-read the committed avatar pointer after an ambiguous commit error."""
        self._session.rollback()
        user = self._session.get(UserRecord, user_id, populate_existing=True)
        return user, user.avatar_key if user is not None else None

    def clear_avatar(self, user_id: UUID) -> tuple[UserRecord, str | None]:
        user = self._session.get(UserRecord, user_id)
        if user is None:
            raise LookupError("User not found")
        previous_key = user.avatar_key
        user.avatar_key = None
        user.avatar_media_type = None
        self._session.commit()
        return user, previous_key

    def clear_avatar_artifact(self, user_id: UUID) -> tuple[UserRecord, FileArtifactRecord | None]:
        user = self._session.get(UserRecord, user_id)
        if user is None:
            raise LookupError("User not found")
        previous = self._session.get(FileArtifactRecord, user.avatar_artifact_id) if user.avatar_artifact_id else None
        user.avatar_artifact_id = None
        user.avatar_key = None
        user.avatar_media_type = None
        if previous is not None:
            previous.lifecycle = "pending_delete"
        self._session.commit()
        return user, previous

    def create_session(self, user_id: UUID, token_hash: str) -> None:
        now = datetime.now(timezone.utc)
        self._session.execute(
            delete(SessionRecord).where(
                (SessionRecord.expires_at <= now)
                | (SessionRecord.last_activity_at <= now - IDLE_TIMEOUT)
            )
        )
        self._session.add(
            SessionRecord(
                id=uuid4(),
                user_id=user_id,
                token_hash=token_hash,
                created_at=now,
                last_activity_at=now,
                expires_at=now + ABSOLUTE_TIMEOUT,
            )
        )
        self._session.commit()

    def resolve_session(self, token_hash: str) -> UserRecord | None:
        now = datetime.now(timezone.utc)
        record = self._session.scalar(
            select(SessionRecord).where(SessionRecord.token_hash == token_hash)
        )
        if (
            record is None
            or now >= record.expires_at
            or now >= record.last_activity_at + IDLE_TIMEOUT
        ):
            if record is not None:
                self._session.delete(record)
                self._session.commit()
            return None
        record.last_activity_at = now
        user = self._session.get(UserRecord, record.user_id)
        if user is None or not user.is_active:
            self._session.delete(record)
            self._session.commit()
            return None
        self._session.commit()
        return user

    def revoke_session(self, token_hash: str) -> None:
        record = self._session.scalar(
            select(SessionRecord).where(SessionRecord.token_hash == token_hash)
        )
        if record is not None:
            self._session.delete(record)
            self._session.commit()
