"""
Structured logging configuration using structlog.

This module sets up structured logging for the entire application.
"""

import logging
import sys
from typing import Any
import structlog
from structlog.types import EventDict, Processor


def add_app_context(
    logger: logging.Logger,
    method_name: str,
    event_dict: EventDict
) -> EventDict:
    """
    Add application context to log entries.

    Args:
        logger: Logger instance
        method_name: Method name
        event_dict: Event dictionary

    Returns:
        Modified event dictionary
    """
    event_dict["app"] = "okta-mcp-server"
    return event_dict


def configure_logging(log_level: str = "INFO") -> None:
    """
    Configure structured logging for the application.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    # Configure structlog processors
    processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        add_app_context,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ]

    # Add JSON rendering for production, console for development
    if sys.stderr.isatty():
        # Development: colored console output
        processors.append(structlog.dev.ConsoleRenderer())
    else:
        # Production: JSON output
        processors.append(structlog.processors.JSONRenderer())

    # Configure structlog
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, log_level.upper())
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Configure standard logging to use structlog
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, log_level.upper()),
    )


def get_logger(name: str) -> structlog.BoundLogger:
    """
    Get a logger instance.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Bound logger instance
    """
    return structlog.get_logger(name)


class LoggerMixin:
    """Mixin class to add logging to any class."""

    @property
    def logger(self) -> structlog.BoundLogger:
        """Get logger for this class."""
        if not hasattr(self, "_logger"):
            self._logger = get_logger(self.__class__.__name__)
        return self._logger
