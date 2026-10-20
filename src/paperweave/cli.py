"""Command line entry point for local development operations."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlsplit
from uuid import uuid4

from paperweave.config import AppConfig, ConfigError, load_config


ROOT = Path(__file__).resolve().parents[2]
CONTAINER_CONFIG = "/app/config.toml"


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="paperweave",
        description="Local PaperWeave Compose operations.",
        epilog="storage-check starts a temporary isolated SeaweedFS project and verifies S3 authentication plus put/get/delete.",
    )
    parser.add_argument("--config", type=Path, default=ROOT / "config.toml")
    parser.add_argument("--project-name", default=os.getenv("COMPOSE_PROJECT_NAME", "paperweave"))
    parser.add_argument(
        "command",
        choices=("init", "config-check", "up", "down", "restart", "logs", "ps", "migrate", "test", "storage-check", "help"),
    )
    return parser


def _compose_environment(config: AppConfig) -> dict[str, str]:
    return {
        "PW_APP_NAME": config.app.name,
        "PW_LOG_LEVEL": config.app.log_level,
        "PW_API_HOST": config.api.host,
        "PW_API_PORT": str(config.api.port),
        "PW_UI_HOST": config.ui.host,
        "PW_UI_PORT": str(config.ui.port),
        "PW_API_BASE_URL": config.ui.api_base_url,
        "PW_HEALTH_TIMEOUT": str(config.timeouts.health_seconds),
        "PW_REQUEST_TIMEOUT": str(config.timeouts.request_seconds),
        "PW_HEALTH_POLL_INTERVAL": str(config.timeouts.health_poll_seconds),
        "PW_DB_HOST": config.database.host,
        "PW_DB_PORT": str(config.database.port),
        "PW_DB_NAME": config.database.name,
        "PW_DB_USER": config.database.user,
        "PW_DB_PASSWORD": config.database.password,
        "PW_BIND_HOST": config.deployment.bind_host,
        "PW_SEAWEED_VOLUME_NAME": "paperweave_seaweedfs_data",
        "PW_S3_ENDPOINT_URL": config.storage.s3_endpoint_url,
        "PW_S3_REGION": config.storage.s3_region,
        "PW_S3_BUCKET": config.storage.s3_bucket,
        "PW_S3_ACCESS_KEY": config.storage.s3_access_key,
        "PW_S3_SECRET_KEY": config.storage.s3_secret_key,
    }


class ComposeRunner:
    def __init__(self, config_path: Path, project_name: str, config: AppConfig) -> None:
        self.config_path = config_path.resolve()
        self.project_name = project_name
        self.environment = os.environ.copy()
        self.environment.update(_compose_environment(config))
        self.environment["PW_CONFIG_PATH"] = str(self.config_path)
        self.environment["PW_VOLUME_NAME"] = f"{project_name}-postgres-data"
        self.environment["PW_SEAWEED_VOLUME_NAME"] = f"{project_name}-seaweedfs-data"
        s3_config_path = self.config_path.parent / ".paperweave-secrets" / f"{project_name}-seaweedfs-s3.json"
        s3_config_path.parent.mkdir(parents=True, exist_ok=True)
        s3_config_path.parent.chmod(0o700)
        s3_document = {
            "identities": [{
                "name": "paperweave-api",
                "credentials": [{
                    "accessKey": config.storage.s3_access_key,
                    "secretKey": config.storage.s3_secret_key,
                }],
                "actions": ["Admin", "Read", "List", "Tagging", "Write"],
            }]
        }
        s3_fd = os.open(s3_config_path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        os.chmod(s3_config_path, 0o600)
        with os.fdopen(s3_fd, "w", encoding="utf-8") as s3_file:
            json.dump(s3_document, s3_file)
        self.environment["PW_SEAWEED_S3_CONFIG"] = str(s3_config_path.resolve())
        self.environment["PAPERWEAVE_CONFIG_FILE"] = CONTAINER_CONFIG

    def run(
        self, *arguments: str, check: bool = True, capture_output: bool = False
    ) -> subprocess.CompletedProcess[str]:
        command = [
            "docker",
            "compose",
            "--project-directory",
            str(ROOT),
            "--project-name",
            self.project_name,
            "--env-file",
            "/dev/null",
            "-f",
            str(ROOT / "compose.yaml"),
            *arguments,
        ]
        return subprocess.run(
            command, cwd=ROOT, env=self.environment, check=check, text=True,
            capture_output=capture_output,
        )

    def start(self, force_recreate: bool = False) -> None:
        self.run("build", "api", "migrate", "ui")
        self.run("stop", "api", "ui", check=False)
        self.run("up", "-d", "--wait", "--wait-timeout", "60", "db")
        self.run("run", "--rm", "migrate")
        recreate = ("--force-recreate",) if force_recreate else ()
        self.run("up", "-d", "--wait", "--wait-timeout", "60", *recreate, "api", "ui")


def _initialize(config_path: Path) -> int:
    sample = ROOT / "config.example.toml"
    if config_path.exists():
        print(f"Configuration already exists; left unchanged: {config_path}")
        return 0
    config_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with sample.open("rb") as source, config_path.open("xb") as target:
            shutil.copyfileobj(source, target)
        config_path.chmod(0o600)
    except FileExistsError:
        print(f"Configuration already exists; left unchanged: {config_path}")
        return 0
    print(f"Created local configuration: {config_path}")
    return 0


def _test(runner: ComposeRunner) -> int:
    test_runner = ComposeRunner(
        runner.config_path,
        f"paperweave-test-{uuid4().hex[:12]}",
        load_config(runner.config_path),
    )
    test_runner.environment["PW_FILE_VOLUME_NAME"] = f"{test_runner.project_name}-files"
    test_runner.environment.update({
        "PW_S3_ENDPOINT_URL": "http://storage-check-seaweedfs:8333",
        "PW_S3_BUCKET": "paperweave-test-artifacts",
        "PW_S3_CHECK_MODE": "readiness",
        "PW_S3_CHECK_TIMEOUT": "30",
    })
    try:
        test_runner.run("--profile", "test", "build", "test")
        test_runner.run("--profile", "test", "up", "-d", "--wait", "--wait-timeout", "60", "test-db", "storage-check-seaweedfs")
        test_runner.run("--profile", "test", "run", "--rm", "--no-deps", "storage-probe")
        result = test_runner.run("--profile", "test", "run", "--rm", "--no-deps", "test", check=False)
        return result.returncode
    finally:
        try:
            test_runner.run("--profile", "test", "down", "--volumes", "--remove-orphans", check=False)
        finally:
            _remove_ephemeral_s3_config(test_runner)


def _remove_ephemeral_s3_config(runner: ComposeRunner) -> None:
    expected_name = f"{runner.project_name}-seaweedfs-s3.json"
    path = Path(runner.environment["PW_SEAWEED_S3_CONFIG"])
    if path.parent.name == ".paperweave-secrets" and path.name == expected_name:
        path.unlink(missing_ok=True)


def _safe_endpoint(endpoint: str) -> str:
    parsed = urlsplit(endpoint)
    host = parsed.hostname or "invalid-endpoint"
    if ":" in host:
        host = f"[{host}]"
    try:
        port = f":{parsed.port}" if parsed.port else ""
    except ValueError:
        return "invalid S3 endpoint"
    return f"{parsed.scheme}://{host}{port}"


def _seaweedfs_state(runner: ComposeRunner) -> str:
    result = runner.run("ps", "--format", "json", "seaweedfs", check=False, capture_output=True)
    if result.returncode:
        return "unavailable (Compose status query failed)"
    try:
        rows = [json.loads(line) for line in result.stdout.splitlines() if line.strip()]
        if not rows:
            return "not running"
        service = rows[0]
        state = str(service.get("State") or "unknown").lower()
        health = str(service.get("Health") or "").lower()
        return f"{state} ({health})" if health and health not in {"none", ""} else state
    except (json.JSONDecodeError, AttributeError, TypeError):
        return "unknown (unrecognized Compose status)"


def _storage_summary(config: AppConfig, seaweedfs_state: str, s3_status: str) -> None:
    print(f"Storage backend: {config.storage.backend}")
    print(f"SeaweedFS: {seaweedfs_state}")
    print(f"S3 readiness: {s3_status}")
    print(f"S3 endpoint: {_safe_endpoint(config.storage.s3_endpoint_url)}")
    print(f"S3 bucket: {config.storage.s3_bucket}")


def _run_s3_probe(runner: ComposeRunner, *, mode: str, profile: str) -> int:
    runner.environment["PW_S3_CHECK_MODE"] = mode
    runner.environment["PW_S3_CHECK_TIMEOUT"] = "30"
    result = runner.run("--profile", profile, "run", "--rm", "--no-deps", "storage-probe", check=False)
    if result.returncode:
        print(f"S3 readiness: unavailable (probe exited {result.returncode})", file=sys.stderr)
    return result.returncode


def _storage_check(runner: ComposeRunner, config: AppConfig) -> int:
    check_project = f"paperweave-storage-check-{uuid4().hex[:12]}"
    check_runner = ComposeRunner(runner.config_path, check_project, config)
    check_runner.environment["PW_FILE_VOLUME_NAME"] = f"{check_project}-files"
    check_runner.environment.update({
        "PW_S3_ENDPOINT_URL": "http://storage-check-seaweedfs:8333",
        "PW_S3_BUCKET": f"paperweave-check-{uuid4().hex[:12]}",
        "PW_S3_CHECK_MODE": "round-trip",
        "PW_S3_CHECK_TIMEOUT": "30",
    })
    print("Starting isolated, temporary SeaweedFS storage check.", flush=True)
    try:
        check_runner.run("--profile", "storage-check", "up", "-d", "storage-check-seaweedfs")
        return _run_s3_probe(check_runner, mode="round-trip", profile="storage-check")
    finally:
        try:
            check_runner.run("--profile", "storage-check", "down", "--volumes", "--remove-orphans", check=False)
        finally:
            _remove_ephemeral_s3_config(check_runner)


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.command == "help":
        _parser().print_help()
        return 0
    if args.command == "init":
        return _initialize(args.config)

    try:
        config = load_config(args.config)
    except ConfigError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    if args.command == "config-check":
        print("Configuration is valid.")
        return 0

    runner = ComposeRunner(args.config, args.project_name, config)
    try:
        if args.command == "up":
            runner.start()
            state = _seaweedfs_state(runner)
            if config.storage.backend == "s3" and urlsplit(config.storage.s3_endpoint_url).hostname == "seaweedfs":
                probe_status = _run_s3_probe(runner, mode="readiness", profile="storage-check")
                _storage_summary(config, state, "available" if probe_status == 0 else "unavailable")
                return probe_status
            if config.storage.backend == "local":
                s3_status = "not checked (local backend selected)"
            else:
                s3_status = "not checked (configured endpoint is outside local SeaweedFS)"
            _storage_summary(config, state, s3_status)
        elif args.command == "restart":
            runner.start(force_recreate=True)
            state = _seaweedfs_state(runner)
            if config.storage.backend == "s3" and urlsplit(config.storage.s3_endpoint_url).hostname == "seaweedfs":
                probe_status = _run_s3_probe(runner, mode="readiness", profile="storage-check")
                _storage_summary(config, state, "available" if probe_status == 0 else "unavailable")
                return probe_status
            _storage_summary(config, state, "not checked")
        elif args.command == "down":
            runner.run("down", "--remove-orphans")
        elif args.command == "migrate":
            runner.run("up", "-d", "--wait", "--wait-timeout", "60", "db")
            runner.run("run", "--rm", "migrate")
        elif args.command == "logs":
            runner.run("logs", "--follow", "--tail", "100")
        elif args.command == "ps":
            runner.run("ps")
        elif args.command == "test":
            return _test(runner)
        elif args.command == "storage-check":
            return _storage_check(runner, config)
    except FileNotFoundError:
        print("Docker Compose is required but was not found.", file=sys.stderr)
        return 127
    except subprocess.CalledProcessError as exc:
        return exc.returncode or 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
