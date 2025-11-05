"""Logging configuration."""

import logging
import sys
from typing import Any

import structlog
from structlog.types import Processor

from app.config import settings


def setup_logging() -> None:
    """Setup structured logging."""
    processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    if settings.LOG_FORMAT == "json":
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.extend(
            [
                structlog.dev.ConsoleRenderer(),
            ]
        )

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(
            logging.getLevelName(settings.LOG_LEVEL)
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Configure standard logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, settings.LOG_LEVEL.upper()),
    )


def get_logger(*args: Any, **kwargs: Any) -> structlog.BoundLogger:
    """Get a structured logger instance."""
    return structlog.get_logger(*args, **kwargs)

