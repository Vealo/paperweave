from base64 import b64encode
from hashlib import sha256
from io import BytesIO
from uuid import uuid4

import boto3
import pytest
from botocore.exceptions import ClientError
from botocore.response import StreamingBody
from botocore.stub import Stubber

from paperweave.infrastructure.storage.s3 import S3ObjectStorage


def test_s3_avatar_upload_is_verified_and_deleted() -> None:
    client = boto3.client(
        "s3", endpoint_url="http://s3.invalid", region_name="us-east-1",
        aws_access_key_id="unit-test", aws_secret_access_key="unit-test-secret",
    )
    storage = S3ObjectStorage(
        endpoint_url="http://s3.invalid", region="us-east-1", bucket="unit-test",
        access_key="unit-test", secret_key="unit-test-secret", client=client,
    )
    file_id = uuid4()
    content = b"normalized-avatar"
    key = storage.avatar_key(file_id, ".png")
    checksum = sha256(content).hexdigest()
    with Stubber(client) as stubber:
        stubber.add_response("put_object", {"ETag": '"etag"'}, {
            "Bucket": "unit-test", "Key": key, "Body": content, "ContentType": "image/png",
            "ChecksumSHA256": b64encode(sha256(content).digest()).decode("ascii"),
        })
        stubber.add_response("head_object", {"ContentLength": len(content)}, {"Bucket": "unit-test", "Key": key})
        stubber.add_response("get_object", {
            "Body": StreamingBody(BytesIO(content), len(content)), "ContentLength": len(content),
        }, {"Bucket": "unit-test", "Key": key})
        stubber.add_response("delete_object", {}, {"Bucket": "unit-test", "Key": key})

        assert storage.put_avatar(file_id, content, ".png") == key
        assert storage.verify(key, len(content), checksum)
        storage.delete(key)

        stubber.assert_no_pending_responses()


def test_s3_backend_errors_are_not_reported_as_success() -> None:
    client = boto3.client(
        "s3", endpoint_url="http://s3.invalid", region_name="us-east-1",
        aws_access_key_id="unit-test", aws_secret_access_key="unit-test-secret",
    )
    storage = S3ObjectStorage(
        endpoint_url="http://s3.invalid", region="us-east-1", bucket="unit-test",
        access_key="unit-test", secret_key="unit-test-secret", client=client,
    )
    with Stubber(client) as stubber:
        stubber.add_client_error("head_object", service_error_code="InternalError", expected_params={
            "Bucket": "unit-test", "Key": "missing-key",
        })
        with pytest.raises(ClientError):
            storage.head("missing-key")
