"""
Basic integration tests for exchange plugins.

These tests validate that the exchange plugins can be instantiated
and configured correctly. They don't require actual API credentials
or network access.
"""

import pytest

from crypto_bot.plugins.exchanges.binance_plugin import BinancePlugin
from crypto_bot.plugins.exchanges.coinbase_pro_plugin import CoinbaseProPlugin
from crypto_bot.plugins.exchanges.config_models import BinanceConfig, CoinbaseProConfig


class TestBinancePluginBasic:
    """Basic tests for Binance plugin."""

    def test_instantiate_with_default_config(self) -> None:
        """Test that Binance plugin can be instantiated with default config."""
        config = BinanceConfig()
        plugin = BinancePlugin(config)

        assert plugin.name == "Binance"
        assert plugin.id == "binance"
        assert plugin.certified is True
        assert not plugin._initialized

    def test_sandbox_flag_in_config(self) -> None:
        """Test that sandbox flag is properly configured."""
        config = BinanceConfig(sandbox=True)
        plugin = BinancePlugin(config)

        assert plugin.sandbox is True

    def test_properties_before_initialization(self) -> None:
        """Test that properties can be accessed before initialization."""
        config = BinanceConfig()
        plugin = BinancePlugin(config)

        assert isinstance(plugin.name, str)
        assert isinstance(plugin.id, str)
        assert isinstance(plugin.countries, list)
        assert isinstance(plugin.urls, dict)
        assert isinstance(plugin.version, str)
        assert isinstance(plugin.certified, bool)
        assert isinstance(plugin.has, dict)

    def test_has_required_capabilities(self) -> None:
        """Test that plugin has required capabilities."""
        config = BinanceConfig()
        plugin = BinancePlugin(config)

        required_capabilities = [
            "createOrder",
            "cancelOrder",
            "fetchBalance",
            "fetchTicker",
            "fetchOrderBook",
            "fetchOHLCV",
        ]

        for capability in required_capabilities:
            assert capability in plugin.has
            assert plugin.has[capability] is True


class TestCoinbaseProPluginBasic:
    """Basic tests for Coinbase Pro plugin."""

    def test_instantiate_with_default_config(self) -> None:
        """Test that Coinbase Pro plugin can be instantiated with default config."""
        config = CoinbaseProConfig()
        plugin = CoinbaseProPlugin(config)

        assert plugin.name == "Coinbase Pro"
        assert plugin.id == "coinbasepro"
        assert plugin.certified is True
        assert not plugin._initialized

    def test_sandbox_flag_in_config(self) -> None:
        """Test that sandbox flag is properly configured."""
        config = CoinbaseProConfig(sandbox=True)
        plugin = CoinbaseProPlugin(config)

        assert plugin.sandbox is True

    def test_properties_before_initialization(self) -> None:
        """Test that properties can be accessed before initialization."""
        config = CoinbaseProConfig()
        plugin = CoinbaseProPlugin(config)

        assert isinstance(plugin.name, str)
        assert isinstance(plugin.id, str)
        assert isinstance(plugin.countries, list)
        assert isinstance(plugin.urls, dict)
        assert isinstance(plugin.version, str)
        assert isinstance(plugin.certified, bool)
        assert isinstance(plugin.has, dict)

    def test_has_required_capabilities(self) -> None:
        """Test that plugin has required capabilities."""
        config = CoinbaseProConfig()
        plugin = CoinbaseProPlugin(config)

        required_capabilities = [
            "createOrder",
            "cancelOrder",
            "fetchBalance",
            "fetchTicker",
            "fetchOrderBook",
        ]

        for capability in required_capabilities:
            assert capability in plugin.has
            assert plugin.has[capability] is True

    def test_positions_not_supported(self) -> None:
        """Test that Coinbase Pro correctly indicates no futures support."""
        config = CoinbaseProConfig()
        plugin = CoinbaseProPlugin(config)

        assert plugin.has.get("fetchPositions") is False


@pytest.mark.asyncio
class TestPluginLifecycle:
    """Test plugin lifecycle management."""

    async def test_binance_plugin_close(self) -> None:
        """Test that Binance plugin can be closed without initialization."""
        config = BinanceConfig()
        plugin = BinancePlugin(config)

        # Should not raise even if not initialized
        await plugin.close()
        assert not plugin._initialized

    async def test_coinbase_plugin_close(self) -> None:
        """Test that Coinbase Pro plugin can be closed without initialization."""
        config = CoinbaseProConfig()
        plugin = CoinbaseProPlugin(config)

        # Should not raise even if not initialized
        await plugin.close()
        assert not plugin._initialized
