"""Isolated tests for avatar decoding, normalization and replacement lifecycle."""

from __future__ import annotations

from io import BytesIO
from pathlib import Path
from types import SimpleNamespace
from uuid import UUID

import pytest
from PIL import Image

import paperweave.modules.identity.profile as profile_module
from paperweave.infrastructure.storage.local import LocalFileStorage
from paperweave.modules.identity.profile import (
    MAX_AVATAR_BYTES,
    MAX_AVATAR_DIMENSION,
    MAX_AVATAR_PIXELS,
    AvatarTooLargeError,
    InvalidAvatarError,
    ProfileService,
)


USER_ID = UUID("a180eb97-9dad-45a1-af32-6c387cb06625")


def image_bytes(
    format_name: str = "PNG",
    size: tuple[int, int] = (4, 3),
    *,
    exif: bytes | None = None,
) -> bytes:
    image = Image.new("RGB", size, color=(120, 40, 80))
    output = BytesIO()
    save_options = {"exif": exif} if exif is not None else {}
    image.save(output, format=format_name, **save_options)
    return output.getvalue()


class MemoryStorage:
    def __init__(self) -> None:
        self.objects: dict[str, bytes] = {"avatars/old.png": b"old avatar"}
        self.deleted: list[str] = []
        self.last_put: tuple[str, bytes, str] | None = None
        self.fail_put = False

    def put_avatar(self, file_id: UUID, content: bytes, extension: str) -> str:
        if self.fail_put:
            raise OSError("write failed")
        key = f"avatars/{file_id.hex}{extension}"
        self.objects[key] = content
        self.last_put = (key, content, extension)
        return key

    def delete(self, key: str) -> None:
        self.deleted.append(key)
        self.objects.pop(key, None)

    def read(self, key: str) -> bytes:
        return self.objects[key]


class MemoryRepository:
    def __init__(self, storage: MemoryStorage) -> None:
        self.storage = storage
        self.updated: list[tuple[UUID, str, str]] = []
        self.fail_update = False
        self.fail_after_commit = False
        self.fail_reconcile = False
        self.user = SimpleNamespace(avatar_key="avatars/old.png", avatar_media_type="image/png")

    def get_user(self, user_id: UUID):
        return self.user

    def update_avatar(self, user_id: UUID, storage_key: str, media_type: str):
        if self.fail_update:
            raise RuntimeError("database commit failed")
        assert storage_key in self.storage.objects
        assert "avatars/old.png" in self.storage.objects
        self.updated.append((user_id, storage_key, media_type))
        self.user.avatar_key = storage_key
        self.user.avatar_media_type = media_type
        if self.fail_after_commit:
            raise RuntimeError("commit acknowledgement lost")
        return self.user, "avatars/old.png"

    def resolve_avatar_after_write_error(self, user_id: UUID):
        if self.fail_reconcile:
            raise RuntimeError("database unavailable during recovery")
        return self.user, self.user.avatar_key


def service() -> tuple[ProfileService, MemoryRepository, MemoryStorage]:
    storage = MemoryStorage()
    repository = MemoryRepository(storage)
    return ProfileService(repository, storage), repository, storage


@pytest.mark.parametrize("format_name", ["PNG", "JPEG", "WEBP"])
def test_supported_decoded_images_normalize_to_png_and_ignore_mime(format_name: str) -> None:
    profile, repository, storage = service()

    profile.update_avatar(USER_ID, "text/plain", image_bytes(format_name))

    assert repository.updated[0][2] == "image/png"
    assert storage.last_put is not None
    key, content, extension = storage.last_put
    assert key == repository.user.avatar_key
    assert extension == ".png"
    with Image.open(BytesIO(content)) as normalized:
        assert normalized.format == "PNG"
        assert normalized.size == (4, 3)
        assert not normalized.getexif()
    assert "avatars/old.png" in storage.deleted
    assert "avatars/old.png" not in storage.objects


def test_exif_orientation_is_applied_and_metadata_is_removed() -> None:
    exif = Image.Exif()
    exif[274] = 6
    profile, _, storage = service()

    profile.update_avatar(USER_ID, "image/jpeg", image_bytes("JPEG", (4, 2), exif=exif.tobytes()))

    assert storage.last_put is not None
    with Image.open(BytesIO(storage.last_put[1])) as normalized:
        assert normalized.size == (2, 4)
        assert not normalized.getexif()
        assert "exif" not in normalized.info


def test_normalized_png_drops_embedded_metadata() -> None:
    from PIL.PngImagePlugin import PngInfo

    metadata = PngInfo()
    metadata.add_text("Comment", "private comment")
    metadata.add_itxt("XML:com.adobe.xmp", "<xmp>private metadata</xmp>")
    output = BytesIO()
    Image.new("RGB", (4, 3), color=(120, 40, 80)).save(
        output, format="PNG", pnginfo=metadata, icc_profile=b"test-profile"
    )
    profile, _, storage = service()

    profile.update_avatar(USER_ID, "image/png", output.getvalue())

    assert storage.last_put is not None
    with Image.open(BytesIO(storage.last_put[1])) as normalized:
        assert not normalized.info
        assert not normalized.getexif()


def test_input_exactly_at_byte_limit_is_accepted(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(profile_module, "MAX_AVATAR_BYTES", 4096)
    content = image_bytes()
    content += b"\0" * (4096 - len(content))
    profile, repository, _ = service()

    profile.update_avatar(USER_ID, "image/png", content)

    assert len(repository.updated) == 1


def test_invalid_or_corrupt_image_does_not_write_or_change_old_object() -> None:
    profile, repository, storage = service()

    with pytest.raises(InvalidAvatarError):
        profile.update_avatar(USER_ID, "image/png", b"not an image")

    assert not repository.updated
    assert storage.objects == {"avatars/old.png": b"old avatar"}
    assert not storage.deleted


def test_dimension_limit_is_enforced_before_storage() -> None:
    profile, repository, storage = service()
    allowed = image_bytes(size=(MAX_AVATAR_DIMENSION, 1))
    profile.update_avatar(USER_ID, "image/png", allowed)
    assert len(repository.updated) == 1

    profile, repository, storage = service()
    payload = image_bytes(size=(MAX_AVATAR_DIMENSION + 1, 1))

    with pytest.raises(AvatarTooLargeError):
        profile.update_avatar(USER_ID, "image/png", payload)

    assert not repository.updated
    assert set(storage.objects) == {"avatars/old.png"}


def test_pixel_limit_is_enforced_at_boundary_before_storage(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(profile_module, "MAX_AVATAR_PIXELS", 12)
    profile, repository, storage = service()

    allowed = image_bytes(size=(3, 4))
    profile.update_avatar(USER_ID, "image/png", allowed)
    assert len(repository.updated) == 1

    profile, repository, storage = service()
    too_large = image_bytes(size=(4, 4))
    with pytest.raises(AvatarTooLargeError):
        profile.update_avatar(USER_ID, "image/png", too_large)

    assert not repository.updated
    assert set(storage.objects) == {"avatars/old.png"}


def test_payload_size_limit_is_enforced_before_decode() -> None:
    profile, repository, storage = service()

    with pytest.raises(AvatarTooLargeError):
        profile.update_avatar(USER_ID, "image/png", b"x" * (MAX_AVATAR_BYTES + 1))

    assert not repository.updated
    assert set(storage.objects) == {"avatars/old.png"}


def test_repository_failure_removes_new_object_and_preserves_previous_avatar() -> None:
    profile, repository, storage = service()
    repository.fail_update = True

    with pytest.raises(RuntimeError, match="database commit failed"):
        profile.update_avatar(USER_ID, "image/jpeg", image_bytes("JPEG"))

    assert set(storage.objects) == {"avatars/old.png"}
    assert storage.deleted == [storage.last_put[0]]
    assert repository.user.avatar_key == "avatars/old.png"


def test_ambiguous_commit_keeps_new_object_when_database_points_to_it() -> None:
    profile, repository, storage = service()
    repository.fail_after_commit = True

    user = profile.update_avatar(USER_ID, "image/jpeg", image_bytes("JPEG"))

    assert user.avatar_key == storage.last_put[0]
    assert user.avatar_key in storage.objects
    assert "avatars/old.png" in storage.deleted


def test_unresolved_commit_outcome_keeps_candidate_and_logs_reconciliation_failure(
    caplog: pytest.LogCaptureFixture,
) -> None:
    profile, repository, storage = service()
    repository.fail_update = True
    repository.fail_reconcile = True

    with pytest.raises(RuntimeError, match="database commit failed"):
        profile.update_avatar(USER_ID, "image/jpeg", image_bytes("JPEG"))

    assert storage.last_put is not None
    assert storage.last_put[0] in storage.objects
    assert "avatars/old.png" in storage.objects
    assert any(
        getattr(record, "event", None) == "profile.avatar.commit_outcome_unknown"
        for record in caplog.records
    )


def test_storage_write_failure_never_updates_database() -> None:
    profile, repository, storage = service()
    storage.fail_put = True

    with pytest.raises(OSError, match="write failed"):
        profile.update_avatar(USER_ID, "image/png", image_bytes())

    assert not repository.updated
    assert set(storage.objects) == {"avatars/old.png"}
    assert not storage.deleted


def test_local_avatar_write_failure_leaves_no_partial_or_temporary_object(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    storage = LocalFileStorage(tmp_path)

    def fail_replace(source, target) -> None:
        raise OSError("atomic replace failed")

    monkeypatch.setattr("paperweave.infrastructure.storage.local.os.replace", fail_replace)
    with pytest.raises(OSError, match="atomic replace failed"):
        storage.put_avatar(USER_ID, b"avatar", ".png")

    avatar_dir = tmp_path / "avatars" / USER_ID.hex[:2]
    assert not list(avatar_dir.iterdir())


def test_local_avatar_write_replaces_atomically_and_can_be_read_and_deleted(
    tmp_path: Path,
) -> None:
    storage = LocalFileStorage(tmp_path)
    key = storage.put_avatar(USER_ID, b"normalized avatar", ".png")
    storage.put_avatar(USER_ID, b"replacement avatar", ".png")

    assert storage.read(key) == b"replacement avatar"
    avatar_dir = tmp_path / "avatars" / USER_ID.hex[:2]
    assert [path.name for path in avatar_dir.iterdir()] == [Path(key).name]

    storage.delete(key)

    assert not (tmp_path / key).exists()
