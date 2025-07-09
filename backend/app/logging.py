"""
This file contains a hack to make typed struct logger without needing
to import two things every time.
"""

from logging import Logger

import structlog
from structlog import get_logger as structlog_get_logger

from app.config import get_config

config = get_config()
LOG_LEVEL = config.get("general.log_level", "INFO")


def get_logger() -> Logger:
    logger: Logger = structlog_get_logger()
    structlog.configure(
        wrapper_class=structlog.make_filtering_bound_logger(LOG_LEVEL),
    )
    return logger
