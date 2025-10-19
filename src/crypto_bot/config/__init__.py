"""
Configuration module for the Crypto Trading Bot.

This module provides configuration loading and validation using YAML files
with Pydantic schemas. Supports multiple environments (development, staging,
production) and overlays environment variables for sensitive data.
"""

from crypto_bot.config.loader import ConfigLoader, load_config
from crypto_bot.config.schemas import (
    ApiConfig,
    AppConfig,
    Config,
    CorsConfig,
    DatabaseConfig,
    ExchangeConfig,
    ExchangesConfig,
    ExecutionConfig,
    LoggingConfig,
    MonitoringConfig,
    NotificationChannelConfig,
    NotificationsConfig,
    RateLimitsConfig,
    RedisConfig,
    RiskConfig,
    SecurityConfig,
    StrategiesConfig,
    TradingConfig,
)

# Legacy settings support for backward compatibility
from crypto_bot.config.settings import Settings, settings

__all__ = [
    # Loader
    "ConfigLoader",
    "load_config",
    # Schemas
    "Config",
    "AppConfig",
    "DatabaseConfig",
    "RedisConfig",
    "TradingConfig",
    "RiskConfig",
    "ExecutionConfig",
    "ExchangeConfig",
    "ExchangesConfig",
    "RateLimitsConfig",
    "StrategiesConfig",
    "ApiConfig",
    "CorsConfig",
    "LoggingConfig",
    "MonitoringConfig",
    "NotificationChannelConfig",
    "NotificationsConfig",
    "SecurityConfig",
    # Legacy
    "Settings",
    "settings",
]
