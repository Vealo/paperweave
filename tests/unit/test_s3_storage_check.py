from io import BytesIO
from uuid import UUID

import boto3
from botocore.response import StreamingBody
from botocore.stub import Stubber

from paperweave.infrastructure.storage import s3_check


def _client():
    return boto3.client(
        "s3", endpoint_url="http://s3.invalid", region_name="us-east-1",
        aws_access_key_id="unit-test", aws_secret_access_key="unit-test-secret",
    )


def test_s3_check_client_uses_bounded_timeouts(monkeypatch) -> None:
    monkeypatch.setenv("PW_S3_ENDPOINT_URL", "http://s3.invalid")
    monkeypatch.setenv("PW_S3_REGION", "us-east-1")
    monkeypatch.setenv("PW_S3_ACCESS_KEY", "unit-test")
    monkeypatch.setenv("PW_S3_SECRET_KEY", "unit-test-secret")

    client = s3_check._client()

    assert client.meta.config.connect_timeout == 2
    assert client.meta.config.read_timeout == 4


def test_s3_check_round_trip_deletes_its_unique_object(monkeypatch, capsys) -> None:
    client = _client()
    monkeypatch.setattr(s3_check, "_client", lambda: client)
    ids = iter((UUID(int=1), UUID(int=2)))
    monkeypatch.setattr(s3_check, "uuid4", lambda: next(ids))
    monkeypatch.setenv("PW_S3_CHECK_MODE", "round-trip")
    monkeypatch.setenv("PW_S3_CHECK_TIMEOUT", "1")
    monkeypatch.setenv("PW_S3_BUCKET", "unit-test")
    key = "paperweave-diagnostics/storage-check/00000000000000000000000000000001"
    payload = b"paperweave storage check 00000000-0000-0000-0000-000000000002"

    with Stubber(client) as stubber:
        stubber.add_response("head_bucket", {}, {"Bucket": "unit-test"})
        stubber.add_response("put_object", {"ETag": '"etag"'}, {
            "Bucket": "unit-test", "Key": key, "Body": payload, "ContentType": "text/plain",
        })
        stubber.add_response("get_object", {
            "Body": StreamingBody(BytesIO(payload), len(payload)), "ContentLength": len(payload),
        }, {"Bucket": "unit-test", "Key": key})
        stubber.add_response("delete_object", {}, {"Bucket": "unit-test", "Key": key})
        stubber.add_client_error("head_object", service_error_code="404", http_status_code=404, expected_params={
            "Bucket": "unit-test", "Key": key,
        })

        assert s3_check.main() == 0
        stubber.assert_no_pending_responses()

    assert "S3 check passed" in capsys.readouterr().out


def test_s3_check_reports_auth_failure_without_success(monkeypatch, capsys) -> None:
    client = _client()
    monkeypatch.setattr(s3_check, "_client", lambda: client)
    monkeypatch.setenv("PW_S3_CHECK_MODE", "readiness")
    monkeypatch.setenv("PW_S3_CHECK_TIMEOUT", "0.1")
    monkeypatch.setenv("PW_S3_BUCKET", "unit-test")

    with Stubber(client) as stubber:
        stubber.add_client_error("head_bucket", service_error_code="AccessDenied", http_status_code=403, expected_params={
            "Bucket": "unit-test",
        })
        assert s3_check.main() == 1

    captured = capsys.readouterr()
    assert "AccessDenied" in captured.err
    assert "passed" not in captured.out


def test_round_trip_cleanup_deletes_object_after_validation_failure(monkeypatch) -> None:
    client = _client()
    ids = iter((UUID(int=3), UUID(int=4)))
    monkeypatch.setattr(s3_check, "uuid4", lambda: next(ids))
    key = "paperweave-diagnostics/storage-check/00000000000000000000000000000003"
    payload = b"paperweave storage check 00000000-0000-0000-0000-000000000004"

    with Stubber(client) as stubber:
        stubber.add_response("put_object", {"ETag": '"etag"'}, {
            "Bucket": "unit-test", "Key": key, "Body": payload, "ContentType": "text/plain",
        })
        stubber.add_response("get_object", {
            "Body": StreamingBody(BytesIO(b"wrong"), 5), "ContentLength": 5,
        }, {"Bucket": "unit-test", "Key": key})
        stubber.add_response("delete_object", {}, {"Bucket": "unit-test", "Key": key})

        try:
            s3_check._round_trip(client, "unit-test")
        except RuntimeError as exc:
            assert str(exc) == "S3 round-trip returned different bytes"
        else:
            raise AssertionError("mismatched payload should fail the check")
        stubber.assert_no_pending_responses()
