"""
Configuration loader for YAML files with environment variable overlay.
"""

import os
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv

from crypto_bot.config.schemas import Config


class ConfigLoader:
    """
    Loads configuration from YAML files and overlays with environment variables.

    Supports multiple profiles (development, staging, production).
    Base configuration is loaded first, then environment-specific config,
    finally environment variables for sensitive data.
    """

    def __init__(self, config_dir: Path | None = None, env: str | None = None) -> None:
        """
        Initialize the configuration loader.

        Args:
            config_dir: Path to configuration directory.
                       Defaults to 'config' in project root.
            env: Environment name (development, staging, production).
                Defaults to ENVIRONMENT env var or 'development'.
        """
        # Load .env file first
        load_dotenv()

        # Determine config directory
        if config_dir is None:
            # Assume config dir is at project root
            project_root = Path(__file__).parent.parent.parent.parent
            config_dir = project_root / "config"

        self.config_dir = config_dir
        self.environments_dir = config_dir / "environments"

        # Determine environment
        if env is None:
            env = os.getenv("ENVIRONMENT", "development")

        self.environment = env.lower()

        # Validate environment
        valid_envs = ["development", "staging", "production"]
        if self.environment not in valid_envs:
            raise ValueError(
                f"Invalid environment '{self.environment}'. "
                f"Must be one of: {', '.join(valid_envs)}"
            )

    def _load_yaml(self, file_path: Path) -> dict[str, Any]:
        """Load YAML file and return as dictionary."""
        if not file_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {file_path}")

        with open(file_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)

        return data or {}

    def _deep_merge(
        self, base: dict[str, Any], override: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Deep merge two dictionaries.

        Values from 'override' take precedence over 'base'.
        Nested dictionaries are merged recursively.
        """
        result = base.copy()

        for key, value in override.items():
            if (
                key in result
                and isinstance(result[key], dict)
                and isinstance(value, dict)
            ):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value

        return result

    def _overlay_env_vars(self, config: dict[str, Any]) -> dict[str, Any]:
        """
        Overlay environment variables onto configuration.

        Environment variables for sensitive data:
        - DATABASE_USER, DATABASE_PASSWORD
        - REDIS_PASSWORD
        - BINANCE_API_KEY, BINANCE_API_SECRET
        - COINBASE_API_KEY, COINBASE_API_SECRET, COINBASE_PASSPHRASE
        - ENCRYPTION_KEY, JWT_SECRET
        - TELEGRAM_TOKEN, TELEGRAM_CHAT_ID
        - DISCORD_WEBHOOK_URL
        - EMAIL_SMTP_PASSWORD
        """
        # Database credentials
        if db_user := os.getenv("DATABASE_USER"):
            config.setdefault("database", {})["user"] = db_user
        if db_password := os.getenv("DATABASE_PASSWORD"):
            config.setdefault("database", {})["password"] = db_password

        # Redis password
        if redis_password := os.getenv("REDIS_PASSWORD"):
            config.setdefault("redis", {})["password"] = redis_password

        # Binance credentials
        if binance_key := os.getenv("BINANCE_API_KEY"):
            config.setdefault("exchanges", {}).setdefault("binance", {})[
                "api_key"
            ] = binance_key
        if binance_secret := os.getenv("BINANCE_API_SECRET"):
            config.setdefault("exchanges", {}).setdefault("binance", {})[
                "api_secret"
            ] = binance_secret

        # Coinbase credentials
        if coinbase_key := os.getenv("COINBASE_API_KEY"):
            config.setdefault("exchanges", {}).setdefault("coinbase", {})[
                "api_key"
            ] = coinbase_key
        if coinbase_secret := os.getenv("COINBASE_API_SECRET"):
            config.setdefault("exchanges", {}).setdefault("coinbase", {})[
                "api_secret"
            ] = coinbase_secret
        if coinbase_passphrase := os.getenv("COINBASE_PASSPHRASE"):
            config.setdefault("exchanges", {}).setdefault("coinbase", {})[
                "passphrase"
            ] = coinbase_passphrase

        # Security
        if encryption_key := os.getenv("ENCRYPTION_KEY"):
            config.setdefault("security", {})["encryption_key"] = encryption_key
        if jwt_secret := os.getenv("JWT_SECRET"):
            config.setdefault("security", {})["jwt_secret"] = jwt_secret

        # Telegram
        if telegram_token := os.getenv("TELEGRAM_BOT_TOKEN"):
            config.setdefault("notifications", {}).setdefault("telegram", {})[
                "token"
            ] = telegram_token
        if telegram_chat_id := os.getenv("TELEGRAM_CHAT_ID"):
            config.setdefault("notifications", {}).setdefault("telegram", {})[
                "chat_id"
            ] = telegram_chat_id

        # Discord
        if discord_webhook := os.getenv("DISCORD_WEBHOOK_URL"):
            config.setdefault("notifications", {}).setdefault("discord", {})[
                "webhook_url"
            ] = discord_webhook

        # Email
        if email_password := os.getenv("EMAIL_SMTP_PASSWORD"):
            config.setdefault("notifications", {}).setdefault("email", {})[
                "token"
            ] = email_password

        return config

    def load(self) -> Config:
        """
        Load configuration from YAML files and environment variables.

        Returns:
            Config: Validated configuration object.

        Raises:
            FileNotFoundError: If configuration files are not found.
            ValueError: If configuration validation fails.
        """
        # Load base configuration
        base_file = self.environments_dir / "base.yaml"
        config_data = self._load_yaml(base_file)

        # Load environment-specific configuration
        env_file = self.environments_dir / f"{self.environment}.yaml"
        if env_file.exists():
            env_config = self._load_yaml(env_file)
            config_data = self._deep_merge(config_data, env_config)

        # Overlay environment variables
        config_data = self._overlay_env_vars(config_data)

        # Validate and create Config object
        try:
            config = Config(**config_data)
        except Exception as e:
            raise ValueError(f"Configuration validation failed: {e}") from e

        return config


def load_config(config_dir: Path | None = None, env: str | None = None) -> Config:
    """
    Convenience function to load configuration.

    Args:
        config_dir: Path to configuration directory.
        env: Environment name.

    Returns:
        Config: Validated configuration object.
    """
    loader = ConfigLoader(config_dir=config_dir, env=env)
    return loader.load()
