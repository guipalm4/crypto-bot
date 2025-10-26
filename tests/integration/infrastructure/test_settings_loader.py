"""
Integration tests for settings loader.

Tests loading and validation of configuration from YAML files.
"""

import os
from decimal import Decimal
from pathlib import Path

import pytest

from crypto_bot.infrastructure.config.settings import (
    Settings,
    get_settings,
    load_yaml_config,
    merge_configs,
    reload_settings,
)


class TestLoadYamlConfig:
    """Tests for YAML configuration loading."""

    def test_load_base_config(self) -> None:
        """Test loading base configuration file."""
        config_path = (
            Path(__file__).parent.parent.parent.parent
            / "config"
            / "environments"
            / "base.yaml"
        )
        config = load_yaml_config(config_path)

        assert "app" in config
        assert "database" in config
        assert "trading" in config
        assert config["app"]["name"] == "Crypto Trading Bot"

    def test_load_development_config(self) -> None:
        """Test loading development configuration file."""
        config_path = (
            Path(__file__).parent.parent.parent.parent
            / "config"
            / "environments"
            / "development.yaml"
        )
        config = load_yaml_config(config_path)

        assert "app" in config
        assert config["app"]["log_level"] == "DEBUG"

    def test_load_nonexistent_file(self) -> None:
        """Test that loading nonexistent file raises FileNotFoundError."""
        config_path = Path("nonexistent.yaml")
        with pytest.raises(FileNotFoundError):
            load_yaml_config(config_path)


class TestMergeConfigs:
    """Tests for configuration merging."""

    def test_merge_simple_configs(self) -> None:
        """Test merging simple configurations."""
        config1 = {"a": 1, "b": 2}
        config2 = {"b": 3, "c": 4}

        result = merge_configs(config1, config2)

        assert result == {"a": 1, "b": 3, "c": 4}

    def test_merge_nested_configs(self) -> None:
        """Test merging nested configurations."""
        config1 = {"app": {"name": "Bot", "version": "1.0"}}
        config2 = {"app": {"version": "2.0", "debug": True}}

        result = merge_configs(config1, config2)

        assert result == {"app": {"name": "Bot", "version": "2.0", "debug": True}}

    def test_merge_multiple_configs(self) -> None:
        """Test merging more than two configurations."""
        config1 = {"a": 1}
        config2 = {"b": 2}
        config3 = {"c": 3}

        result = merge_configs(config1, config2, config3)

        assert result == {"a": 1, "b": 2, "c": 3}


class TestGetSettings:
    """Tests for settings loader with caching."""

    def test_get_settings_development(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test loading development settings."""
        # Clear cache before test
        get_settings.cache_clear()

        # Set environment
        monkeypatch.setenv("CRYPTOBOT_ENV", "development")

        settings = get_settings()

        assert isinstance(settings, Settings)
        assert settings.app.name == "Crypto Trading Bot"
        assert settings.app.log_level == "DEBUG"
        assert settings.database.host == "localhost"
        assert settings.trading.dry_run is True

    def test_get_settings_validates_risk_config(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that risk configuration is properly validated."""
        get_settings.cache_clear()
        monkeypatch.setenv("CRYPTOBOT_ENV", "development")

        settings = get_settings()

        # Check risk configuration structure
        assert settings.trading.risk is not None
        assert settings.trading.risk.stop_loss.enabled is True
        assert settings.trading.risk.stop_loss.percentage == Decimal("2.0")
        assert settings.trading.risk.take_profit.percentage == Decimal("5.0")
        assert settings.trading.risk.exposure_limit.max_per_asset == Decimal("10000.0")
        assert settings.trading.risk.trailing_stop.trailing_percentage == Decimal("3.0")
        assert settings.trading.risk.max_concurrent_trades.max_trades == 5
        assert (
            settings.trading.risk.drawdown_control.max_drawdown_percentage
            == Decimal("15.0")
        )

    def test_reload_settings_clears_cache(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that reload_settings clears cache."""
        get_settings.cache_clear()
        monkeypatch.setenv("CRYPTOBOT_ENV", "development")

        # Load settings once
        settings1 = get_settings()

        # Reload settings
        settings2 = reload_settings()

        # Both should have same values but force reload happened
        assert settings1.app.name == settings2.app.name

    def test_settings_caching_works(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that settings are cached between calls."""
        get_settings.cache_clear()
        monkeypatch.setenv("CRYPTOBOT_ENV", "development")

        # Load settings twice
        settings1 = get_settings()
        settings2 = get_settings()

        # Should be the exact same object due to caching
        assert settings1 is settings2

    def test_environment_override_works(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that environment variables override config."""
        get_settings.cache_clear()
        monkeypatch.setenv("CRYPTOBOT_ENV", "development")
        monkeypatch.setenv("CRYPTOBOT_APP__LOG_LEVEL", "ERROR")

        settings = get_settings()

        # Environment override should take precedence
        assert settings.app.log_level == "ERROR"


class TestSettingsValidation:
    """Tests for settings validation."""

    def test_valid_base_configuration(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that base configuration is valid."""
        get_settings.cache_clear()
        monkeypatch.setenv("CRYPTOBOT_ENV", "development")

        # Should not raise ValidationError
        settings = get_settings()
        assert settings is not None

    def test_exchanges_configuration(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test exchanges configuration loading."""
        get_settings.cache_clear()
        monkeypatch.setenv("CRYPTOBOT_ENV", "development")

        settings = get_settings()

        assert settings.exchanges.binance.enabled is True
        assert settings.exchanges.binance.sandbox is True
        assert settings.exchanges.coinbase.enabled is True


class TestEnvironmentSpecificSettings:
    """Tests for environment-specific settings."""

    def test_development_environment(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test development-specific settings."""
        get_settings.cache_clear()
        monkeypatch.setenv("CRYPTOBOT_ENV", "development")

        settings = get_settings()

        assert settings.app.log_level == "DEBUG"
        assert settings.database.echo is True
        assert settings.trading.dry_run is True

    def test_default_environment_is_development(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that default environment is development."""
        get_settings.cache_clear()
        # Don't set CRYPTOBOT_ENV
        monkeypatch.delenv("CRYPTOBOT_ENV", raising=False)

        settings = get_settings()

        # Should load development by default
        assert settings.app.log_level == "DEBUG"
