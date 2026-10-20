from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from paperweave.cli import ComposeRunner, _run_s3_probe, _safe_endpoint, _seaweedfs_state, _storage_summary
from paperweave.config import load_config


def test_start_does_not_start_app_when_migration_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config_path = tmp_path / "config.toml"
    config_path.write_text(
        (Path(__file__).parents[2] / "config.example.toml").read_text(),
        encoding="utf-8",
    )
    runner = ComposeRunner(config_path, "paperweave-test", load_config(config_path))
    calls: list[tuple[str, ...]] = []

    def fake_run(*arguments: str, check: bool = True) -> subprocess.CompletedProcess[str]:
        calls.append(arguments)
        if arguments[:2] == ("run", "--rm"):
            raise subprocess.CalledProcessError(1, arguments)
        return subprocess.CompletedProcess(arguments, 0)

    monkeypatch.setattr(runner, "run", fake_run)

    with pytest.raises(subprocess.CalledProcessError):
        runner.start()

    assert ("up", "-d", "--wait", "--wait-timeout", "60", "db") in calls
    assert ("run", "--rm", "migrate") in calls
    assert not any(call[0] == "up" and call[-2:] == ("api", "ui") for call in calls)


def test_storage_summary_omits_endpoint_credentials(tmp_path: Path, capsys) -> None:
    config_path = tmp_path / "config.toml"
    config_path.write_text(
        (Path(__file__).parents[2] / "config.example.toml").read_text(),
        encoding="utf-8",
    )
    config = load_config(config_path)

    assert _safe_endpoint("https://user:secret@example.test:9443/s3?token=hidden") == "https://example.test:9443"
    _storage_summary(config, "running (healthy)", "unavailable")
    output = capsys.readouterr().out
    assert "change_me_storage_secret" not in output
    assert "S3 endpoint:" in output
    assert "S3 bucket: paperweave-artifacts" in output
    assert "S3 readiness: unavailable" in output


def test_seaweedfs_state_reports_compose_health(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    config_path = tmp_path / "config.toml"
    config_path.write_text(
        (Path(__file__).parents[2] / "config.example.toml").read_text(),
        encoding="utf-8",
    )
    runner = ComposeRunner(config_path, "paperweave-test", load_config(config_path))

    def fake_run(*arguments: str, check: bool = True, capture_output: bool = False) -> subprocess.CompletedProcess[str]:
        assert arguments == ("ps", "--format", "json", "seaweedfs")
        assert capture_output
        return subprocess.CompletedProcess(arguments, 0, stdout='{"Service":"seaweedfs","State":"running","Health":"healthy"}\n')

    monkeypatch.setattr(runner, "run", fake_run)
    assert _seaweedfs_state(runner) == "running (healthy)"


def test_s3_probe_failure_is_reported_as_unavailable(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys) -> None:
    config_path = tmp_path / "config.toml"
    config_path.write_text(
        (Path(__file__).parents[2] / "config.example.toml").read_text(),
        encoding="utf-8",
    )
    runner = ComposeRunner(config_path, "paperweave-test", load_config(config_path))

    def fake_run(*arguments: str, check: bool = True, capture_output: bool = False) -> subprocess.CompletedProcess[str]:
        assert arguments == ("--profile", "storage-check", "run", "--rm", "--no-deps", "storage-probe")
        return subprocess.CompletedProcess(arguments, 1)

    monkeypatch.setattr(runner, "run", fake_run)
    assert _run_s3_probe(runner, mode="readiness", profile="storage-check") == 1
    assert "S3 readiness: unavailable" in capsys.readouterr().err
