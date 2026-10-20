"""S3-compatible storage adapter for private user artifacts."""

from uuid import UUID
from hashlib import sha256

import boto3
from botocore.config import Config


class S3ObjectStorage:
    def __init__(self, *, endpoint_url: str, region: str, bucket: str, access_key: str, secret_key: str, client=None) -> None:
        self.bucket = bucket
        self.backend = "s3"
        self.client = client or boto3.client(
            "s3", endpoint_url=endpoint_url, region_name=region,
            aws_access_key_id=access_key, aws_secret_access_key=secret_key,
            config=Config(s3={"addressing_style": "path"}, retries={"max_attempts": 3, "mode": "standard"}),
        )

    def put(self, file_id: UUID, content: bytes) -> str:
        return self.put_object(self.document_key(file_id), content, "application/pdf")

    @staticmethod
    def document_key(file_id: UUID) -> str:
        return f"documents/{file_id.hex[:2]}/{file_id.hex}"

    def put_avatar(self, file_id: UUID, content: bytes, extension: str) -> str:
        if extension not in {".png", ".jpg", ".webp"}:
            raise ValueError("Unsupported avatar extension")
        return self.put_object(self.avatar_key(file_id, extension), content, "image/png")

    def put_image(self, file_id: UUID, content: bytes) -> str:
        return self.put_object(self.image_key(file_id), content, "image/png")

    @staticmethod
    def image_key(file_id: UUID) -> str:
        return f"images/{file_id.hex[:2]}/{file_id.hex}.png"

    @staticmethod
    def avatar_key(file_id: UUID, extension: str) -> str:
        return f"avatars/{file_id.hex[:2]}/{file_id.hex}{extension}"

    def put_object(self, key: str, content: bytes, media_type: str) -> str:
        import base64
        import hashlib

        digest = base64.b64encode(hashlib.sha256(content).digest()).decode("ascii")
        self.client.put_object(Bucket=self.bucket, Key=key, Body=content, ContentType=media_type, ChecksumSHA256=digest)
        return key

    def read(self, key: str) -> bytes:
        result = self.client.get_object(Bucket=self.bucket, Key=key)
        return result["Body"].read()

    def delete(self, key: str) -> None:
        self.client.delete_object(Bucket=self.bucket, Key=key)

    def head(self, key: str) -> dict:
        return self.client.head_object(Bucket=self.bucket, Key=key)

    def check(self) -> None:
        try:
            self.client.head_bucket(Bucket=self.bucket)
        except Exception as exc:
            code = getattr(exc, "response", {}).get("Error", {}).get("Code")
            if code not in {"404", "NoSuchBucket", "NotFound"}:
                raise
            self.client.create_bucket(Bucket=self.bucket)

    def verify(self, key: str, size_bytes: int, checksum_sha256: str | None = None) -> bool:
        metadata = self.head(key)
        if metadata.get("ContentLength") != size_bytes:
            return False
        if checksum_sha256 is None:
            return True
        return sha256(self.read(key)).hexdigest() == checksum_sha256
