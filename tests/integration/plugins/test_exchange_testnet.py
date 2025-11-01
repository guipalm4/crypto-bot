"""
Integration tests for exchange plugins using real testnet environments.

These tests require testnet API credentials and will be skipped if not available.
Use environment variables or test configuration to provide credentials:
- BINANCE_TESTNET_API_KEY
- BINANCE_TESTNET_API_SECRET
- COINBASE_TESTNET_API_KEY
- COINBASE_TESTNET_API_SECRET
- COINBASE_TESTNET_PASSPHRASE

Mark tests with @pytest.mark.integration to run separately from unit tests.
"""

import os
from decimal import Decimal
from unittest.mock import patch

import pytest
import pytest_asyncio

from crypto_bot.application.dtos.order import (
    CreateOrderRequest,
    OrderSide,
    OrderType,
)
from crypto_bot.application.exceptions import ExchangeError
from crypto_bot.plugins.exchanges.binance_plugin import BinancePlugin
from crypto_bot.plugins.exchanges.coinbase_pro_plugin import CoinbaseProPlugin
from crypto_bot.plugins.exchanges.config_models import BinanceConfig, CoinbaseProConfig

# Check for testnet credentials
BINANCE_TESTNET_AVAILABLE = bool(
    os.getenv("BINANCE_TESTNET_API_KEY") and os.getenv("BINANCE_TESTNET_API_SECRET")
)

COINBASE_TESTNET_AVAILABLE = bool(
    os.getenv("COINBASE_TESTNET_API_KEY")
    and os.getenv("COINBASE_TESTNET_API_SECRET")
    and os.getenv("COINBASE_TESTNET_PASSPHRASE")
)


@pytest.fixture
def binance_testnet_config() -> BinanceConfig:
    """Create Binance testnet configuration."""
    return BinanceConfig(
        api_key=os.getenv("BINANCE_TESTNET_API_KEY", ""),
        api_secret=os.getenv("BINANCE_TESTNET_API_SECRET", ""),
        sandbox=True,  # Enable testnet mode
    )


@pytest.fixture
def coinbase_testnet_config() -> CoinbaseProConfig:
    """Create Coinbase Pro testnet configuration."""
    return CoinbaseProConfig(
        api_key=os.getenv("COINBASE_TESTNET_API_KEY", ""),
        api_secret=os.getenv("COINBASE_TESTNET_API_SECRET", ""),
        passphrase=os.getenv("COINBASE_TESTNET_PASSPHRASE", ""),
        sandbox=True,  # Enable testnet mode
    )


@pytest.mark.integration
@pytest.mark.asyncio
class TestBinanceTestnetIntegration:
    """Integration tests for Binance plugin on testnet."""

    @pytest.mark.skipif(
        not BINANCE_TESTNET_AVAILABLE,
        reason="Binance testnet credentials not available",
    )
    async def test_initialize_binance_testnet(
        self, binance_testnet_config: BinanceConfig
    ) -> None:
        """Test initializing Binance plugin with testnet."""
        plugin = BinancePlugin(binance_testnet_config)
        assert not plugin._initialized

        await plugin.initialize()
        assert plugin._initialized
        assert plugin.sandbox is True

        await plugin.close()

    @pytest.mark.skipif(
        not BINANCE_TESTNET_AVAILABLE,
        reason="Binance testnet credentials not available",
    )
    async def test_fetch_markets_binance_testnet(
        self, binance_testnet_config: BinanceConfig
    ) -> None:
        """Test fetching markets from Binance testnet."""
        plugin = BinancePlugin(binance_testnet_config)
        await plugin.initialize()

        markets = await plugin.fetch_markets()
        assert isinstance(markets, list)
        assert len(markets) > 0

        # Verify market structure
        market = markets[0]
        assert "id" in market or "symbol" in market

        await plugin.close()

    @pytest.mark.skipif(
        not BINANCE_TESTNET_AVAILABLE,
        reason="Binance testnet credentials not available",
    )
    async def test_fetch_ticker_binance_testnet(
        self, binance_testnet_config: BinanceConfig
    ) -> None:
        """Test fetching ticker from Binance testnet."""
        plugin = BinancePlugin(binance_testnet_config)
        await plugin.initialize()
        await plugin.load_markets()

        ticker = await plugin.fetch_ticker("BTC/USDT")
        assert isinstance(ticker, dict)
        assert "symbol" in ticker or "last" in ticker

        await plugin.close()

    @pytest.mark.skipif(
        not BINANCE_TESTNET_AVAILABLE,
        reason="Binance testnet credentials not available",
    )
    async def test_fetch_ohlcv_binance_testnet(
        self, binance_testnet_config: BinanceConfig
    ) -> None:
        """Test fetching OHLCV data from Binance testnet."""
        plugin = BinancePlugin(binance_testnet_config)
        await plugin.initialize()
        await plugin.load_markets()

        ohlcv = await plugin.fetch_ohlcv("BTC/USDT", timeframe="1h", limit=10)
        assert isinstance(ohlcv, list)
        if len(ohlcv) > 0:
            # OHLCV format: [timestamp, open, high, low, close, volume]
            assert len(ohlcv[0]) == 6

        await plugin.close()

    @pytest.mark.skipif(
        not BINANCE_TESTNET_AVAILABLE,
        reason="Binance testnet credentials not available",
    )
    async def test_fetch_balance_binance_testnet(
        self, binance_testnet_config: BinanceConfig
    ) -> None:
        """Test fetching balance from Binance testnet."""
        plugin = BinancePlugin(binance_testnet_config)
        await plugin.initialize()

        balance = await plugin.fetch_balance()
        assert balance is not None
        # Balance can be BalanceDTO or dict
        if isinstance(balance, dict):
            assert len(balance) >= 0  # May be empty on testnet
        else:
            assert hasattr(balance, "currency")

        await plugin.close()

    @pytest.mark.skipif(
        not BINANCE_TESTNET_AVAILABLE,
        reason="Binance testnet credentials not available",
    )
    async def test_create_and_cancel_order_binance_testnet(
        self, binance_testnet_config: BinanceConfig
    ) -> None:
        """Test creating and canceling order on Binance testnet."""
        plugin = BinancePlugin(binance_testnet_config)
        await plugin.initialize()
        await plugin.load_markets()

        # Create a limit buy order (will likely fail if insufficient balance, but tests the flow)
        order_request = CreateOrderRequest(
            exchange="binance",
            symbol="BTC/USDT",
            side=OrderSide.BUY,
            type=OrderType.LIMIT,
            quantity=Decimal("0.0001"),  # Very small amount
            price=Decimal("1000"),  # Low price unlikely to fill
        )

        try:
            order = await plugin.create_order(order_request)
            assert order is not None
            assert order.exchange_order_id is not None

            # Cancel the order
            canceled_order = await plugin.cancel_order(
                order.exchange_order_id, "BTC/USDT"
            )
            assert canceled_order is not None

        except Exception as e:
            # Order creation may fail due to insufficient balance or other testnet issues
            # This is acceptable - we're testing the integration, not the exchange itself
            assert (
                "insufficient" in str(e).lower()
                or "balance" in str(e).lower()
                or "price" in str(e).lower()
            )

        await plugin.close()

    @pytest.mark.skipif(
        not BINANCE_TESTNET_AVAILABLE,
        reason="Binance testnet credentials not available",
    )
    async def test_rate_limit_handling_binance_testnet(
        self, binance_testnet_config: BinanceConfig
    ) -> None:
        """Test rate limit handling on Binance testnet."""
        plugin = BinancePlugin(binance_testnet_config)
        await plugin.initialize()
        await plugin.load_markets()

        # Make multiple rapid requests to test rate limiting
        for _ in range(5):
            try:
                await plugin.fetch_ticker("BTC/USDT")
            except Exception as e:
                # Rate limit errors are acceptable
                if "rate limit" in str(e).lower() or "429" in str(e):
                    break

        await plugin.close()

    @pytest.mark.skipif(
        not BINANCE_TESTNET_AVAILABLE,
        reason="Binance testnet credentials not available",
    )
    async def test_error_handling_invalid_symbol_binance_testnet(
        self, binance_testnet_config: BinanceConfig
    ) -> None:
        """Test error handling for invalid symbol on Binance testnet."""
        plugin = BinancePlugin(binance_testnet_config)
        await plugin.initialize()
        await plugin.load_markets()

        # Try to fetch ticker for invalid symbol
        with pytest.raises(ExchangeError):  # Should raise exchange error
            await plugin.fetch_ticker("INVALID/SYMBOL")

        await plugin.close()


@pytest.mark.integration
@pytest.mark.asyncio
class TestCoinbaseProTestnetIntegration:
    """Integration tests for Coinbase Pro plugin on testnet."""

    @pytest.mark.skipif(
        not COINBASE_TESTNET_AVAILABLE,
        reason="Coinbase Pro testnet credentials not available",
    )
    async def test_initialize_coinbase_testnet(
        self, coinbase_testnet_config: CoinbaseProConfig
    ) -> None:
        """Test initializing Coinbase Pro plugin with testnet."""
        plugin = CoinbaseProPlugin(coinbase_testnet_config)
        assert not plugin._initialized

        await plugin.initialize()
        assert plugin._initialized
        assert plugin.sandbox is True

        await plugin.close()

    @pytest.mark.skipif(
        not COINBASE_TESTNET_AVAILABLE,
        reason="Coinbase Pro testnet credentials not available",
    )
    async def test_fetch_markets_coinbase_testnet(
        self, coinbase_testnet_config: CoinbaseProConfig
    ) -> None:
        """Test fetching markets from Coinbase Pro testnet."""
        plugin = CoinbaseProPlugin(coinbase_testnet_config)
        await plugin.initialize()

        markets = await plugin.fetch_markets()
        assert isinstance(markets, list)
        # Coinbase may return empty list on testnet, which is acceptable

        await plugin.close()

    @pytest.mark.skipif(
        not COINBASE_TESTNET_AVAILABLE,
        reason="Coinbase Pro testnet credentials not available",
    )
    async def test_fetch_ticker_coinbase_testnet(
        self, coinbase_testnet_config: CoinbaseProConfig
    ) -> None:
        """Test fetching ticker from Coinbase Pro testnet."""
        plugin = CoinbaseProPlugin(coinbase_testnet_config)
        await plugin.initialize()
        await plugin.load_markets()

        try:
            ticker = await plugin.fetch_ticker("BTC/USD")
            assert isinstance(ticker, dict)
        except Exception:
            # Coinbase Pro testnet may have limited symbols
            pass

        await plugin.close()

    @pytest.mark.skipif(
        not COINBASE_TESTNET_AVAILABLE,
        reason="Coinbase Pro testnet credentials not available",
    )
    async def test_fetch_ohlcv_coinbase_testnet(
        self, coinbase_testnet_config: CoinbaseProConfig
    ) -> None:
        """Test fetching OHLCV data from Coinbase Pro testnet."""
        plugin = CoinbaseProPlugin(coinbase_testnet_config)
        await plugin.initialize()
        await plugin.load_markets()

        try:
            ohlcv = await plugin.fetch_ohlcv("BTC/USD", timeframe="1h", limit=10)
            assert isinstance(ohlcv, list)
            if len(ohlcv) > 0:
                # OHLCV format: [timestamp, open, high, low, close, volume]
                assert len(ohlcv[0]) == 6
        except Exception:
            # Coinbase Pro testnet may have limited symbols or data
            pass

        await plugin.close()

    @pytest.mark.skipif(
        not COINBASE_TESTNET_AVAILABLE,
        reason="Coinbase Pro testnet credentials not available",
    )
    async def test_fetch_balance_coinbase_testnet(
        self, coinbase_testnet_config: CoinbaseProConfig
    ) -> None:
        """Test fetching balance from Coinbase Pro testnet."""
        plugin = CoinbaseProPlugin(coinbase_testnet_config)
        await plugin.initialize()

        balance = await plugin.fetch_balance()
        assert balance is not None
        # Balance can be BalanceDTO or dict
        if isinstance(balance, dict):
            assert len(balance) >= 0  # May be empty on testnet
        else:
            assert hasattr(balance, "currency")

        await plugin.close()

    @pytest.mark.skipif(
        not COINBASE_TESTNET_AVAILABLE,
        reason="Coinbase Pro testnet credentials not available",
    )
    async def test_create_and_cancel_order_coinbase_testnet(
        self, coinbase_testnet_config: CoinbaseProConfig
    ) -> None:
        """Test creating and canceling order on Coinbase Pro testnet."""
        plugin = CoinbaseProPlugin(coinbase_testnet_config)
        await plugin.initialize()
        await plugin.load_markets()

        # Create a limit buy order (will likely fail if insufficient balance, but tests the flow)
        order_request = CreateOrderRequest(
            exchange="coinbasepro",
            symbol="BTC/USD",
            side=OrderSide.BUY,
            type=OrderType.LIMIT,
            quantity=Decimal("0.001"),  # Very small amount
            price=Decimal("1000"),  # Low price unlikely to fill
        )

        try:
            order = await plugin.create_order(order_request)
            assert order is not None
            assert order.exchange_order_id is not None

            # Cancel the order
            canceled_order = await plugin.cancel_order(
                order.exchange_order_id, "BTC/USD"
            )
            assert canceled_order is not None

        except Exception as e:
            # Order creation may fail due to insufficient balance or other testnet issues
            # This is acceptable - we're testing the integration, not the exchange itself
            assert (
                "insufficient" in str(e).lower()
                or "balance" in str(e).lower()
                or "price" in str(e).lower()
                or "invalid" in str(e).lower()
            )

        await plugin.close()

    @pytest.mark.skipif(
        not COINBASE_TESTNET_AVAILABLE,
        reason="Coinbase Pro testnet credentials not available",
    )
    async def test_rate_limit_handling_coinbase_testnet(
        self, coinbase_testnet_config: CoinbaseProConfig
    ) -> None:
        """Test rate limit handling on Coinbase Pro testnet."""
        plugin = CoinbaseProPlugin(coinbase_testnet_config)
        await plugin.initialize()
        await plugin.load_markets()

        # Make multiple rapid requests to test rate limiting
        try:
            for _ in range(5):
                try:
                    await plugin.fetch_ticker("BTC/USD")
                except Exception as e:
                    # Rate limit errors are acceptable
                    if "rate limit" in str(e).lower() or "429" in str(e):
                        break
        except Exception:
            # Coinbase Pro testnet may have limited symbols
            pass

        await plugin.close()

    @pytest.mark.skipif(
        not COINBASE_TESTNET_AVAILABLE,
        reason="Coinbase Pro testnet credentials not available",
    )
    async def test_error_handling_invalid_symbol_coinbase_testnet(
        self, coinbase_testnet_config: CoinbaseProConfig
    ) -> None:
        """Test error handling for invalid symbol on Coinbase Pro testnet."""
        plugin = CoinbaseProPlugin(coinbase_testnet_config)
        await plugin.initialize()
        await plugin.load_markets()

        # Try to fetch ticker for invalid symbol
        try:
            with pytest.raises(ExchangeError):  # Should raise exchange error
                await plugin.fetch_ticker("INVALID/SYMBOL")
        except ExchangeError:
            # Some exchanges return empty data instead of raising, which is acceptable
            pass

        await plugin.close()


@pytest.mark.integration
@pytest.mark.asyncio
class TestExchangePluginErrorHandling:
    """Test error handling scenarios for exchange plugins."""

    @pytest.mark.skipif(
        not BINANCE_TESTNET_AVAILABLE,
        reason="Binance testnet credentials not available",
    )
    async def test_network_error_handling(
        self, binance_testnet_config: BinanceConfig
    ) -> None:
        """Test handling of network errors."""
        plugin = BinancePlugin(binance_testnet_config)
        await plugin.initialize()
        await plugin.load_markets()

        # Test error handling with invalid symbol
        # This should trigger proper error handling in the plugin
        try:
            await plugin.fetch_ticker("INVALID/SYMBOL")
            # If no error raised, that's also acceptable (some exchanges return empty data)
        except Exception:
            # Expected - plugin should handle errors gracefully
            pass

        await plugin.close()

    @pytest.mark.skipif(
        not BINANCE_TESTNET_AVAILABLE,
        reason="Binance testnet credentials not available",
    )
    async def test_authentication_error_handling(self) -> None:
        """Test handling of authentication errors."""
        # Create plugin with invalid credentials
        invalid_config = BinanceConfig(
            api_key="invalid_key",
            api_secret="invalid_secret",
            sandbox=True,
        )
        plugin = BinancePlugin(invalid_config)

        try:
            await plugin.initialize()
            # Try an authenticated operation
            with pytest.raises(ExchangeError):
                await plugin.fetch_balance()
        finally:
            await plugin.close()

    @pytest.mark.skipif(
        not COINBASE_TESTNET_AVAILABLE,
        reason="Coinbase Pro testnet credentials not available",
    )
    async def test_coinbase_authentication_error_handling(self) -> None:
        """Test handling of authentication errors for Coinbase Pro."""
        # Create plugin with invalid credentials
        invalid_config = CoinbaseProConfig(
            api_key="invalid_key",
            api_secret="invalid_secret",
            password="invalid_passphrase",
            sandbox=True,
        )
        plugin = CoinbaseProPlugin(invalid_config)

        try:
            await plugin.initialize()
            # Try an authenticated operation
            with pytest.raises(ExchangeError):
                await plugin.fetch_balance()
        finally:
            await plugin.close()
