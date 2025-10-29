"""
Logging utility for the crypto bot.

Provides a consistent logging interface across the application.
"""

import logging
import os
import re
import sys
from functools import lru_cache
from typing import Optional

REDACT_PATTERNS = [
    # Exchange API credentials
    re.compile(r"(api[_-]?key\s*[=:]\s*)([^\s,;]+)", re.IGNORECASE),
    re.compile(r"(api[_-]?secret\s*[=:]\s*)([^\s,;]+)", re.IGNORECASE),
    re.compile(r"(passphrase\s*[=:]\s*)([^\s,;]+)", re.IGNORECASE),
    # Database credentials
    re.compile(r"(password\s*[=:]\s*)([^\s,;]+)", re.IGNORECASE),
    re.compile(r"(postgres[_-]?password\s*[=:]\s*)([^\s,;]+)", re.IGNORECASE),
    # JWT and encryption
    re.compile(r"(jwt[_-]?secret\s*[=:]\s*)([^\s,;]+)", re.IGNORECASE),
    re.compile(r"(encryption[_-]?key\s*[=:]\s*)([^\s,;]+)", re.IGNORECASE),
    # Notification tokens
    re.compile(r"(telegram[_-]?bot[_-]?token\s*[=:]\s*)([^\s,;]+)", re.IGNORECASE),
    re.compile(r"(discord[_-]?webhook\s*[=:]\s*)([^\s,;]+)", re.IGNORECASE),
    re.compile(r"(smtp[_-]?password\s*[=:]\s*)([^\s,;]+)", re.IGNORECASE),
    # General patterns
    re.compile(r"(token\s*[=:]\s*)([^\s,;]+)", re.IGNORECASE),
    re.compile(r"(secret\s*[=:]\s*)([^\s,;]+)", re.IGNORECASE),
]


class _RedactingFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:  # noqa: D401
        msg = super().format(record)
        for pattern in REDACT_PATTERNS:
            msg = pattern.sub(r"\1[REDACTED]", msg)
        return msg


@lru_cache(maxsize=None)
def get_logger(name: str, level: Optional[int] = None) -> logging.Logger:
    """
    Get a logger instance with the given name.

    Args:
        name: Logger name, typically __name__ of the calling module.
        level: Optional logging level (e.g., logging.DEBUG, logging.INFO).
               If not provided, uses INFO as default.

    Returns:
        Configured logger instance.
    """
    logger = logging.getLogger(name)

    # Set level
    if level is None:
        level = logging.INFO
    logger.setLevel(level)

    # Avoid adding handlers multiple times
    if not logger.handlers:
        # Create console handler
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(level)

        # Create formatter
        formatter: logging.Formatter
        if os.getenv("CRYPTOBOT_LOG_JSON", "false").lower() in {"1", "true", "yes"}:
            formatter = logging.Formatter(
                fmt='{"ts":"%(asctime)s","logger":"%(name)s","lvl":"%(levelname)s","msg":"%(message)s"}',
                datefmt="%Y-%m-%dT%H:%M:%S%z",
            )
        else:
            formatter = _RedactingFormatter(
                fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        handler.setFormatter(formatter)

        # Add handler to logger
        logger.addHandler(handler)

    return logger
