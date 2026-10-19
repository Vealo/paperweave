from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from paperweave.cli import ComposeRunner
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
