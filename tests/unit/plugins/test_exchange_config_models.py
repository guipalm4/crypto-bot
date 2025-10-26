"""Unit tests for exchange configuration models."""

import pytest
from pydantic import ValidationError

from crypto_bot.plugins.exchanges.config_models import (
    BinanceConfig,
    CoinbaseProConfig,
    ExchangeConfig,
)


class TestExchangeConfig:
    """Test cases for base ExchangeConfig model."""

    def test_default_values(self) -> None:
        """Test that default values are correctly set."""
        config = ExchangeConfig()

        assert config.api_key is None
        assert config.secret is None
        assert config.password is None
        assert config.sandbox is False
        assert config.timeout == 30000
        assert config.rate_limit == 1000
        assert config.enable_rate_limit is True
        assert config.proxy is None
        assert config.verbose is False
        assert config.options == {}

    def test_custom_values(self) -> None:
        """Test that custom values can be set."""
        config = ExchangeConfig(
            api_key="encrypted_key",
            secret="encrypted_secret",
            sandbox=True,
            timeout=60000,
            rate_limit=2000,
            enable_rate_limit=False,
            proxy="https://proxy.example.com:8080",
            verbose=True,
            options={"defaultType": "future"},
        )

        assert config.api_key == "encrypted_key"
        assert config.secret == "encrypted_secret"
        assert config.sandbox is True
        assert config.timeout == 60000
        assert config.rate_limit == 2000
        assert config.enable_rate_limit is False
        assert config.proxy == "https://proxy.example.com:8080"
        assert config.verbose is True
        assert config.options == {"defaultType": "future"}

    def test_invalid_timeout(self) -> None:
        """Test that invalid timeout raises validation error."""
        with pytest.raises(ValidationError) as exc_info:
            ExchangeConfig(timeout=0)

        assert "timeout" in str(exc_info.value)

    def test_invalid_rate_limit(self) -> None:
        """Test that invalid rate_limit raises validation error."""
        with pytest.raises(ValidationError) as exc_info:
            ExchangeConfig(rate_limit=-1)

        assert "rate_limit" in str(exc_info.value)

    def test_invalid_proxy_format(self) -> None:
        """Test that invalid proxy format raises validation error."""
        with pytest.raises(ValidationError) as exc_info:
            ExchangeConfig(proxy="invalid-proxy-url")

        assert "proxy" in str(exc_info.value).lower()

    def test_valid_http_proxy(self) -> None:
        """Test that valid HTTP proxy is accepted."""
        config = ExchangeConfig(proxy="http://proxy.example.com:8080")
        assert config.proxy == "http://proxy.example.com:8080"

    def test_valid_https_proxy(self) -> None:
        """Test that valid HTTPS proxy is accepted."""
        config = ExchangeConfig(proxy="https://proxy.example.com:8080")
        assert config.proxy == "https://proxy.example.com:8080"

    def test_reject_unknown_fields(self) -> None:
        """Test that unknown fields are rejected."""
        with pytest.raises(ValidationError):
            ExchangeConfig(unknown_field="value")  # type: ignore


class TestBinanceConfig:
    """Test cases for BinanceConfig model."""

    def test_inherits_from_exchange_config(self) -> None:
        """Test that BinanceConfig inherits from ExchangeConfig."""
        config = BinanceConfig()
        assert isinstance(config, ExchangeConfig)

    def test_default_values(self) -> None:
        """Test that default values are correctly inherited."""
        config = BinanceConfig()
        assert config.sandbox is False
        assert config.enable_rate_limit is True

    def test_custom_values(self) -> None:
        """Test that custom values can be set."""
        config = BinanceConfig(
            api_key="binance_key",
            secret="binance_secret",
            sandbox=True,
        )
        assert config.api_key == "binance_key"
        assert config.secret == "binance_secret"
        assert config.sandbox is True


class TestCoinbaseProConfig:
    """Test cases for CoinbaseProConfig model."""

    def test_inherits_from_exchange_config(self) -> None:
        """Test that CoinbaseProConfig inherits from ExchangeConfig."""
        config = CoinbaseProConfig()
        assert isinstance(config, ExchangeConfig)

    def test_passphrase_not_required_for_public_operations(self) -> None:
        """Test that passphrase is not required when no API key is provided."""
        config = CoinbaseProConfig()
        assert config.password is None
        assert config.api_key is None

    def test_passphrase_required_with_api_key(self) -> None:
        """Test that passphrase is required when API key is provided."""
        with pytest.raises(ValidationError) as exc_info:
            CoinbaseProConfig(
                api_key="coinbase_key",
                secret="coinbase_secret",
                # password/passphrase missing
            )

        error_str = str(exc_info.value).lower()
        assert "password" in error_str or "passphrase" in error_str

    def test_valid_coinbase_config_with_passphrase(self) -> None:
        """Test that valid Coinbase Pro config with passphrase is accepted."""
        config = CoinbaseProConfig(
            api_key="coinbase_key",
            secret="coinbase_secret",
            password="coinbase_passphrase",
            sandbox=True,
        )

        assert config.api_key == "coinbase_key"
        assert config.secret == "coinbase_secret"
        assert config.password == "coinbase_passphrase"
        assert config.sandbox is True

    def test_public_only_config(self) -> None:
        """Test that config without credentials is valid for public operations."""
        config = CoinbaseProConfig(sandbox=True)
        assert config.api_key is None
        assert config.secret is None
        assert config.password is None
        assert config.sandbox is True
