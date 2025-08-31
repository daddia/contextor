"""Structured logging configuration for Contextor."""

import logging
import os
import sys
from typing import Any

import structlog
from structlog.processors import TimeStamper


def configure_logging(
    level: str = "INFO", json_output: bool = None, include_context: bool = True
) -> None:
    """Configure structured logging for Contextor.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR)
        json_output: Force JSON output (defaults to True for production)
        include_context: Include contextual information in logs
    """
    # Determine if we should use JSON output
    if json_output is None:
        # Use JSON in production/CI environments, human-readable in development
        json_output = bool(
            os.getenv("CI")
            or os.getenv("CONTEXTOR_JSON_LOGS")
            or os.getenv("ENVIRONMENT", "").lower() in ("production", "prod", "staging")
        )

    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s", stream=sys.stdout, level=getattr(logging, level.upper())
    )

    # Configure processors based on output format
    processors = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        TimeStamper(fmt="iso", utc=True),
    ]

    if include_context:
        processors.append(
            structlog.processors.CallsiteParameterAdder(
                parameters=[
                    structlog.processors.CallsiteParameter.FILENAME,
                    structlog.processors.CallsiteParameter.FUNC_NAME,
                    structlog.processors.CallsiteParameter.LINENO,
                ]
            )
        )

    if json_output:
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.extend(
            [
                structlog.dev.ConsoleRenderer(colors=True),
            ]
        )

    # Configure structlog
    structlog.configure(
        processors=processors,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


def get_logger(name: str = None) -> structlog.stdlib.BoundLogger:
    """Get a configured logger instance.

    Args:
        name: Logger name (defaults to caller's module)

    Returns:
        Configured structlog logger
    """
    return structlog.get_logger(name)


def log_operation(
    logger: structlog.stdlib.BoundLogger, operation: str, **context: Any
) -> dict[str, Any]:
    """Create a logging context for an operation.

    Args:
        logger: Logger instance
        operation: Operation name
        **context: Additional context fields

    Returns:
        Context dictionary for operation tracking
    """
    import time

    op_context = {"operation": operation, "start_time": time.time(), **context}

    logger.info("Operation started", **op_context)
    return op_context


def log_operation_complete(
    logger: structlog.stdlib.BoundLogger,
    context: dict[str, Any],
    success: bool = True,
    **additional_context: Any,
) -> None:
    """Log completion of an operation.

    Args:
        logger: Logger instance
        context: Context from log_operation
        success: Whether operation succeeded
        **additional_context: Additional context fields
    """
    import time

    duration = time.time() - context["start_time"]

    final_context = {
        **context,
        "duration_seconds": round(duration, 3),
        "success": success,
        **additional_context,
    }

    if success:
        logger.info("Operation completed", **final_context)
    else:
        logger.error("Operation failed", **final_context)


def log_file_operation(
    logger: structlog.stdlib.BoundLogger, operation: str, file_path: str, **context: Any
) -> dict[str, Any]:
    """Create a logging context for a file operation.

    Args:
        logger: Logger instance
        operation: Operation name
        file_path: Path to the file being processed
        **context: Additional context fields

    Returns:
        Context dictionary for operation tracking
    """
    from pathlib import Path

    path = Path(file_path)

    return log_operation(
        logger,
        operation,
        file_path=str(file_path),
        file_name=path.name,
        file_size_bytes=path.stat().st_size if path.exists() else None,
        **context,
    )
