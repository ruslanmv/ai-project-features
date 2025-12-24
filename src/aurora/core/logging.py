"""Structured logging configuration for Aurora using structlog.

This module sets up production-grade structured logging with JSON formatting
for machine parsing and pretty-printing for development. All logs include
context information like timestamps, log levels, and custom fields.

Examples:
    >>> from aurora.core.logging import setup_logging, get_logger
    >>> setup_logging(log_level="INFO", json_logs=False)
    >>> logger = get_logger(__name__)
    >>> logger.info("agent_started", agent="TaskPlanner", phase="P3")
"""

from __future__ import annotations

import logging
import sys
from typing import Any

import structlog
from rich.console import Console
from rich.logging import RichHandler


def setup_logging(*, log_level: str = "INFO", json_logs: bool = False) -> None:
    """Configure application-wide structured logging.

    This function sets up structlog with appropriate processors based on the
    environment (development vs production). In development, logs are pretty-
    printed to the console. In production, logs are output as JSON for machine
    parsing.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        json_logs: If True, output JSON logs (production). If False, use
            pretty-printed console logs (development).

    Examples:
        >>> setup_logging(log_level="DEBUG", json_logs=False)  # Development
        >>> setup_logging(log_level="INFO", json_logs=True)    # Production
    """
    # Convert string log level to logging constant
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)

    # Shared processors for all logging configurations
    shared_processors: list[Any] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ]

    if json_logs:
        # Production: JSON output for machine parsing
        processors = shared_processors + [
            structlog.processors.JSONRenderer(),
        ]
        # Use standard StreamHandler for JSON
        handler: logging.Handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(
            logging.Formatter("%(message)s")  # structlog handles all formatting
        )
    else:
        # Development: Pretty console output with Rich
        processors = shared_processors + [
            structlog.dev.ConsoleRenderer(
                colors=True,
                exception_formatter=structlog.dev.plain_traceback,
            ),
        ]
        # Use RichHandler for beautiful terminal output
        console = Console(stderr=False, force_terminal=True)
        handler = RichHandler(
            console=console,
            rich_tracebacks=True,
            tracebacks_show_locals=True,
            markup=True,
        )

    # Configure structlog
    structlog.configure(
        processors=processors,  # type: ignore[arg-type]
        wrapper_class=structlog.make_filtering_bound_logger(numeric_level),
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Configure standard logging to work with structlog
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(numeric_level)

    # Silence noisy third-party libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Get a structured logger instance for the given name.

    This function returns a structlog logger that supports structured logging
    with key-value pairs. The logger automatically includes the module name
    in all log entries.

    Args:
        name: Logger name, typically __name__ from the calling module.

    Returns:
        Configured structlog BoundLogger instance.

    Examples:
        >>> logger = get_logger(__name__)
        >>> logger.info("processing_started", file_count=42, user="alice")
        >>> logger.error("validation_failed", error="Invalid input", field="prompt")
    """
    return structlog.get_logger(name)


def log_exception(
    logger: structlog.stdlib.BoundLogger,
    exc: Exception,
    *,
    context: dict[str, Any] | None = None,
) -> None:
    """Log an exception with full context and traceback.

    This helper function logs exceptions with structured context information,
    making it easier to debug issues in production.

    Args:
        logger: The logger instance to use.
        exc: The exception to log.
        context: Additional context information to include in the log.

    Examples:
        >>> logger = get_logger(__name__)
        >>> try:
        ...     risky_operation()
        ... except Exception as e:
        ...     log_exception(logger, e, context={"operation": "refactor", "file": "app.py"})
    """
    log_data = {
        "exception_type": type(exc).__name__,
        "exception_message": str(exc),
        **(context or {}),
    }

    # Include additional details from AuroraException
    if hasattr(exc, "get_context"):
        log_data["exception_context"] = exc.get_context()  # type: ignore[attr-defined]

    logger.error("exception_occurred", **log_data, exc_info=True)
