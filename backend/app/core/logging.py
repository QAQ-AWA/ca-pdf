"""Logging utilities with structured JSON output."""

from __future__ import annotations

import json
import logging
import logging.config
from datetime import datetime, timezone
from typing import Any

__all__ = ["configure_logging", "JsonFormatter"]

_RESERVED_RECORD_ATTRS = {
    "name",
    "msg",
    "args",
    "levelname",
    "levelno",
    "pathname",
    "filename",
    "module",
    "exc_info",
    "exc_text",
    "stack_info",
    "lineno",
    "funcName",
    "created",
    "msecs",
    "relativeCreated",
    "thread",
    "threadName",
    "processName",
    "process",
}

_LOGGING_CONFIGURED = False


def _json_default(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.astimezone(timezone.utc).isoformat(timespec="milliseconds")
    if isinstance(value, (set, tuple)):
        return list(value)
    return str(value)


class JsonFormatter(logging.Formatter):
    """Format log records as JSON objects."""

    def format(self, record: logging.LogRecord) -> str:  # noqa: D401 - inherited docstring
        log_record: dict[str, Any]
        if isinstance(record.msg, dict):
            log_record = dict(record.msg)
        else:
            log_record = {"message": record.getMessage()}

        log_record.setdefault("level", record.levelname)
        log_record.setdefault("logger", record.name)
        log_record.setdefault(
            "timestamp",
            datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
        )

        if record.exc_info:
            log_record.setdefault("exc_info", self.formatException(record.exc_info))
        if record.stack_info:
            log_record.setdefault("stack_info", record.stack_info)

        for key, value in record.__dict__.items():
            if key in _RESERVED_RECORD_ATTRS or key in log_record:
                continue
            log_record[key] = value

        return json.dumps(log_record, default=_json_default, ensure_ascii=False)


def configure_logging(level: str = "INFO") -> None:
    """Configure application logging with JSON-formatted output."""

    global _LOGGING_CONFIGURED

    normalized_level = level.upper()
    logging_level = logging.getLevelName(normalized_level)
    if not isinstance(logging_level, int):
        logging_level = logging.INFO

    if _LOGGING_CONFIGURED:
        logging.getLogger().setLevel(logging_level)
        return

    logging.config.dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "json": {
                    "()": "app.core.logging.JsonFormatter",
                }
            },
            "handlers": {
                "default": {
                    "class": "logging.StreamHandler",
                    "formatter": "json",
                    "stream": "ext://sys.stdout",
                }
            },
            "root": {
                "handlers": ["default"],
                "level": logging_level,
            },
        }
    )

    for logger_name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        logger = logging.getLogger(logger_name)
        logger.handlers.clear()
        logger.propagate = True
        logger.setLevel(logging_level)

    _LOGGING_CONFIGURED = True
