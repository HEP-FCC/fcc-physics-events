"""
This file contains a hack to make typed struct logger without needing
to import two things every time.
"""

import logging
from logging import Logger
from typing import cast

import structlog

from app.config import get_config

config = get_config()
LOG_LEVEL = config.get("general.log_level", "INFO").upper()

# Flag to track if logging has been configured
_logging_configured = False


def setup_logging() -> None:
    """
    Set up structured logging for the application.
    This should be called once at application startup.
    """
    global _logging_configured

    # Avoid reconfiguring if already set up
    if _logging_configured:
        return

    # Get the root logger and completely clear it
    root_logger = logging.getLogger()

    # Clear ALL handlers to ensure no duplicates
    root_logger.handlers.clear()

    # Set the level
    root_logger.setLevel(LOG_LEVEL)

    # Clear any existing structlog configuration
    structlog.reset_defaults()

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M:%S.%f"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.dev.ConsoleRenderer(
                colors=False,
            ),
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # Get the root logger and set its level
    root_logger = logging.getLogger()
    root_logger.setLevel(LOG_LEVEL)

    # Remove any existing handlers to avoid duplicates
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Add a new handler that uses structlog
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(message)s"))
    root_logger.addHandler(handler)

    # Prevent propagation to avoid any potential parent logger duplication
    root_logger.propagate = False

    # Disable uvicorn access logging to prevent duplicates
    uvicorn_access = logging.getLogger("uvicorn.access")
    uvicorn_access.disabled = True
    uvicorn_access.propagate = False

    # Also disable uvicorn error logger's access-like messages
    uvicorn_error = logging.getLogger("uvicorn.error")
    uvicorn_error.setLevel(logging.WARNING)  # Only show warnings and errors
    uvicorn_error.propagate = False

    # Mark as configured
    _logging_configured = True


def get_logger(name: str | None = None) -> Logger:
    """
    Get a logger with the specified name.
    """
    return cast(Logger, structlog.get_logger(name))
