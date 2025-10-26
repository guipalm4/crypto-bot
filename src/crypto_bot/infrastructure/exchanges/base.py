"""
Abstract base class for exchange implementations.

This module defines the core interface that all exchange plugins must implement.
It provides a standardized way to interact with different cryptocurrency exchanges
through a unified API, supporting authentication, market data retrieval, and trading operations.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from crypto_bot.application.dtos.order import (
    BalanceDTO,
    CreateOrderRequest,
    OrderDTO,
    OrderStatusDTO,
)


class ExchangeBase(ABC):
    """
    Abstract base class for exchange implementations.

    This class defines the contract that all exchange plugins must implement.
    It provides a unified interface for interacting with different cryptocurrency
    exchanges, supporting both public and private API operations.

    All exchange implementations should inherit from this class and implement
    all abstract methods. The class is designed to work with CCXT 4.x and
    supports asynchronous operations for better performance.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        secret: Optional[str] = None,
        sandbox: bool = False,
        **kwargs: Any,
    ) -> None:
        """
        Initialize the exchange instance.

        Args:
            api_key: API key for private operations (optional for public-only exchanges)
            secret: API secret for private operations (optional for public-only exchanges)
            sandbox: Whether to use sandbox/testnet mode
            **kwargs: Additional exchange-specific configuration parameters
        """
        self.api_key = api_key
        self.secret = secret
        self.sandbox = sandbox
        self.config = kwargs
        self._initialized = False

    @property
    @abstractmethod
    def name(self) -> str:
        """
        Get the exchange name.

        Returns:
            The exchange name (e.g., 'binance', 'coinbase')
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def id(self) -> str:
        """
        Get the exchange ID.

        Returns:
            The exchange ID (e.g., 'binance', 'coinbasepro')
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def countries(self) -> List[str]:
        """
        Get the list of countries where the exchange operates.

        Returns:
            List of country codes (e.g., ['US', 'GB'])
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def urls(self) -> Dict[str, str]:
        """
        Get the exchange URLs.

        Returns:
            Dictionary mapping URL types to URLs (e.g., {'api': 'https://api.binance.com'})
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def version(self) -> str:
        """
        Get the exchange API version.

        Returns:
            The API version string
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def certified(self) -> bool:
        """
        Check if the exchange is certified by CCXT.

        Returns:
            True if the exchange is certified, False otherwise
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def has(self) -> Dict[str, bool]:
        """
        Get the capabilities of the exchange.

        Returns:
            Dictionary mapping capability names to boolean values
        """
        raise NotImplementedError

    @abstractmethod
    async def initialize(self) -> None:
        """
        Initialize the exchange instance.
        """
        raise NotImplementedError

    @abstractmethod
    async def load_markets(self, reload: bool = False) -> Dict[str, Any]:
        """
        Load exchange markets.
        """
        raise NotImplementedError

    @abstractmethod
    async def fetch_markets(self) -> List[Dict[str, Any]]:
        """
        Fetch all available markets from the exchange.
        """
        raise NotImplementedError

    @abstractmethod
    async def fetch_ticker(self, symbol: str) -> Dict[str, Any]:
        """
        Fetch ticker data for a symbol.
        """
        raise NotImplementedError

    @abstractmethod
    async def fetch_tickers(
        self, symbols: Optional[List[str]] = None
    ) -> Dict[str, Dict[str, Any]]:
        """
        Fetch ticker data for multiple symbols.
        """
        raise NotImplementedError

    @abstractmethod
    async def fetch_order_book(
        self, symbol: str, limit: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Fetch order book for a symbol.
        """
        raise NotImplementedError

    @abstractmethod
    async def fetch_ohlcv(
        self,
        symbol: str,
        timeframe: str = "1m",
        since: Optional[datetime] = None,
        limit: Optional[int] = None,
    ) -> List[List[int | float]]:
        """
        Fetch OHLCV (candlestick) data for a symbol.
        """
        raise NotImplementedError

    @abstractmethod
    async def fetch_trades(
        self, symbol: str, since: Optional[datetime] = None, limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch recent trades for a symbol.
        """
        raise NotImplementedError

    @abstractmethod
    async def create_order(self, request: CreateOrderRequest) -> OrderDTO:
        """
        Create a new order.
        """
        raise NotImplementedError

    @abstractmethod
    async def cancel_order(
        self, order_id: str, symbol: Optional[str] = None
    ) -> OrderDTO:
        """
        Cancel an existing order.
        """
        raise NotImplementedError

    @abstractmethod
    async def fetch_order(
        self, order_id: str, symbol: Optional[str] = None
    ) -> OrderDTO:
        """
        Fetch order details.
        """
        raise NotImplementedError

    @abstractmethod
    async def fetch_order_status(
        self, order_id: str, symbol: Optional[str] = None
    ) -> OrderStatusDTO:
        """
        Fetch order status.
        """
        raise NotImplementedError

    @abstractmethod
    async def fetch_open_orders(self, symbol: Optional[str] = None) -> List[OrderDTO]:
        """
        Fetch open orders.
        """
        raise NotImplementedError

    @abstractmethod
    async def cancel_all_orders(self, symbol: Optional[str] = None) -> List[OrderDTO]:
        """
        Cancel all open orders.
        """
        raise NotImplementedError

    @abstractmethod
    async def fetch_balance(
        self, currency: Optional[str] = None
    ) -> BalanceDTO | Dict[str, BalanceDTO]:
        """
        Fetch account balance.
        """
        raise NotImplementedError

    @abstractmethod
    async def fetch_positions(
        self, symbols: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch trading positions (for derivatives exchanges).
        """
        raise NotImplementedError

    @abstractmethod
    async def fetch_my_trades(
        self,
        symbol: Optional[str] = None,
        since: Optional[datetime] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Fetch user's trade history.
        """
        raise NotImplementedError

    @abstractmethod
    def amount_to_precision(self, symbol: str, amount: float | str | Decimal) -> str:
        """
        Convert amount to exchange-specific precision.
        """
        raise NotImplementedError

    @abstractmethod
    def price_to_precision(self, symbol: str, price: float | str | Decimal) -> str:
        """
        Convert price to exchange-specific precision.
        """
        raise NotImplementedError

    @abstractmethod
    def cost_to_precision(self, symbol: str, cost: float | str | Decimal) -> str:
        """
        Convert cost to exchange-specific precision.
        """
        raise NotImplementedError

    @abstractmethod
    def currency_to_precision(
        self, currency: str, amount: float | str | Decimal
    ) -> str:
        """
        Convert currency amount to exchange-specific precision.
        """
        raise NotImplementedError

    @abstractmethod
    async def close(self) -> None:
        """
        Close the exchange connection and cleanup resources.
        """
        raise NotImplementedError

    def __str__(self) -> str:
        """Return string representation of the exchange."""
        return f"{self.__class__.__name__}(name={self.name}, id={self.id})"

    def __repr__(self) -> str:
        """Return detailed string representation of the exchange."""
        return (
            f"{self.__class__.__name__}(name={self.name}, id={self.id}, "
            f"sandbox={self.sandbox}, initialized={self._initialized})"
        )
