"""Application-wide logging configuration.

Sensitive data (passwords, tokens) must never be logged. All log call
sites in this project are written to respect that rule.
"""
import logging
import sys

from app.config import settings

_LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"


def setup_logging() -> None:
    """Configure root logging handlers/formatters. Call once at startup."""
    level = logging.DEBUG if settings.environment == "development" else logging.INFO

    root = logging.getLogger()
    root.setLevel(level)

    # Avoid duplicate handlers on reload.
    if root.handlers:
        return

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(_LOG_FORMAT))
    root.addHandler(handler)

    # Quiet down noisy third-party loggers.
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Return a module-scoped logger."""
    return logging.getLogger(name)
