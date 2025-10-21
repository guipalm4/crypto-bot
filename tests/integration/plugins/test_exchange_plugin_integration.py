"""
Integration tests for exchange plugin system.
"""

import pytest
import tempfile
import asyncio
from pathlib import Path
from unittest.mock import Mock, patch
from decimal import Decimal
from datetime import datetime

from crypto_bot.plugins.registry import ExchangePluginRegistry, PluginNotFound, PluginValidationError
from crypto_bot.infrastructure.exchanges.base import ExchangeBase
from crypto_bot.application.dtos.order import CreateOrderRequest, OrderSide, OrderType


class TestExchangePlugin(ExchangeBase):
    """Test exchange plugin for integration testing."""
    
    name = "Test Exchange"
    id = "test_exchange"
    countries = ["US", "GB"]
    urls = {
        "api": "https://api.testexchange.com",
        "www": "https://www.testexchange.com"
    }
    version = "2.0.0"
    certified = True
    has = {
        "createOrder": True,
        "cancelOrder": True,
        "fetchBalance": True,
        "fetchTicker": True,
        "fetchOrderBook": True,
        "fetchOHLCV": True,
        "fetchTrades": True,
        "fetchMarkets": True,
        "fetchPositions": False,
        "fetchMyTrades": True,
    }
    
    def __init__(self, api_key: str = None, secret: str = None, sandbox: bool = False, **kwargs):
        super().__init__(api_key, secret, sandbox, **kwargs)
        self._test_data = {
            "markets": {
                "BTC/USDT": {
                    "id": "BTCUSDT",
                    "symbol": "BTC/USDT",
                    "base": "BTC",
                    "quote": "USDT",
                    "active": True
                }
            },
            "ticker": {
                "symbol": "BTC/USDT",
                "last": 50000.0,
                "bid": 49999.0,
                "ask": 50001.0,
                "high": 51000.0,
                "low": 49000.0,
                "volume": 1000.0
            },
            "balance": {
                "USDT": {"free": 10000.0, "used": 0.0, "total": 10000.0},
                "BTC": {"free": 0.5, "used": 0.0, "total": 0.5}
            }
        }
    
    async def initialize(self) -> None:
        """Initialize the exchange."""
        self._initialized = True
    
    async def load_markets(self, reload: bool = False) -> dict:
        """Load exchange markets."""
        return self._test_data["markets"]
    
    async def fetch_markets(self) -> list:
        """Fetch all available markets."""
        return list(self._test_data["markets"].values())
    
    async def fetch_ticker(self, symbol: str) -> dict:
        """Fetch ticker data."""
        ticker = self._test_data["ticker"].copy()
        ticker["symbol"] = symbol
        ticker["timestamp"] = datetime.now()
        return ticker
    
    async def fetch_tickers(self, symbols=None) -> dict:
        """Fetch ticker data for multiple symbols."""
        if symbols is None:
            symbols = ["BTC/USDT"]
        
        result = {}
        for symbol in symbols:
            result[symbol] = await self.fetch_ticker(symbol)
        return result
    
    async def fetch_order_book(self, symbol: str, limit=None) -> dict:
        """Fetch order book."""
        return {
            "symbol": symbol,
            "bids": [[49999.0, 1.0], [49998.0, 2.0]],
            "asks": [[50001.0, 1.0], [50002.0, 2.0]],
            "timestamp": datetime.now()
        }
    
    async def fetch_ohlcv(self, symbol: str, timeframe='1m', since=None, limit=None):
        """Fetch OHLCV data."""
        now = datetime.now()
        timestamp = int(now.timestamp() * 1000)
        return [
            [timestamp, 50000.0, 51000.0, 49000.0, 50000.0, 1000.0]
        ]
    
    async def fetch_trades(self, symbol: str, since=None, limit=None):
        """Fetch recent trades."""
        return [
            {
                "id": "12345",
                "symbol": symbol,
                "side": "buy",
                "amount": 1.0,
                "price": 50000.0,
                "timestamp": datetime.now()
            }
        ]
    
    async def create_order(self, request: CreateOrderRequest):
        """Create a new order."""
        from crypto_bot.application.dtos.order import OrderDTO, OrderStatus
        
        return OrderDTO(
            id=f"test_{int(datetime.now().timestamp() * 1000)}",
            exchange_order_id=f"ex_{int(datetime.now().timestamp() * 1000)}",
            exchange=self.name,
            symbol=request.symbol,
            side=request.side,
            type=request.type,
            status=OrderStatus.OPEN,
            quantity=request.quantity,
            filled_quantity=Decimal("0"),
            remaining_quantity=request.quantity,
            price=request.price,
            average_price=None,
            cost=Decimal("0"),
            fee=Decimal("0"),
            fee_currency="USDT",
            timestamp=datetime.now(),
            last_trade_timestamp=None
        )
    
    async def cancel_order(self, order_id: str, symbol=None):
        """Cancel an order."""
        from crypto_bot.application.dtos.order import OrderDTO, OrderStatus
        
        return OrderDTO(
            id=order_id,
            exchange_order_id=order_id,
            exchange=self.name,
            symbol=symbol or "BTC/USDT",
            side=OrderSide.BUY,
            type=OrderType.LIMIT,
            status=OrderStatus.CANCELED,
            quantity=Decimal("1"),
            filled_quantity=Decimal("0"),
            remaining_quantity=Decimal("1"),
            price=Decimal("50000"),
            average_price=None,
            cost=Decimal("0"),
            fee=Decimal("0"),
            fee_currency="USDT",
            timestamp=datetime.now(),
            last_trade_timestamp=None
        )
    
    async def fetch_order(self, order_id: str, symbol=None):
        """Fetch order details."""
        from crypto_bot.application.dtos.order import OrderDTO, OrderStatus
        
        return OrderDTO(
            id=order_id,
            exchange_order_id=order_id,
            exchange=self.name,
            symbol=symbol or "BTC/USDT",
            side=OrderSide.BUY,
            type=OrderType.LIMIT,
            status=OrderStatus.OPEN,
            quantity=Decimal("1"),
            filled_quantity=Decimal("0"),
            remaining_quantity=Decimal("1"),
            price=Decimal("50000"),
            average_price=None,
            cost=Decimal("0"),
            fee=Decimal("0"),
            fee_currency="USDT",
            timestamp=datetime.now(),
            last_trade_timestamp=None
        )
    
    async def fetch_order_status(self, order_id: str, symbol=None):
        """Fetch order status."""
        from crypto_bot.application.dtos.order import OrderStatusDTO, OrderStatus
        
        return OrderStatusDTO(
            order_id=order_id,
            status=OrderStatus.OPEN,
            filled_quantity=Decimal("0"),
            remaining_quantity=Decimal("1"),
            average_price=None,
            last_update=datetime.now()
        )
    
    async def fetch_open_orders(self, symbol=None):
        """Fetch open orders."""
        return []
    
    async def cancel_all_orders(self, symbol=None):
        """Cancel all orders."""
        return []
    
    async def fetch_balance(self, currency=None):
        """Fetch account balance."""
        from crypto_bot.application.dtos.order import BalanceDTO
        
        balances = {}
        for curr, data in self._test_data["balance"].items():
            balances[curr] = BalanceDTO(
                exchange=self.name,
                currency=curr,
                free=Decimal(str(data["free"])),
                used=Decimal(str(data["used"])),
                total=Decimal(str(data["total"])),
                timestamp=datetime.now()
            )
        
        if currency:
            return balances.get(currency, BalanceDTO(
                exchange=self.name,
                currency=currency,
                free=Decimal("0"),
                used=Decimal("0"),
                total=Decimal("0"),
                timestamp=datetime.now()
            ))
        else:
            return balances
    
    async def fetch_positions(self, symbols=None):
        """Fetch trading positions."""
        return []
    
    async def fetch_my_trades(self, symbol=None, since=None, limit=None):
        """Fetch user's trade history."""
        return []
    
    def amount_to_precision(self, symbol: str, amount):
        """Convert amount to precision."""
        return str(amount)
    
    def price_to_precision(self, symbol: str, price):
        """Convert price to precision."""
        return str(price)
    
    def cost_to_precision(self, symbol: str, cost):
        """Convert cost to precision."""
        return str(cost)
    
    def currency_to_precision(self, currency: str, amount):
        """Convert currency amount to precision."""
        return str(amount)
    
    async def close(self) -> None:
        """Close the exchange connection."""
        self._initialized = False


class TestExchangePluginIntegration:
    """Integration tests for exchange plugin system."""
    
    @pytest.fixture
    def temp_plugin_dir(self):
        """Create a temporary directory with test plugins."""
        with tempfile.TemporaryDirectory() as temp_dir:
            plugin_dir = Path(temp_dir) / "exchanges"
            plugin_dir.mkdir()
            
            # Create a test plugin file
            plugin_file = plugin_dir / "test_exchange.py"
            plugin_content = '''
from crypto_bot.infrastructure.exchanges.base import ExchangeBase
from crypto_bot.application.dtos.order import CreateOrderRequest, OrderDTO, OrderStatusDTO, BalanceDTO, OrderSide, OrderType
from decimal import Decimal
from datetime import datetime
from typing import Dict, List, Optional, Any, Union

class TestExchangePlugin(ExchangeBase):
    name = "Test Exchange"
    id = "test_exchange"
    countries = ["US", "GB"]
    urls = {"api": "https://api.testexchange.com"}
    version = "2.0.0"
    certified = True
    has = {"createOrder": True, "fetchBalance": True, "fetchTicker": True}
    
    async def initialize(self): self._initialized = True
    async def load_markets(self, reload=False): return {"BTC/USDT": {"id": "BTCUSDT"}}
    async def fetch_markets(self): return [{"id": "BTCUSDT", "symbol": "BTC/USDT"}]
    async def fetch_ticker(self, symbol): return {"symbol": symbol, "last": 50000.0}
    async def fetch_tickers(self, symbols=None): return {"BTC/USDT": await self.fetch_ticker("BTC/USDT")}
    async def fetch_order_book(self, symbol, limit=None): return {"symbol": symbol, "bids": [], "asks": []}
    async def fetch_ohlcv(self, symbol, timeframe='1m', since=None, limit=None): return []
    async def fetch_trades(self, symbol, since=None, limit=None): return []
    async def create_order(self, request): return OrderDTO(id="test", exchange_order_id="ex_test", exchange="Test", symbol=request.symbol, side=request.side, type=request.type, status=OrderSide.BUY, quantity=request.quantity, filled_quantity=Decimal("0"), remaining_quantity=request.quantity, price=request.price, average_price=None, cost=Decimal("0"), fee=Decimal("0"), fee_currency="USDT", timestamp=datetime.now(), last_trade_timestamp=None)
    async def cancel_order(self, order_id, symbol=None): return OrderDTO(id=order_id, exchange_order_id=order_id, exchange="Test", symbol="BTC/USDT", side=OrderSide.BUY, type=OrderType.LIMIT, status=OrderSide.BUY, quantity=Decimal("1"), filled_quantity=Decimal("0"), remaining_quantity=Decimal("1"), price=Decimal("50000"), average_price=None, cost=Decimal("0"), fee=Decimal("0"), fee_currency="USDT", timestamp=datetime.now(), last_trade_timestamp=None)
    async def fetch_order(self, order_id, symbol=None): return OrderDTO(id=order_id, exchange_order_id=order_id, exchange="Test", symbol="BTC/USDT", side=OrderSide.BUY, type=OrderType.LIMIT, status=OrderSide.BUY, quantity=Decimal("1"), filled_quantity=Decimal("0"), remaining_quantity=Decimal("1"), price=Decimal("50000"), average_price=None, cost=Decimal("0"), fee=Decimal("0"), fee_currency="USDT", timestamp=datetime.now(), last_trade_timestamp=None)
    async def fetch_order_status(self, order_id, symbol=None): return OrderStatusDTO(order_id=order_id, status=OrderSide.BUY, filled_quantity=Decimal("0"), remaining_quantity=Decimal("1"), average_price=None, last_update=datetime.now())
    async def fetch_open_orders(self, symbol=None): return []
    async def cancel_all_orders(self, symbol=None): return []
    async def fetch_balance(self, currency=None): return BalanceDTO(exchange="Test", currency="USDT", free=Decimal("10000"), used=Decimal("0"), total=Decimal("10000"), timestamp=datetime.now())
    async def fetch_positions(self, symbols=None): return []
    async def fetch_my_trades(self, symbol=None, since=None, limit=None): return []
    def amount_to_precision(self, symbol, amount): return str(amount)
    def price_to_precision(self, symbol, price): return str(price)
    def cost_to_precision(self, symbol, cost): return str(cost)
    def currency_to_precision(self, currency, amount): return str(amount)
    async def close(self): self._initialized = False
'''
            plugin_file.write_text(plugin_content)
            
            yield str(plugin_dir)
    
    def test_plugin_discovery_and_loading(self, temp_plugin_dir):
        """Test plugin discovery and loading from directory."""
        registry = ExchangePluginRegistry(temp_plugin_dir)
        
        # Load plugins
        registry.load_plugins()
        
        # Verify plugin was loaded
        assert registry._loaded
        assert len(registry._plugins) == 1
        assert "test_exchange" in registry._plugins
        
        # Verify plugin info
        plugin_info = registry.get_exchange_info("test_exchange")
        assert plugin_info["name"] == "Test Exchange"
        assert plugin_info["id"] == "test_exchange"
        assert plugin_info["version"] == "2.0.0"
        assert plugin_info["certified"] is True
    
    def test_plugin_instantiation_and_usage(self, temp_plugin_dir):
        """Test plugin instantiation and basic usage."""
        registry = ExchangePluginRegistry(temp_plugin_dir)
        registry.load_plugins()
        
        # Create plugin instance
        instance = registry.get_exchange("test_exchange", api_key="test_key")
        
        # Verify instance properties
        assert instance.name == "Test Exchange"
        assert instance.id == "test_exchange"
        assert instance.certified is True
        assert not instance._initialized
    
    @pytest.mark.asyncio
    async def test_plugin_async_operations(self, temp_plugin_dir):
        """Test async operations with plugin instance."""
        registry = ExchangePluginRegistry(temp_plugin_dir)
        registry.load_plugins()
        
        # Create plugin instance
        instance = registry.get_exchange("test_exchange", api_key="test_key")
        
        # Test initialization
        await instance.initialize()
        assert instance._initialized
        
        # Test market operations
        markets = await instance.load_markets()
        assert "BTC/USDT" in markets
        
        ticker = await instance.fetch_ticker("BTC/USDT")
        assert ticker["symbol"] == "BTC/USDT"
        assert ticker["last"] == 50000.0
        
        # Test order operations
        from crypto_bot.application.dtos.order import CreateOrderRequest, OrderSide, OrderType
        from decimal import Decimal
        
        order_request = CreateOrderRequest(
            exchange="test_exchange",
            symbol="BTC/USDT",
            side=OrderSide.BUY,
            type=OrderType.LIMIT,
            quantity=Decimal("0.1"),
            price=Decimal("50000")
        )
        
        order = await instance.create_order(order_request)
        assert order.symbol == "BTC/USDT"
        assert order.side == OrderSide.BUY
        
        # Test balance operations
        balance = await instance.fetch_balance("USDT")
        assert balance.currency == "USDT"
        assert balance.free == Decimal("10000")
        
        # Test cleanup
        await instance.close()
        assert not instance._initialized
    
    def test_plugin_validation_errors(self, temp_plugin_dir):
        """Test plugin validation error handling."""
        registry = ExchangePluginRegistry(temp_plugin_dir)
        
        # Test with invalid plugin class
        class InvalidPlugin(ExchangeBase):
            # Missing required attributes
            pass
        
        with pytest.raises(PluginValidationError):
            registry._validate_plugin(InvalidPlugin)
    
    def test_plugin_not_found_errors(self, temp_plugin_dir):
        """Test plugin not found error handling."""
        registry = ExchangePluginRegistry(temp_plugin_dir)
        registry.load_plugins()
        
        # Test getting non-existent plugin
        with pytest.raises(PluginNotFound):
            registry.get_exchange("nonexistent")
        
        # Test getting info for non-existent plugin
        with pytest.raises(PluginNotFound):
            registry.get_exchange_info("nonexistent")
    
    def test_plugin_reloading(self, temp_plugin_dir):
        """Test plugin reloading functionality."""
        registry = ExchangePluginRegistry(temp_plugin_dir)
        
        # Load plugins initially
        registry.load_plugins()
        initial_count = len(registry._plugins)
        
        # Reload plugins
        registry.reload_plugins()
        
        # Verify plugins were reloaded
        assert len(registry._plugins) == initial_count
        assert registry._loaded
    
    def test_plugin_unloading(self, temp_plugin_dir):
        """Test plugin unloading functionality."""
        registry = ExchangePluginRegistry(temp_plugin_dir)
        registry.load_plugins()
        
        # Create an instance
        instance = registry.get_exchange("test_exchange")
        assert "test_exchange" in registry._instances
        
        # Unload the plugin
        registry.unload_plugin("test_exchange")
        
        # Verify plugin was unloaded
        assert "test_exchange" not in registry._plugins
        assert "test_exchange" not in registry._instances
    
    def test_multiple_plugin_instances(self, temp_plugin_dir):
        """Test creating multiple instances of the same plugin."""
        registry = ExchangePluginRegistry(temp_plugin_dir)
        registry.load_plugins()
        
        # Create multiple instances
        instance1 = registry.get_exchange("test_exchange", api_key="key1")
        instance2 = registry.get_exchange("test_exchange", api_key="key2")
        
        # Verify they are different instances
        assert instance1 is not instance2
        assert instance1.api_key == "key1"
        assert instance2.api_key == "key2"
        
        # Verify both are tracked
        assert len(registry._instances) == 2
    
    def test_plugin_precision_methods(self, temp_plugin_dir):
        """Test plugin precision methods."""
        registry = ExchangePluginRegistry(temp_plugin_dir)
        registry.load_plugins()
        
        instance = registry.get_exchange("test_exchange")
        
        # Test precision methods
        assert instance.amount_to_precision("BTC/USDT", 1.23456789) == "1.23456789"
        assert instance.price_to_precision("BTC/USDT", 50000.123) == "50000.123"
        assert instance.cost_to_precision("BTC/USDT", 1000.456) == "1000.456"
        assert instance.currency_to_precision("USDT", 1000.789) == "1000.789"
    
    def test_plugin_string_representation(self, temp_plugin_dir):
        """Test plugin string representation."""
        registry = ExchangePluginRegistry(temp_plugin_dir)
        registry.load_plugins()
        
        instance = registry.get_exchange("test_exchange")
        
        # Test string representation
        str_repr = str(instance)
        assert "TestExchangePlugin" in str_repr
        assert "Test Exchange" in str_repr
        assert "test_exchange" in str_repr
        
        # Test repr
        repr_str = repr(instance)
        assert "TestExchangePlugin" in repr_str
        assert "test_exchange" in repr_str
