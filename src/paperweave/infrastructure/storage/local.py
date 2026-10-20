"""Local filesystem adapter using generated opaque keys, never user paths."""

import os
import tempfile
from pathlib import Path
from uuid import UUID

class LocalFileStorage:
    def __init__(self, root: Path) -> None:
        self.root = root.resolve()

    def put(self, file_id: UUID, content: bytes) -> str:
        key = f"{file_id.hex[:2]}/{file_id.hex}.pdf"
        return self._write(key, content)

    def put_avatar(self, file_id: UUID, content: bytes, extension: str) -> str:
        if extension not in {".png", ".jpg", ".webp"}:
            raise ValueError("Unsupported avatar extension")
        key = f"avatars/{file_id.hex[:2]}/{file_id.hex}{extension}"
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

    def _write(self, key: str, content: bytes) -> str:
        target = (self.root / key).resolve()
        if not target.is_relative_to(self.root): raise ValueError("Invalid storage key")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
        return key

    def read(self, key: str) -> bytes:
        target = (self.root / key).resolve()
        if not target.is_relative_to(self.root): raise FileNotFoundError
        return target.read_bytes()

    def delete(self, key: str) -> None:
        target = (self.root / key).resolve()
        if not target.is_relative_to(self.root): raise FileNotFoundError
        target.unlink(missing_ok=True)
