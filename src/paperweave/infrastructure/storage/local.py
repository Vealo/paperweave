"""Local filesystem adapter using generated opaque keys, never user paths."""

import os
import tempfile
from hashlib import sha256
from pathlib import Path
from uuid import UUID

class LocalFileStorage:
    def __init__(self, root: Path) -> None:
        self.root = root.resolve()
        self.backend = "local"
        self.bucket = ""

    def check(self) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        if not self.root.is_dir() or not os.access(self.root, os.W_OK):
            raise OSError("Local artifact storage is unavailable")

    def put(self, file_id: UUID, content: bytes) -> str:
        key = self.document_key(file_id)
        return self._write(key, content)

    @staticmethod
    def document_key(file_id: UUID) -> str:
        return f"{file_id.hex[:2]}/{file_id.hex}.pdf"

    def put_avatar(self, file_id: UUID, content: bytes, extension: str) -> str:
        if extension not in {".png", ".jpg", ".webp"}:
            raise ValueError("Unsupported avatar extension")
        key = self.avatar_key(file_id, extension)
        target = (self.root / key).resolve()
        if not target.is_relative_to(self.root):
            raise ValueError("Invalid storage key")
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary_path: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="wb",
                dir=target.parent,
                prefix=f".{target.name}.",
                suffix=".tmp",
                delete=False,
            ) as temporary:
                temporary_path = Path(temporary.name)
                temporary.write(content)
                temporary.flush()
                os.fsync(temporary.fileno())
            os.replace(temporary_path, target)
            return key
        finally:
            if temporary_path is not None:
                temporary_path.unlink(missing_ok=True)

    def put_image(self, file_id: UUID, content: bytes) -> str:
        return self._write(self.image_key(file_id), content)

    @staticmethod
    def image_key(file_id: UUID) -> str:
        return f"images/{file_id.hex[:2]}/{file_id.hex}.png"

    @staticmethod
    def avatar_key(file_id: UUID, extension: str) -> str:
        return f"avatars/{file_id.hex[:2]}/{file_id.hex}{extension}"

    def _write(self, key: str, content: bytes) -> str:
        target = (self.root / key).resolve()
        if not target.is_relative_to(self.root): raise ValueError("Invalid storage key")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
        return key

    def verify(self, key: str, size_bytes: int, checksum_sha256: str | None = None) -> bool:
        content = self.read(key)
        return len(content) == size_bytes and (checksum_sha256 is None or sha256(content).hexdigest() == checksum_sha256)

    def read(self, key: str) -> bytes:
        target = (self.root / key).resolve()
        if not target.is_relative_to(self.root): raise FileNotFoundError
        return target.read_bytes()

    def delete(self, key: str) -> None:
        target = (self.root / key).resolve()
        if not target.is_relative_to(self.root): raise FileNotFoundError
        target.unlink(missing_ok=True)
