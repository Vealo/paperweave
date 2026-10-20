"""Database adapter for owner accounts and server-side sessions."""

from collections.abc import Callable
from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from paperweave.infrastructure.db.models import SessionRecord, UserRecord, UserSettingsRecord
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

    def clear_avatar(self, user_id: UUID) -> tuple[UserRecord, str | None]:
        user = self._session.get(UserRecord, user_id)
        if user is None:
            raise LookupError("User not found")
        previous_key = user.avatar_key
        user.avatar_key = None
        user.avatar_media_type = None
        self._session.commit()
        return user, previous_key

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
