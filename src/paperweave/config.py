"""Validated application configuration loaded from one TOML source."""

from __future__ import annotations

import ipaddress
import tomllib
from pathlib import Path
from typing import Literal
from urllib.parse import urlparse

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator, model_validator


class ConfigError(ValueError):
    """A safe, user-facing configuration error without submitted values."""


class StrictSettings(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class AppSettings(StrictSettings):
    name: str = Field(min_length=1, max_length=100)
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


class ApiSettings(StrictSettings):
    host: Literal["0.0.0.0"]
    port: int = Field(ge=1, le=65535)


class UiSettings(StrictSettings):
    host: Literal["0.0.0.0"]
    port: int = Field(ge=1, le=65535)
    api_base_url: str = Field(min_length=1)

    @field_validator("api_base_url")
    @classmethod
    def validate_local_api_url(cls, value: str) -> str:
        parsed = urlparse(value)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            raise ValueError("must be an absolute HTTP(S) URL")
        if parsed.username is not None or parsed.password is not None:
            raise ValueError("must not include user information")
        if parsed.path not in {"", "/"} or parsed.query or parsed.fragment:
            raise ValueError("must not include a path, query, or fragment")
        hostname = parsed.hostname.lower()
        if hostname != "localhost":
            try:
                if not ipaddress.ip_address(hostname).is_loopback:
                    raise ValueError("must target a loopback host")
            except ValueError as exc:
                raise ValueError("must target localhost or a loopback IP") from exc
        try:
            port = parsed.port
        except ValueError as exc:
            raise ValueError("contains an invalid port") from exc
        if port is None or not 1 <= port <= 65535:
            raise ValueError("must include a valid port")
        return value.rstrip("/")


class TimeoutSettings(StrictSettings):
    health_seconds: float = Field(gt=0, le=60)
    request_seconds: float = Field(gt=0, le=300)
    health_poll_seconds: float = Field(gt=0, le=3600)


class DatabaseSettings(StrictSettings):
    host: str = Field(min_length=1)
    port: int = Field(ge=1, le=65535)
    name: str = Field(min_length=1, max_length=63)
    user: str = Field(min_length=1, max_length=63)
    password: str = Field(min_length=1)


class DeploymentSettings(StrictSettings):
    bind_host: str = "127.0.0.1"

    @field_validator("bind_host")
    @classmethod
    def require_loopback(cls, value: str) -> str:
        try:
            address = ipaddress.ip_address(value)
        except ValueError as exc:
            raise ValueError("must be a loopback IP address") from exc
        if not address.is_loopback:
            raise ValueError("must be a loopback IP address")
        return value


class AppConfig(StrictSettings):
    app: AppSettings
    api: ApiSettings
    ui: UiSettings
    timeouts: TimeoutSettings
    database: DatabaseSettings
    deployment: DeploymentSettings

    @model_validator(mode="after")
    def validate_service_ports(self) -> "AppConfig":
        if self.api.port == self.ui.port:
            raise ValueError("api.port and ui.port must be different")
        configured_api_port = urlparse(self.ui.api_base_url).port
        if configured_api_port != self.api.port:
            raise ValueError("ui.api_base_url port must match api.port")
        return self


def load_config(path: str | Path) -> AppConfig:
    """Load and validate TOML, omitting invalid values from error messages."""
    config_path = Path(path)
    try:
        with config_path.open("rb") as file:
            document = tomllib.load(file)
    except FileNotFoundError as exc:
        raise ConfigError(f"Configuration file not found: {config_path}") from exc
    except PermissionError as exc:
        raise ConfigError(f"Configuration file is not readable: {config_path}") from exc
    except tomllib.TOMLDecodeError as exc:
        raise ConfigError(f"Invalid TOML in {config_path}: {exc}") from exc

    try:
        return AppConfig.model_validate(document)
    except ValidationError as exc:
        issues = [
            f"{'.'.join(str(part) for part in issue['loc'])}: {issue['msg']}"
            for issue in exc.errors(include_input=False)
        ]
        raise ConfigError("Invalid configuration: " + "; ".join(issues)) from exc
