
"""
CrowdShield AI — Production Logging Configuration

Provides centralized application logging for:

    AI pipeline
    detection
    tracking
    crowd intelligence
    risk analysis
    response decisions
    routing
    camera services
    backend services

Logs are written to both:
    console
    rotating log file
"""

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional


PROJECT_ROOT = Path(
    r"C:\Users\pabit\CrowdShield-AI"
)

LOG_DIR = (
    PROJECT_ROOT
    / "logs"
)

DEFAULT_LOG_FILE = (
    LOG_DIR
    / "crowdshield.log"
)

DEFAULT_LOG_LEVEL = logging.INFO

LOG_FORMAT = (
    "%(asctime)s | "
    "%(levelname)s | "
    "%(name)s | "
    "%(message)s"
)

DATE_FORMAT = (
    "%Y-%m-%d %H:%M:%S"
)


def ensure_log_directory(
    log_file: Path = DEFAULT_LOG_FILE,
) -> Path:

    log_file = Path(log_file)

    log_file.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    return log_file


def configure_logging(
    level: int = DEFAULT_LOG_LEVEL,
    log_file: Optional[Path] = None,
    max_bytes: int = 5 * 1024 * 1024,
    backup_count: int = 5,
) -> logging.Logger:

    """
    Configure the root CrowdShield logger.

    Parameters
    ----------
    level:
        Logging level.

    log_file:
        Destination log file.

    max_bytes:
        Maximum size of one log file.

    backup_count:
        Number of rotated backup files.

    Returns
    -------
    logging.Logger
        Configured CrowdShield logger.
    """

    if log_file is None:

        log_file = DEFAULT_LOG_FILE

    log_file = ensure_log_directory(
        log_file
    )

    logger = logging.getLogger(
        "crowdshield"
    )

    logger.setLevel(
        level
    )

    logger.propagate = False

    # -------------------------------------------------------------
    # Avoid duplicate handlers when configure_logging() is called
    # repeatedly from notebooks, FastAPI reloads, or tests.
    # -------------------------------------------------------------

    if logger.handlers:

        return logger

    formatter = logging.Formatter(
        fmt=LOG_FORMAT,
        datefmt=DATE_FORMAT,
    )

    # -------------------------------------------------------------
    # Console handler
    # -------------------------------------------------------------

    console_handler = logging.StreamHandler()

    console_handler.setLevel(
        level
    )

    console_handler.setFormatter(
        formatter
    )

    # -------------------------------------------------------------
    # Rotating file handler
    # -------------------------------------------------------------

    file_handler = RotatingFileHandler(
        filename=str(log_file),
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding="utf-8",
    )

    file_handler.setLevel(
        level
    )

    file_handler.setFormatter(
        formatter
    )

    logger.addHandler(
        console_handler
    )

    logger.addHandler(
        file_handler
    )

    logger.info(
        "CrowdShield logging initialized."
    )

    return logger


def get_logger(
    name: str,
) -> logging.Logger:

    """
    Return a named logger under the CrowdShield namespace.

    Example
    -------
    get_logger("pipeline")
    get_logger("risk")
    get_logger("camera")
    """

    if not name:

        raise ValueError(
            "Logger name cannot be empty."
        )

    return logging.getLogger(
        f"crowdshield.{name}"
    )


def set_log_level(
    level: int,
) -> None:

    """
    Change the CrowdShield logger level.
    """

    logger = logging.getLogger(
        "crowdshield"
    )

    logger.setLevel(
        level
    )

    for handler in logger.handlers:

        handler.setLevel(
            level
        )


def shutdown_logging() -> None:

    """
    Flush and close CrowdShield logging handlers.
    """

    logger = logging.getLogger(
        "crowdshield"
    )

    handlers = list(
        logger.handlers
    )

    for handler in handlers:

        try:

            handler.flush()
            handler.close()

        except Exception:
            pass

        logger.removeHandler(
            handler
        )


class PipelineLogger:

    """
    Convenience wrapper for production AI pipeline logging.
    """

    def __init__(
        self,
        component: str,
    ) -> None:

        if not component:

            raise ValueError(
                "Component name cannot be empty."
            )

        self.logger = get_logger(
            component
        )

    def debug(
        self,
        message: str,
    ) -> None:

        self.logger.debug(
            message
        )

    def info(
        self,
        message: str,
    ) -> None:

        self.logger.info(
            message
        )

    def warning(
        self,
        message: str,
    ) -> None:

        self.logger.warning(
            message
        )

    def error(
        self,
        message: str,
    ) -> None:

        self.logger.error(
            message
        )

    def exception(
        self,
        message: str,
    ) -> None:

        self.logger.exception(
            message
        )
