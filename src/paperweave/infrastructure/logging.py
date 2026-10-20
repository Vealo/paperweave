"""Reusable structured logging setup and event helpers for PaperWeave."""

from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
from datetime import datetime, timezone
import json
import logging
import os
import re
import shlex
import sys
from typing import Any


_SENSITIVE_KEY = re.compile(
    r"password|secret|token|cookie|authorization|prompt|content|body|"
    r"manuscript|document_text|selected_text|email|raw_response",
    re.IGNORECASE,
)
_LEVEL_COLORS = {
    "DEBUG": "\x1b[2m",
    "INFO": "\x1b[0m",
    "WARNING": "\x1b[33m",
    "ERROR": "\x1b[31m",
    "CRITICAL": "\x1b[1;31m",
}
_RESET = "\x1b[0m"
_LOG_CONTEXT: ContextVar[dict[str, Any]] = ContextVar("paperweave_log_context", default={})


def _safe_fields(fields: dict[str, Any]) -> dict[str, Any]:
    safe: dict[str, Any] = {}
    for key, value in fields.items():
        if _SENSITIVE_KEY.search(key):
            safe[key] = "[REDACTED]"
        elif isinstance(value, dict):
            safe[key] = _safe_fields(value)
        elif isinstance(value, (list, tuple)):
            safe[key] = [
                _safe_fields(item) if isinstance(item, dict) else item
                for item in value
            ]
        else:
            safe[key] = value
    return safe


@contextmanager
def log_context(**fields: Any):
    """Bind safe operation fields to all events emitted in the current context."""

    token = _LOG_CONTEXT.set({**_LOG_CONTEXT.get(), **fields})
    try:
        yield
    finally:
        _LOG_CONTEXT.reset(token)


class JsonLineFormatter(logging.Formatter):
    """Render one structured JSON object per record, without terminal codes."""

    def format(self, record: logging.LogRecord) -> str:
        event = getattr(record, "event", record.name)
        fields = _safe_fields({**_LOG_CONTEXT.get(), **getattr(record, "event_fields", {})})
        payload: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created, timezone.utc)
            .isoformat(timespec="milliseconds")
            .replace("+00:00", "Z"),
            "level": record.levelname,
            "service": os.getenv("PW_SERVICE", "api"),
            "event": event,
            "message": record.getMessage(),
        }
        payload.update(fields)
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False, separators=(",", ":"), default=str)


class ConsoleFormatter(logging.Formatter):
    """Readable single-line terminal rendering with shared severity colors."""

    def format(self, record: logging.LogRecord) -> str:
        event = getattr(record, "event", record.name)
        fields = _safe_fields({**_LOG_CONTEXT.get(), **getattr(record, "event_fields", {})})
        level = record.levelname
        color = _LEVEL_COLORS.get(level, "")
        level_text = f"{color}{level}{_RESET}" if color else level
        suffix = " ".join(f"{key}={shlex.quote(str(value))}" for key, value in fields.items())
        timestamp = datetime.fromtimestamp(record.created, timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")
        line = f"{timestamp} {os.getenv('PW_SERVICE', 'api')} {level_text} {event}: {record.getMessage()}"
        if suffix:
            line = f"{line} {suffix}"
        if record.exc_info:
            line = f"{line}\n{self.formatException(record.exc_info)}"
        return line


def configure_logging(*, service: str, level: str | None = None) -> None:
    """Configure the shared root pipeline before application components log."""

    os.environ["PW_SERVICE"] = service
    selected_level = (level or os.getenv("PW_LOG_LEVEL", "INFO")).upper()
    stream = sys.stdout
    handler = logging.StreamHandler(stream)
    use_color = stream.isatty() and os.getenv("NO_COLOR") is None
    handler.setFormatter(ConsoleFormatter() if use_color else JsonLineFormatter())

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(selected_level)

    # Uvicorn's own handlers otherwise bypass the shared formatter.
    for name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        logger = logging.getLogger(name)
        logger.handlers.clear()
        logger.propagate = True


def log_event(
    logger: logging.Logger,
    level: int,
    event: str,
    message: str,
    **fields: Any,
) -> None:
    """Emit an event through the common schema and redaction pipeline."""

    logger.log(level, message, extra={"event": event, "event_fields": fields})
