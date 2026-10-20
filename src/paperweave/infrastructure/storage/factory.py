"""Configured storage backend factory shared by API services."""

import os
from pathlib import Path

from paperweave.infrastructure.storage.local import LocalFileStorage
from paperweave.infrastructure.storage.s3 import S3ObjectStorage
from paperweave.infrastructure.storage.router import StorageRouter


def create_storage(config):
    storage = config.storage
    local = LocalFileStorage(Path(os.getenv("PW_FILE_STORAGE", storage.local_path)))
    s3 = S3ObjectStorage(
            endpoint_url=storage.s3_endpoint_url,
            region=storage.s3_region,
            bucket=storage.s3_bucket,
            access_key=storage.s3_access_key,
            secret_key=storage.s3_secret_key,
        )
    backends = {"local": local, "s3": s3}
    return StorageRouter(backends[storage.backend], backends)
