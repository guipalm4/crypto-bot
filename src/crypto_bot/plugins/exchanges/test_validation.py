"""
Test file for plugin validation system.

This file contains example plugins (valid and invalid) to test
the plugin validation and loading system.
"""

from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from decimal import Decimal

from crypto_bot.infrastructure.exchanges.base import ExchangeBase
from crypto_bot.application.dtos.order import (
    BalanceDTO,
    CreateOrderRequest,
    OrderDTO,
    OrderStatusDTO,
)


class ValidExchangePlugin(ExchangeBase):
    """
    Valid exchange plugin for testing.
    
    This plugin implements all required methods and attributes
    and should pass validation.
    """
    
    name = "Test Exchange"
    id = "test_exchange"
    countries = ["US", "GB"]
    urls = {
        "api": "https://api.testexchange.com",
        "www": "https://www.testexchange.com",
        "doc": "https://docs.testexchange.com"
    }
    version = "1.0.0"
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
    
    async def initialize(self) -> None:
        """Initialize the exchange."""
        self._initialized = True
    
    async def load_markets(self, reload: bool = False) -> Dict[str, Any]:
        """Load exchange markets."""
        return {"BTC/USDT": {"id": "BTCUSDT", "symbol": "BTC/USDT"}}
    
    async def fetch_markets(self) -> List[Dict[str, Any]]:
        """Fetch all available markets."""
        return [{"id": "BTCUSDT", "symbol": "BTC/USDT", "base": "BTC", "quote": "USDT"}]
    
    async def fetch_ticker(self, symbol: str) -> Dict[str, Any]:
        """Fetch ticker data."""
        return {
            "symbol": symbol,
            "last": 50000.0,
            "bid": 49999.0,
            "ask": 50001.0,
            "high": 51000.0,
            "low": 49000.0,
            "volume": 1000.0,
            "timestamp": datetime.now()
        }
    
    async def fetch_tickers(self, symbols: Optional[List[str]] = None) -> Dict[str, Dict[str, Any]]:
        """Fetch ticker data for multiple symbols."""
        return {"BTC/USDT": await self.fetch_ticker("BTC/USDT")}
    
    async def fetch_order_book(self, symbol: str, limit: Optional[int] = None) -> Dict[str, Any]:
        """Fetch order book."""
        return {
            "symbol": symbol,
            "bids": [[49999.0, 1.0], [49998.0, 2.0]],
            "asks": [[50001.0, 1.0], [50002.0, 2.0]],
            "timestamp": datetime.now()
        }
    
    async def fetch_ohlcv(self, symbol: str, timeframe: str = '1m', 
                         since: Optional[datetime] = None, limit: Optional[int] = None) -> List[List[Union[int, float]]]:
        """Fetch OHLCV data."""
        return [
            [int(datetime.now().timestamp() * 1000), 50000.0, 51000.0, 49000.0, 50000.0, 1000.0]
        ]
    
    async def fetch_trades(self, symbol: str, since: Optional[datetime] = None, 
                          limit: Optional[int] = None) -> List[Dict[str, Any]]:
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
    
    async def create_order(self, request: CreateOrderRequest) -> OrderDTO:
        """Create a new order."""
        return OrderDTO(
            id="order_123",
            exchange_order_id="ex_123",
            exchange=self.name,
            symbol=request.symbol,
            side=request.side,
            type=request.type,
            status="open",
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
    
    async def cancel_order(self, order_id: str, symbol: Optional[str] = None) -> OrderDTO:
        """Cancel an order."""
        return OrderDTO(
            id="order_123",
            exchange_order_id=order_id,
            exchange=self.name,
            symbol=symbol or "BTC/USDT",
            side="buy",
            type="limit",
            status="canceled",
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
    
    async def fetch_order(self, order_id: str, symbol: Optional[str] = None) -> OrderDTO:
        """Fetch order details."""
        return OrderDTO(
            id="order_123",
            exchange_order_id=order_id,
            exchange=self.name,
            symbol=symbol or "BTC/USDT",
            side="buy",
            type="limit",
            status="open",
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
    
    async def fetch_order_status(self, order_id: str, symbol: Optional[str] = None) -> OrderStatusDTO:
        """Fetch order status."""
        return OrderStatusDTO(
            order_id=order_id,
            status="open",
            filled_quantity=Decimal("0"),
            remaining_quantity=Decimal("1"),
            average_price=None,
            last_update=datetime.now()
        )
    
    async def fetch_open_orders(self, symbol: Optional[str] = None) -> List[OrderDTO]:
        """Fetch open orders."""
        return []
    
    async def cancel_all_orders(self, symbol: Optional[str] = None) -> List[OrderDTO]:
        """Cancel all orders."""
        return []
    
    async def fetch_balance(self, currency: Optional[str] = None) -> Union[BalanceDTO, Dict[str, BalanceDTO]]:
        """Fetch account balance."""
        balance = BalanceDTO(
            exchange=self.name,
            currency="USDT",
            free=Decimal("10000"),
            used=Decimal("0"),
            total=Decimal("10000"),
            timestamp=datetime.now()
        )
        
        if currency:
            return balance
        else:
            return {"USDT": balance}
    
    async def fetch_positions(self, symbols: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Fetch trading positions."""
        return []
    
    async def fetch_my_trades(self, symbol: Optional[str] = None, 
                             since: Optional[datetime] = None, 
                             limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Fetch user's trade history."""
        return []
    
    def amount_to_precision(self, symbol: str, amount: Union[float, str, Decimal]) -> str:
        """Convert amount to precision."""
        return str(amount)
    
    def price_to_precision(self, symbol: str, price: Union[float, str, Decimal]) -> str:
        """Convert price to precision."""
        return str(price)
    
    def cost_to_precision(self, symbol: str, cost: Union[float, str, Decimal]) -> str:
        """Convert cost to precision."""
        return str(cost)
    
    def currency_to_precision(self, currency: str, amount: Union[float, str, Decimal]) -> str:
        """Convert currency amount to precision."""
        return str(amount)
    
    async def close(self) -> None:
        """Close the exchange connection."""
        self._initialized = False


class InvalidExchangePlugin(ExchangeBase):
    """
    Invalid exchange plugin for testing.
    
    This plugin is missing required attributes and methods
    and should fail validation.
    """
    
    # Missing required attributes: name, id, countries, urls, version
    # Missing required methods: initialize, load_markets, create_order, etc.
    
    async def fetch_ticker(self, symbol: str) -> Dict[str, Any]:
        """Only implement one method to test validation."""
        return {"symbol": symbol}


class IncompleteExchangePlugin(ExchangeBase):
    """
    Incomplete exchange plugin for testing.
    
    This plugin has some required attributes but is missing
    required methods and should fail validation.
    """
    
    name = "Incomplete Exchange"
    id = "incomplete_exchange"
    countries = ["US"]
    urls = {"api": "https://api.incomplete.com"}
    version = "1.0.0"
    certified = False
    has = {}
    
    # Missing most required methods
    async def fetch_ticker(self, symbol: str) -> Dict[str, Any]:
        """Only implement one method."""
        return {"symbol": symbol}
