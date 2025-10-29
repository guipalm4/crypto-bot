"""
System events logging utilities.

Provides structured logging for system lifecycle events:
startup, shutdown, configuration changes, errors, etc.
"""

from typing import Any

from crypto_bot.utils.structured_logger import get_logger

_logger = get_logger(__name__)


def log_startup(
    app_name: str,
    version: str,
    environment: str,
    **context: Any,
) -> None:
    """
    Log application startup event.

    Args:
        app_name: Application name
        version: Application version
        environment: Environment name (development, staging, production)
        **context: Additional context to include in log
    """
    _logger.info(
        "application_startup",
        app_name=app_name,
        version=version,
        environment=environment,
        event_type="system_lifecycle",
        **context,
    )


def log_shutdown(
    reason: str | None = None,
    exit_code: int = 0,
    **context: Any,
) -> None:
    """
    Log application shutdown event.

    Args:
        reason: Reason for shutdown
        exit_code: Exit code
        **context: Additional context to include in log
    """
    _logger.info(
        "application_shutdown",
        reason=reason,
        exit_code=exit_code,
        event_type="system_lifecycle",
        **context,
    )


def log_config_change(
    section: str,
    key: str | None = None,
    old_value: Any = None,
    new_value: Any = None,
    **context: Any,
) -> None:
    """
    Log configuration change event.

    Args:
        section: Configuration section name
        key: Configuration key that changed
        old_value: Previous value
        new_value: New value
        **context: Additional context to include in log
    """
    _logger.info(
        "configuration_changed",
        section=section,
        key=key,
        old_value=str(old_value) if old_value is not None else None,
        new_value=str(new_value) if new_value is not None else None,
        event_type="configuration",
        **context,
    )


def log_error(
    error: Exception,
    context: dict[str, Any] | None = None,
    **extra: Any,
) -> None:
    """
    Log error with full context and traceback.

    Args:
        error: Exception that occurred
        context: Additional context dictionary
        **extra: Additional fields to include in log
    """
    error_context = context or {}
    error_context.update(extra)

    _logger.error(
        "error_occurred",
        error_type=type(error).__name__,
        error_message=str(error),
        event_type="error",
        **error_context,
        exc_info=True,
    )


def log_critical_error(
    error: Exception,
    context: dict[str, Any] | None = None,
    **extra: Any,
) -> None:
    """
    Log critical error with full context and traceback.

    Args:
        error: Exception that occurred
        context: Additional context dictionary
        **extra: Additional fields to include in log
    """
    error_context = context or {}
    error_context.update(extra)

    _logger.critical(
        "critical_error",
        error_type=type(error).__name__,
        error_message=str(error),
        event_type="critical_error",
        **error_context,
        exc_info=True,
    )


def log_system_event(
    event_name: str,
    event_type: str = "system",
    **context: Any,
) -> None:
    """
    Log a generic system event.

    Args:
        event_name: Name of the event
        event_type: Type of event (system, monitoring, etc.)
        **context: Additional context to include in log
    """
    _logger.info(
        event_name,
        event_type=event_type,
        **context,
    )


def log_exception_with_context(
    logger_name: str,
    error: Exception,
    context: dict[str, Any] | None = None,
    level: str = "error",
) -> None:
    """
    Log exception with context using a specific logger.

    Args:
        logger_name: Name of the logger to use
        error: Exception that occurred
        context: Additional context dictionary
        level: Log level (debug, info, warning, error, critical)
    """
    logger = get_logger(logger_name)
    error_context = context or {}

    log_method = getattr(logger, level.lower(), logger.error)

    log_method(
        "exception_caught",
        error_type=type(error).__name__,
        error_message=str(error),
        **error_context,
        exc_info=True,
    )
