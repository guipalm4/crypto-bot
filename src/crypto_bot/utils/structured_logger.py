"""
Structured logging utility using structlog.

Provides JSON logging with redaction of sensitive data, log rotation,
and per-module configuration.
"""

import logging
import re
import sys
from functools import lru_cache
from pathlib import Path
from typing import Any, Callable, Sequence, cast

import structlog
from structlog.processors import JSONRenderer
from structlog.stdlib import (
    BoundLogger,
    LoggerFactory,
    PositionalArgumentsFormatter,
    ProcessorFormatter,
    add_log_level,
    add_logger_name,
    filter_by_level,
)

# Redaction patterns (same as in logger.py)
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


def _redact_sensitive_data(
    logger: logging.Logger, method_name: str, event_dict: dict[str, Any]
) -> dict[str, Any]:
    """
    Redact sensitive data from log event dictionary.

    Args:
        logger: Logger instance
        method_name: Log method name
        event_dict: Event dictionary to process

    Returns:
        Event dictionary with sensitive values redacted
    """
    # Redact in event message
    if "event" in event_dict:
        msg = str(event_dict["event"])
        for pattern in REDACT_PATTERNS:
            msg = pattern.sub(r"\1[REDACTED]", msg)
        event_dict["event"] = msg

    # Redact in all string values
    for key, value in list(event_dict.items()):
        if isinstance(value, str):
            redacted_value = value
            for pattern in REDACT_PATTERNS:
                redacted_value = pattern.sub(r"\1[REDACTED]", redacted_value)
            event_dict[key] = redacted_value

    return event_dict


def _parse_size(size_str: str) -> int:
    """
    Parse size string (e.g., "10MB", "500KB") to bytes.

    Args:
        size_str: Size string with unit (KB, MB, GB)

    Returns:
        Size in bytes
    """
    size_str = size_str.upper().strip()
    multipliers = {"KB": 1024, "MB": 1024**2, "GB": 1024**3}

    for unit, multiplier in multipliers.items():
        if size_str.endswith(unit):
            return int(float(size_str[:-2]) * multiplier)

    # Default to bytes if no unit
    return int(size_str)


def configure_structlog(
    level: str = "INFO",
    format: str = "json",
    output: str = "console",
    file_path: str = "./data/logs/crypto-bot.log",
    max_size: str = "10MB",
    backup_count: int = 5,
    per_module: bool = False,
) -> None:
    """
    Configure structlog with JSON rendering, redaction, and file rotation.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format: Output format ("json" or "pretty")
        output: Output destination ("console", "file", or "both")
        file_path: Base path for log files
        max_size: Maximum file size before rotation (e.g., "10MB")
        backup_count: Number of backup files to keep
        per_module: If True, create separate log files per module
    """
    # Convert level string to int
    log_level = getattr(logging, level.upper(), logging.INFO)

    # Shared processors
    shared_processors = [
        filter_by_level,
        add_log_level,
        add_logger_name,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        PositionalArgumentsFormatter(),
        _redact_sensitive_data,  # Custom redaction processor
        ProcessorFormatter.wrap_for_formatter,
    ]

    # Choose renderer based on format for ProcessorFormatter
    if format == "json":
        renderer: Any = JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer(colors=sys.stderr.isatty())

    # Configure structlog
    # Cast needed due to structlog stubs typing limitations
    structlog.configure(
        processors=cast(Sequence[Callable[..., Any]], shared_processors),
        wrapper_class=BoundLogger,
        logger_factory=LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Clear existing handlers to avoid duplicates
    root_logger.handlers.clear()

    # Console handler (if needed)
    if output in ("console", "both"):
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)
        # Cast needed due to structlog stubs typing limitations
        console_formatter = ProcessorFormatter(
            foreign_pre_chain=cast(
                Sequence[Callable[..., Any]], shared_processors[:-1]
            ),  # Exclude wrap_for_formatter
            processors=[
                ProcessorFormatter.remove_processors_meta,
                renderer,
            ],
        )
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)

    # File handler with rotation (if needed)
    if output in ("file", "both"):
        log_path = Path(file_path)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        max_bytes = _parse_size(max_size)

        if per_module:
            # Per-module logging will be handled by get_logger
            # Here we just set up the base configuration
            pass
        else:
            # Single file with rotation
            from logging.handlers import RotatingFileHandler

            file_handler = RotatingFileHandler(
                filename=str(log_path),
                maxBytes=max_bytes,
                backupCount=backup_count,
                encoding="utf-8",
            )
            file_handler.setLevel(log_level)
            # Cast needed due to structlog stubs typing limitations
            file_formatter = ProcessorFormatter(
                foreign_pre_chain=cast(
                    Sequence[Callable[..., Any]], shared_processors[:-1]
                ),
                processors=[
                    ProcessorFormatter.remove_processors_meta,
                    JSONRenderer() if format == "json" else renderer,
                ],
            )
            file_handler.setFormatter(file_formatter)
            root_logger.addHandler(file_handler)

    # Store configuration for per-module loggers
    global _logging_config
    _logging_config = {
        "level": log_level,
        "format": format,
        "file_path": file_path,
        "max_size": max_size,
        "backup_count": backup_count,
        "per_module": per_module,
        "shared_processors": shared_processors,
        "renderer": renderer,
    }


# Global config storage
_logging_config: dict[str, Any] | None = None


@lru_cache(maxsize=None)
def get_logger(name: str) -> BoundLogger:
    """
    Get a structured logger instance with optional per-module file output.

    Args:
        name: Logger name, typically __name__ of the calling module.

    Returns:
        Configured structlog logger instance.
    """
    logger = structlog.get_logger(name)

    # If per-module logging is enabled, add file handler for this module
    if _logging_config and _logging_config.get("per_module", False):
        module_logger = logging.getLogger(name)

        # Avoid duplicate handlers
        if not module_logger.handlers:
            log_path = Path(_logging_config["file_path"])
            log_dir = log_path.parent
            log_dir.mkdir(parents=True, exist_ok=True)

            # Create module-specific log file
            module_name = name.replace(".", "_").replace("/", "_")
            module_log_path = log_dir / f"{module_name}.log"

            from logging.handlers import RotatingFileHandler

            max_bytes = _parse_size(_logging_config["max_size"])

            file_handler = RotatingFileHandler(
                filename=str(module_log_path),
                maxBytes=max_bytes,
                backupCount=_logging_config["backup_count"],
                encoding="utf-8",
            )
            file_handler.setLevel(_logging_config["level"])

            shared_processors = _logging_config["shared_processors"]
            file_formatter = ProcessorFormatter(
                foreign_pre_chain=shared_processors[:-1],
                processors=[
                    ProcessorFormatter.remove_processors_meta,
                    (
                        JSONRenderer()
                        if _logging_config["format"] == "json"
                        else _logging_config["renderer"]
                    ),
                ],
            )
            file_handler.setFormatter(file_formatter)
            module_logger.addHandler(file_handler)
            module_logger.setLevel(_logging_config["level"])
            module_logger.propagate = False  # Don't propagate to root

    return logger


# Initialize structlog on module import
_configured = False


def initialize_logging(
    level: str = "INFO",
    format: str = "json",
    output: str = "console",
    file_path: str = "./data/logs/crypto-bot.log",
    max_size: str = "10MB",
    backup_count: int = 5,
    per_module: bool = False,
) -> None:
    """
    Initialize structured logging system with rotation and per-module support.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format: Output format ("json" or "pretty")
        output: Output destination ("console", "file", or "both")
        file_path: Base path for log files
        max_size: Maximum file size before rotation (e.g., "10MB")
        backup_count: Number of backup files to keep
        per_module: If True, create separate log files per module
    """
    global _configured
    if not _configured:
        configure_structlog(
            level=level,
            format=format,
            output=output,
            file_path=file_path,
            max_size=max_size,
            backup_count=backup_count,
            per_module=per_module,
        )
        _configured = True


def initialize_from_config(logging_config: Any) -> None:
    """
    Initialize structured logging from LoggingConfig object.

    Args:
        logging_config: LoggingConfig instance from config schema
    """
    from crypto_bot.config.schemas import LoggingConfig

    if not isinstance(logging_config, LoggingConfig):
        raise TypeError("logging_config must be a LoggingConfig instance")

    # Determine output mode from handlers
    if "console" in logging_config.handlers and "file" in logging_config.handlers:
        output = "both"
    elif "file" in logging_config.handlers:
        output = "file"
    else:
        output = "console"

    initialize_logging(
        level=logging_config.level,
        format=logging_config.format,
        output=output,
        file_path=logging_config.file_path,
        max_size=logging_config.max_size,
        backup_count=logging_config.backup_count,
        per_module=False,  # Not in current LoggingConfig schema
    )
