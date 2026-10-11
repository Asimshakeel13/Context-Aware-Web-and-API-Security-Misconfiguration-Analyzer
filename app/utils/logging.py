"""Application logging configuration.

Provides a single :func:`configure_logging` entry point and a :func:`get_logger`
helper. Logs are structured (key=value) where practical so scan progress is
greppable. Secret redaction is handled separately in ``utils/redaction.py`` and
must be applied *before* values reach the logger.
"""
from __future__ import annotations

import logging
import sys

from app.config import settings

_CONFIGURED = False

_LEVEL = logging.DEBUG if settings.DEBUG else logging.INFO


def configure_logging() -> None:
    """Configure the root logger once, idempotently."""
    global _CONFIGURED
    if _CONFIGURED:
        return

    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        fmt="%(asctime)s %(levelname)-8s %(name)s :: %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S%z",
    )
    handler.setFormatter(formatter)

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(_LEVEL)

    # Tame noisy third-party loggers.
    for noisy in ("httpx", "httpcore", "urllib3", "asyncio"):
        logging.getLogger(noisy).setLevel(logging.WARNING)

    _CONFIGURED = True


def get_logger(name: str) -> logging.Logger:
    """Return a module-scoped logger, configuring logging on first use."""
    if not _CONFIGURED:
        configure_logging()
    return logging.getLogger(name)
