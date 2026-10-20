"""Command line entry point for local development operations."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

from paperweave.config import AppConfig, ConfigError, load_config


ROOT = Path(__file__).resolve().parents[2]
CONTAINER_CONFIG = "/app/config.toml"


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="paperweave")
    parser.add_argument("--config", type=Path, default=ROOT / "config.toml")
    parser.add_argument("--project-name", default=os.getenv("COMPOSE_PROJECT_NAME", "paperweave"))
    parser.add_argument(
        "command",
        choices=("init", "config-check", "up", "down", "restart", "logs", "ps", "migrate", "test", "help"),
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

    def run(self, *arguments: str, check: bool = True) -> subprocess.CompletedProcess[str]:
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
        return subprocess.run(command, cwd=ROOT, env=self.environment, check=check, text=True)

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
        f"{runner.project_name}-test-{os.getpid()}",
        load_config(runner.config_path),
    )
    try:
        test_runner.run("--profile", "test", "build", "test")
        test_runner.run("--profile", "test", "up", "-d", "--wait", "--wait-timeout", "60", "test-db")
        result = test_runner.run("--profile", "test", "run", "--rm", "--no-deps", "test", check=False)
        return result.returncode
    finally:
        test_runner.run("--profile", "test", "down", "--remove-orphans", check=False)


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
        elif args.command == "restart":
            runner.start(force_recreate=True)
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
    except FileNotFoundError:
        print("Docker Compose is required but was not found.", file=sys.stderr)
        return 127
    except subprocess.CalledProcessError as exc:
        return exc.returncode or 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
