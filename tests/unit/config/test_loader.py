"""
Unit tests for configuration loader.
"""

import os
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, Dict

import pytest
import yaml

from crypto_bot.config.loader import ConfigLoader, load_config
from crypto_bot.config.schemas import Config


@pytest.fixture
def temp_config_dir() -> Any:
    """Create a temporary config directory with test files."""
    with TemporaryDirectory() as tmpdir:
        config_dir = Path(tmpdir)
        env_dir = config_dir / "environments"
        env_dir.mkdir()

        # Create base config
        base_config = {
            "app": {"name": "Test Bot", "version": "1.0.0", "log_level": "INFO"},
            "database": {"host": "localhost", "port": 5432},
            "trading": {"dry_run": True, "max_concurrent_trades": 5},
            "security": {"encryption_key": "test_key_from_yaml"},
        }
        with open(env_dir / "base.yaml", "w") as f:
            yaml.dump(base_config, f)

        # Create development config
        dev_config = {
            "app": {"log_level": "DEBUG"},
            "database": {"echo": True},
            "trading": {"max_concurrent_trades": 2},
        }
        with open(env_dir / "development.yaml", "w") as f:
            yaml.dump(dev_config, f)

        # Create production config
        prod_config = {
            "app": {"log_level": "WARNING"},
            "trading": {"dry_run": False, "max_concurrent_trades": 10},
        }
        with open(env_dir / "production.yaml", "w") as f:
            yaml.dump(prod_config, f)

        yield config_dir


class TestConfigLoader:
    """Test ConfigLoader class."""

    def test_init_default_environment(self, temp_config_dir: Path) -> None:
        """Test initialization with default environment."""
        loader = ConfigLoader(config_dir=temp_config_dir)
        assert loader.environment == "development"
        assert loader.config_dir == temp_config_dir

    def test_init_custom_environment(self, temp_config_dir: Path) -> None:
        """Test initialization with custom environment."""
        loader = ConfigLoader(config_dir=temp_config_dir, env="production")
        assert loader.environment == "production"

    def test_init_invalid_environment(self, temp_config_dir: Path) -> None:
        """Test initialization with invalid environment raises error."""
        with pytest.raises(ValueError, match="Invalid environment"):
            ConfigLoader(config_dir=temp_config_dir, env="invalid")

    def test_load_base_config(self, temp_config_dir: Path) -> None:
        """Test loading base configuration."""
        loader = ConfigLoader(config_dir=temp_config_dir, env="development")
        config = loader.load()

        assert config.app.name == "Test Bot"
        assert config.app.version == "1.0.0"
        assert config.database.host == "localhost"
        assert config.database.port == 5432

    def test_load_development_config(self, temp_config_dir: Path) -> None:
        """Test loading development configuration with overrides."""
        loader = ConfigLoader(config_dir=temp_config_dir, env="development")
        config = loader.load()

        # Base values
        assert config.app.name == "Test Bot"

        # Development overrides
        assert config.app.log_level == "DEBUG"
        assert config.database.echo is True
        assert config.trading.max_concurrent_trades == 2

    def test_load_production_config(self, temp_config_dir: Path) -> None:
        """Test loading production configuration with overrides."""
        loader = ConfigLoader(config_dir=temp_config_dir, env="production")
        config = loader.load()

        # Base values
        assert config.app.name == "Test Bot"

        # Production overrides
        assert config.app.log_level == "WARNING"
        assert config.trading.dry_run is False
        assert config.trading.max_concurrent_trades == 10

    def test_environment_variable_overlay(
        self, temp_config_dir: Path, monkeypatch: Any
    ) -> None:
        """Test environment variables override YAML config."""
        # Set environment variables
        monkeypatch.setenv("DATABASE_USER", "env_user")
        monkeypatch.setenv("DATABASE_PASSWORD", "env_password")
        monkeypatch.setenv("BINANCE_API_KEY", "env_binance_key")
        monkeypatch.setenv("ENCRYPTION_KEY", "env_encryption_key")

        loader = ConfigLoader(config_dir=temp_config_dir, env="development")
        config = loader.load()

        # Environment variables should override
        assert config.database.user == "env_user"
        assert config.database.password == "env_password"
        assert config.exchanges.binance.api_key == "env_binance_key"
        assert config.security.encryption_key == "env_encryption_key"

    def test_deep_merge(self, temp_config_dir: Path) -> None:
        """Test deep merge of nested dictionaries."""
        loader = ConfigLoader(config_dir=temp_config_dir, env="development")

        base: dict[str, Any] = {
            "a": 1,
            "b": {"c": 2, "d": 3},
            "e": {"f": {"g": 4}},
        }

        override: dict[str, Any] = {
            "b": {"c": 10},
            "e": {"f": {"h": 5}},
            "i": 6,
        }

        result = loader._deep_merge(base, override)

        assert result["a"] == 1
        assert result["b"]["c"] == 10  # Overridden
        assert result["b"]["d"] == 3  # Preserved
        assert result["e"]["f"]["g"] == 4  # Preserved
        assert result["e"]["f"]["h"] == 5  # Added
        assert result["i"] == 6  # Added

    def test_missing_base_config(self, temp_config_dir: Path) -> None:
        """Test that missing base config raises error."""
        # Remove base config
        (temp_config_dir / "environments" / "base.yaml").unlink()

        loader = ConfigLoader(config_dir=temp_config_dir, env="development")

        with pytest.raises(FileNotFoundError):
            loader.load()

    def test_missing_environment_config(self, temp_config_dir: Path) -> None:
        """Test that missing environment config falls back to base."""
        # Create staging loader without staging.yaml
        loader = ConfigLoader(config_dir=temp_config_dir, env="staging")

        # Should load base config only (but will fail validation due to
        # missing encryption key unless we set it)
        os.environ["ENCRYPTION_KEY"] = "test_key"
        config = loader.load()

        # Should use base values
        assert config.app.log_level == "INFO"
        assert config.trading.max_concurrent_trades == 5

    def test_validation_error(self, temp_config_dir: Path) -> None:
        """Test that invalid config raises validation error."""
        # Create invalid config with invalid port (out of range)
        invalid_config = {
            "database": {"port": 99999},  # Invalid port
            "security": {"encryption_key": "test"},
        }

        env_dir = temp_config_dir / "environments"
        with open(env_dir / "base.yaml", "w") as f:
            yaml.dump(invalid_config, f)

        # Remove development.yaml so it doesn't override
        dev_file = env_dir / "development.yaml"
        if dev_file.exists():
            dev_file.unlink()

        loader = ConfigLoader(config_dir=temp_config_dir, env="development")

        # Should raise ValueError due to invalid port
        try:
            loader.load()
            pytest.fail("Should have raised ValueError")
        except ValueError as e:
            assert "Configuration validation failed" in str(e)


class TestLoadConfigFunction:
    """Test load_config convenience function."""

    def test_load_config(self, temp_config_dir: Path) -> None:
        """Test load_config function."""
        config = load_config(config_dir=temp_config_dir, env="development")

        assert isinstance(config, Config)
        assert config.app.name == "Test Bot"
        assert config.app.log_level == "DEBUG"

    def test_load_config_with_env_var(
        self, temp_config_dir: Path, monkeypatch: Any
    ) -> None:
        """Test load_config with environment variable."""
        monkeypatch.setenv("ENVIRONMENT", "production")

        config = load_config(config_dir=temp_config_dir)

        assert config.app.log_level == "WARNING"
        assert config.trading.dry_run is False


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_yaml_file(self, temp_config_dir: Path, monkeypatch: Any) -> None:
        """Test handling of empty YAML file."""
        # Ensure ENCRYPTION_KEY is not set
        monkeypatch.delenv("ENCRYPTION_KEY", raising=False)

        env_dir = temp_config_dir / "environments"

        # Create empty base config
        with open(env_dir / "base.yaml", "w") as f:
            f.write("")

        # Remove development.yaml as well
        dev_file = env_dir / "development.yaml"
        if dev_file.exists():
            dev_file.unlink()

        loader = ConfigLoader(config_dir=temp_config_dir, env="development")

        # Should fail validation due to missing required security field
        try:
            loader.load()
            pytest.fail("Should have raised ValueError")
        except ValueError as e:
            assert "Configuration validation failed" in str(e)

    def test_yaml_with_null_values(self, temp_config_dir: Path) -> None:
        """Test handling of null values in YAML."""
        config_with_nulls = {
            "app": {"name": None, "version": "1.0.0", "log_level": "INFO"},
            "security": {"encryption_key": "test"},
        }

        env_dir = temp_config_dir / "environments"
        with open(env_dir / "base.yaml", "w") as f:
            yaml.dump(config_with_nulls, f)

        loader = ConfigLoader(config_dir=temp_config_dir, env="development")

        # Should fail validation or use default
        with pytest.raises(ValueError):
            loader.load()

    def test_overlay_all_sensitive_vars(
        self, temp_config_dir: Path, monkeypatch: Any
    ) -> None:
        """Test overlaying all sensitive environment variables."""
        # Set all sensitive vars
        sensitive_vars = {
            "DATABASE_USER": "db_user",
            "DATABASE_PASSWORD": "db_pass",
            "REDIS_PASSWORD": "redis_pass",
            "BINANCE_API_KEY": "binance_key",
            "BINANCE_API_SECRET": "binance_secret",
            "COINBASE_API_KEY": "coinbase_key",
            "COINBASE_API_SECRET": "coinbase_secret",
            "COINBASE_PASSPHRASE": "coinbase_pass",
            "ENCRYPTION_KEY": "encryption_key",
            "JWT_SECRET": "jwt_secret",
            "TELEGRAM_BOT_TOKEN": "telegram_token",
            "TELEGRAM_CHAT_ID": "telegram_chat",
            "DISCORD_WEBHOOK_URL": "discord_webhook",
            "EMAIL_SMTP_PASSWORD": "email_pass",
        }

        for key, value in sensitive_vars.items():
            monkeypatch.setenv(key, value)

        loader = ConfigLoader(config_dir=temp_config_dir, env="development")
        config = loader.load()

        # Verify all were overlaid
        assert config.database.user == "db_user"
        assert config.database.password == "db_pass"
        assert config.redis.password == "redis_pass"
        assert config.exchanges.binance.api_key == "binance_key"
        assert config.exchanges.binance.api_secret == "binance_secret"
        assert config.exchanges.coinbase.api_key == "coinbase_key"
        assert config.exchanges.coinbase.api_secret == "coinbase_secret"
        assert config.exchanges.coinbase.passphrase == "coinbase_pass"
        assert config.security.encryption_key == "encryption_key"
        assert config.security.jwt_secret == "jwt_secret"
        assert config.notifications.telegram.token == "telegram_token"
        assert config.notifications.telegram.chat_id == "telegram_chat"
        assert config.notifications.discord.webhook_url == "discord_webhook"
        assert config.notifications.email.token == "email_pass"
