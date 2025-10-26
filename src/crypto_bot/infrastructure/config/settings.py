"""
Configuration Settings Loader.

This module provides functionality to load and validate configuration from YAML files,
environment variables, and Pydantic models.
"""

import os
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Optional

import yaml
from pydantic import BaseModel, Field, ValidationError

from crypto_bot.infrastructure.config.risk_config import RiskConfig
from crypto_bot.utils.logger import get_logger

logger = get_logger(__name__)


class DatabaseConfig(BaseModel):
    """Database configuration."""

    host: str = "localhost"
    port: int = 5432
    name: str = "crypto_bot"
    pool_size: int = 5
    max_overflow: int = 10
    pool_timeout: int = 30
    pool_recycle: int = 1800
    echo: bool = False

    model_config = {"frozen": False}


class RedisConfig(BaseModel):
    """Redis configuration."""

    host: str = "localhost"
    port: int = 6379
    db: int = 0
    socket_timeout: int = 5
    socket_connect_timeout: int = 5
    max_connections: int = 50

    model_config = {"frozen": False}


class AppConfig(BaseModel):
    """Application configuration."""

    name: str = "Crypto Trading Bot"
    version: str = "0.1.0"
    log_level: str = "INFO"

    model_config = {"frozen": False}


class TradingExecutionConfig(BaseModel):
    """Trading execution configuration."""

    order_timeout_seconds: int = Field(30, gt=0)
    retry_attempts: int = Field(3, ge=0)
    retry_delay_seconds: int = Field(2, gt=0)

    model_config = {"frozen": False}


class TradingConfig(BaseModel):
    """Trading configuration."""

    dry_run: bool = True
    max_concurrent_trades: int = Field(5, gt=0)
    default_order_type: str = "limit"
    risk: RiskConfig
    execution: TradingExecutionConfig

    model_config = {"frozen": False}


class ExchangeRateLimits(BaseModel):
    """Exchange rate limits configuration."""

    requests_per_second: int = Field(10, gt=0)
    orders_per_day: int = Field(200000, gt=0)

    model_config = {"frozen": False}


class ExchangeConfig(BaseModel):
    """Individual exchange configuration."""

    enabled: bool = False
    sandbox: bool = True
    rate_limits: ExchangeRateLimits

    model_config = {"frozen": False}


class ExchangesConfig(BaseModel):
    """All exchanges configuration."""

    binance: ExchangeConfig
    coinbase: ExchangeConfig

    model_config = {"frozen": False}


class Settings(BaseModel):
    """
    Main application settings.

    Loads configuration from YAML files and environment variables.
    """

    app: AppConfig
    database: DatabaseConfig
    redis: RedisConfig
    trading: TradingConfig
    exchanges: ExchangesConfig

    model_config = {"frozen": False}


def load_yaml_config(config_path: Path) -> Dict[str, Any]:
    """
    Load configuration from a YAML file.

    Args:
        config_path: Path to the YAML configuration file.

    Returns:
        Dictionary containing configuration data.

    Raises:
        FileNotFoundError: If config file doesn't exist.
        yaml.YAMLError: If YAML parsing fails.
    """
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    with open(config_path) as f:
        config_data = yaml.safe_load(f)

    logger.info(f"Loaded configuration from {config_path}")
    return config_data or {}


def merge_configs(*configs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Deep merge multiple configuration dictionaries.

    Later configs override earlier ones.

    Args:
        *configs: Variable number of configuration dictionaries to merge.

    Returns:
        Merged configuration dictionary.
    """
    result: Dict[str, Any] = {}

    for config in configs:
        for key, value in config.items():
            if (
                isinstance(value, dict)
                and key in result
                and isinstance(result[key], dict)
            ):
                result[key] = merge_configs(result[key], value)
            else:
                result[key] = value

    return result


def apply_env_overrides(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Apply environment variable overrides to configuration.

    Environment variables should be prefixed with CRYPTOBOT_ and use double underscores
    for nested keys (e.g., CRYPTOBOT_DATABASE__HOST).

    Args:
        config: Base configuration dictionary.

    Returns:
        Configuration with environment variable overrides applied.
    """
    prefix = "CRYPTOBOT_"

    for env_key, env_value in os.environ.items():
        if not env_key.startswith(prefix):
            continue

        # Remove prefix and split by double underscore
        config_path = env_key[len(prefix) :].lower().split("__")

        # Navigate to the correct nested dictionary
        current = config
        for key in config_path[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]

        # Set the value
        final_key = config_path[-1]
        current[final_key] = env_value

        logger.debug(f"Applied environment override: {config_path} = {env_value}")

    return config


@lru_cache()
def get_settings(environment: Optional[str] = None) -> Settings:
    """
    Get application settings with caching.

    Loads configuration from YAML files and applies environment variable overrides.

    Args:
        environment: Environment name (development, staging, production).
                    If None, uses CRYPTOBOT_ENV environment variable or defaults to 'development'.

    Returns:
        Validated Settings instance.

    Raises:
        ValidationError: If configuration validation fails.
        FileNotFoundError: If required config files are missing.
    """
    if environment is None:
        environment = os.getenv("CRYPTOBOT_ENV", "development")

    logger.info(f"Loading configuration for environment: {environment}")

    # Determine config directory
    config_dir = (
        Path(__file__).parent.parent.parent.parent.parent / "config" / "environments"
    )

    # Load base configuration
    base_config = load_yaml_config(config_dir / "base.yaml")

    # Load environment-specific configuration
    env_config_path = config_dir / f"{environment}.yaml"
    env_config = load_yaml_config(env_config_path) if env_config_path.exists() else {}

    # Merge configurations
    merged_config = merge_configs(base_config, env_config)

    # Apply environment variable overrides
    final_config = apply_env_overrides(merged_config)

    try:
        settings = Settings(**final_config)
        logger.info("Configuration loaded and validated successfully")
        return settings
    except ValidationError as e:
        logger.error(f"Configuration validation failed: {e}")
        raise


def reload_settings() -> Settings:
    """
    Force reload of settings by clearing cache.

    Returns:
        Newly loaded Settings instance.
    """
    get_settings.cache_clear()
    return get_settings()
