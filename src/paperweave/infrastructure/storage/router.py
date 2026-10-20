"""Routes artifact operations to configured local/S3 backends."""


class StorageRouter:
    def __init__(self, selected, backends: dict[str, object]) -> None:
        self.selected = selected
        self.backends = backends
        self.backend = selected.backend
        self.bucket = selected.bucket

    def put(self, file_id, content):
        return self.selected.put(file_id, content)

    def put_avatar(self, file_id, content, extension):
        return self.selected.put_avatar(file_id, content, extension)

    def put_image(self, file_id, content):
        return self.selected.put_image(file_id, content)

    def read(self, key, backend: str | None = None):
        return self.backends[backend or self.backend].read(key)

    def delete(self, key, backend: str | None = None):
        return self.backends[backend or self.backend].delete(key)

    def verify(self, key, size_bytes, checksum_sha256=None, backend: str | None = None):
        return self.backends[backend or self.backend].verify(key, size_bytes, checksum_sha256)

    def check(self):
        check = getattr(self.selected, "check", None)
        if check:
            check()

    def document_key(self, file_id):
        return self.selected.document_key(file_id)

    def avatar_key(self, file_id, extension):
        return self.selected.avatar_key(file_id, extension)

    def image_key(self, file_id):
        return self.selected.image_key(file_id)
