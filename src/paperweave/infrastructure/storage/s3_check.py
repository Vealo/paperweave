"""Bounded, non-destructive S3 readiness and isolated object round-trip check."""

from __future__ import annotations

import os
import sys
import time
from uuid import uuid4

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError


def _client():
    return boto3.client(
        "s3",
        endpoint_url=os.environ["PW_S3_ENDPOINT_URL"],
        region_name=os.environ["PW_S3_REGION"],
        aws_access_key_id=os.environ["PW_S3_ACCESS_KEY"],
        aws_secret_access_key=os.environ["PW_S3_SECRET_KEY"],
        config=Config(
            connect_timeout=2,
            read_timeout=4,
            s3={"addressing_style": "path"},
            retries={"max_attempts": 1},
        ),
    )


def _is_missing_bucket(exc: ClientError) -> bool:
    code = exc.response.get("Error", {}).get("Code")
    return code in {"404", "NoSuchBucket", "NotFound"}


def _ensure_bucket(client, bucket: str) -> None:
    try:
        client.head_bucket(Bucket=bucket)
    except ClientError as exc:
        if not _is_missing_bucket(exc):
            raise
        client.create_bucket(Bucket=bucket)


def _round_trip(client, bucket: str) -> None:
    key = f"paperweave-diagnostics/storage-check/{uuid4().hex}"
    payload = f"paperweave storage check {uuid4()}".encode("ascii")
    created = False
    try:
        client.put_object(Bucket=bucket, Key=key, Body=payload, ContentType="text/plain")
        created = True
        response = client.get_object(Bucket=bucket, Key=key)
        body = response["Body"]
        try:
            actual = body.read()
        finally:
            body.close()
        if actual != payload:
            raise RuntimeError("S3 round-trip returned different bytes")
        client.delete_object(Bucket=bucket, Key=key)
        created = False
        try:
            client.head_object(Bucket=bucket, Key=key)
        except ClientError as exc:
            if _is_missing_bucket(exc) or exc.response.get("Error", {}).get("Code") in {"404", "NoSuchKey", "NotFound"}:
                return
            raise
        created = True
        raise RuntimeError("S3 object still exists after delete")
    finally:
        # A failed check must not leave its uniquely named diagnostic object behind.
        if created:
            client.delete_object(Bucket=bucket, Key=key)


def main() -> int:
    mode = os.getenv("PW_S3_CHECK_MODE", "round-trip")
    if mode not in {"readiness", "round-trip"}:
        print("S3 check failed: unsupported check mode", file=sys.stderr)
        return 1
    bucket = os.environ["PW_S3_BUCKET"]
    timeout = float(os.getenv("PW_S3_CHECK_TIMEOUT", "30"))
    deadline = time.monotonic() + timeout
    client = _client()
    last_error: Exception | None = None

    while time.monotonic() < deadline:
        try:
            _ensure_bucket(client, bucket)
            if mode == "round-trip":
                _round_trip(client, bucket)
            elif mode != "readiness":
                raise ValueError("unsupported S3 check mode")
            print(f"S3 check passed: mode={mode}, bucket={bucket}")
            return 0
        except Exception as exc:
            last_error = exc
            if isinstance(exc, ClientError):
                code = exc.response.get("Error", {}).get("Code", "S3Error")
                operation = exc.operation_name or "S3 operation"
                reason = f"{code} during {operation}"
            else:
                reason = type(exc).__name__
            if time.monotonic() + 1 >= deadline:
                print(f"S3 check failed: {reason}", file=sys.stderr)
                return 1
            time.sleep(1)

    print(f"S3 check failed: {type(last_error).__name__ if last_error else 'timeout'}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
