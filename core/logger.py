from __future__ import annotations

import contextvars
import json
import logging
from logging.config import dictConfig


_request_id_var: contextvars.ContextVar[str] = contextvars.ContextVar("request_id", default="-")
_request_path_var: contextvars.ContextVar[str] = contextvars.ContextVar("request_path", default="-")


class ContextFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = _request_id_var.get("-")
        record.path = _request_path_var.get("-")
        return True


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname.lower(),
            "logger": record.name,
            "request_id": getattr(record, "request_id", "-"),
            "path": getattr(record, "path", "-"),
            "message": record.getMessage(),
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


def configure_logging() -> None:
    dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "filters": {
                "context": {
                    "()": ContextFilter,
                }
            },
            "formatters": {
                "json": {
                    "()": JsonFormatter,
                }
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "formatter": "json",
                    "filters": ["context"],
                }
            },
            "root": {
                "level": "INFO",
                "handlers": ["console"],
            },
            "loggers": {
                "uvicorn": {
                    "level": "INFO",
                    "handlers": ["console"],
                    "propagate": False,
                },
                "uvicorn.error": {
                    "level": "INFO",
                    "handlers": ["console"],
                    "propagate": False,
                },
                "uvicorn.access": {
                    "level": "INFO",
                    "handlers": ["console"],
                    "propagate": False,
                },
            },
        }
    )


def set_request_context(request_id: str, path: str) -> tuple[contextvars.Token[str], contextvars.Token[str]]:
    request_id_token = _request_id_var.set(request_id)
    request_path_token = _request_path_var.set(path)
    return request_id_token, request_path_token


def reset_request_context(tokens: tuple[contextvars.Token[str], contextvars.Token[str]]) -> None:
    request_id_token, request_path_token = tokens
    _request_path_var.reset(request_path_token)
    _request_id_var.reset(request_id_token)
