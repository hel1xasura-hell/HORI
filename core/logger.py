"""Centralized logging configuration for the Hori bot.

Provides a single entry point, `setup_logging`, that configures a root
logger with both a colorized console handler and a rotating file handler.
"""

from __future__ import annotations

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

LOG_DIRECTORY = Path(__file__).resolve().parent.parent / "logs"
LOG_FILE_PATH = LOG_DIRECTORY / "hori.log"
MAX_LOG_FILE_BYTES = 10 * 1024 * 1024
LOG_FILE_BACKUP_COUNT = 5

_LEVEL_COLORS = {
    logging.DEBUG: "\033[36m",
    logging.INFO: "\033[32m",
    logging.WARNING: "\033[33m",
    logging.ERROR: "\033[31m",
    logging.CRITICAL: "\033[41m",
}
_RESET_COLOR = "\033[0m"


class ColorFormatter(logging.Formatter):
    """Formatter that adds ANSI colors to console log output based on level."""

    def __init__(self, fmt: str, datefmt: str | None = None) -> None:
        """Initialize the formatter.

        Args:
            fmt: The base log message format string.
            datefmt: The date format string used for timestamps.
        """
        super().__init__(fmt=fmt, datefmt=datefmt)

    def format(self, record: logging.LogRecord) -> str:
        """Format a log record, wrapping the level name in an ANSI color code.

        Args:
            record: The log record to format.

        Returns:
            The formatted, colorized log line.
        """
        color = _LEVEL_COLORS.get(record.levelno, "")
        original_levelname = record.levelname
        if color:
            record.levelname = f"{color}{original_levelname}{_RESET_COLOR}"
        formatted = super().format(record)
        record.levelname = original_levelname
        return formatted


def setup_logging(log_level: str = "INFO") -> logging.Logger:
    """Configure and return the root application logger.

    Sets up two handlers on the root logger:
        1. A console handler with colorized, human-readable output.
        2. A rotating file handler that persists logs to `logs/hori.log`.

    Args:
        log_level: The minimum log level to emit, as a string (e.g. "DEBUG").

    Returns:
        The configured root logger instance.
    """
    LOG_DIRECTORY.mkdir(parents=True, exist_ok=True)

    root_logger = logging.getLogger()
    resolved_level = getattr(logging, log_level.upper(), logging.INFO)
    root_logger.setLevel(resolved_level)

    if root_logger.handlers:
        root_logger.handlers.clear()

    console_format = "%(asctime)s | %(levelname)-17s | %(name)s | %(message)s"
    file_format = "%(asctime)s | %(levelname)-8s | %(name)s | %(module)s:%(lineno)d | %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"

    console_handler = logging.StreamHandler(stream=sys.stdout)
    console_handler.setFormatter(ColorFormatter(fmt=console_format, datefmt=date_format))
    console_handler.setLevel(resolved_level)

    file_handler = RotatingFileHandler(
        filename=str(LOG_FILE_PATH),
        maxBytes=MAX_LOG_FILE_BYTES,
        backupCount=LOG_FILE_BACKUP_COUNT,
        encoding="utf-8",
    )
    file_handler.setFormatter(logging.Formatter(fmt=file_format, datefmt=date_format))
    file_handler.setLevel(logging.DEBUG)

    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)

    # Silence overly verbose third-party loggers while keeping our own output rich.
    logging.getLogger("pyrogram").setLevel(logging.WARNING)
    logging.getLogger("pymongo").setLevel(logging.WARNING)
    logging.getLogger("apscheduler").setLevel(logging.WARNING)

    return root_logger


def get_logger(name: str) -> logging.Logger:
    """Return a named logger that inherits the root logging configuration.

    Args:
        name: The dotted module name to associate with the logger, typically
            `__name__` of the calling module.

    Returns:
        A configured `logging.Logger` instance.
    """
    return logging.getLogger(name)
