"""
Logging utility for the crypto bot.

Provides a consistent logging interface across the application.
"""

import logging
import sys
from functools import lru_cache
from typing import Optional


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
        formatter = logging.Formatter(
            fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)

        # Add handler to logger
        logger.addHandler(handler)

    return logger
