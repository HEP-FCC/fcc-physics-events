"""
This file contains a hack to make typed struct logger without needing
to import two things every time.
"""

from logging import Logger

from structlog import get_logger as structlog_get_logger


def get_logger() -> Logger:
    logger: Logger = structlog_get_logger()
    return logger
