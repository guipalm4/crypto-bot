"""
Abstract base class for exchange implementations.

This module defines the core interface that all exchange plugins must implement.
It provides a standardized way to interact with different cryptocurrency exchanges
through a unified API, supporting authentication, market data retrieval, and trading operations.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional, Any, Union

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
    
    def __init__(self, api_key: Optional[str] = None, secret: Optional[str] = None, 
                 sandbox: bool = False, **kwargs):
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
        pass
    
    @property
    @abstractmethod
    def id(self) -> str:
        """
        Get the exchange ID.
        
        Returns:
            The exchange ID (e.g., 'binance', 'coinbasepro')
        """
        pass
    
    @property
    @abstractmethod
    def countries(self) -> List[str]:
        """
        Get the list of countries where the exchange operates.
        
        Returns:
            List of country codes (e.g., ['US', 'GB'])
        """
        pass
    
    @property
    @abstractmethod
    def urls(self) -> Dict[str, str]:
        """
        Get the exchange URLs.
        
        Returns:
            Dictionary mapping URL types to URLs (e.g., {'api': 'https://api.binance.com'})
        """
        pass
    
    @property
    @abstractmethod
    def version(self) -> str:
        """
        Get the exchange API version.
        
        Returns:
            The API version string
        """
        pass
    
    @property
    @abstractmethod
    def certified(self) -> bool:
        """
        Check if the exchange is certified by CCXT.
        
        Returns:
            True if the exchange is certified, False otherwise
        """
        pass
    
    @property
    @abstractmethod
    def has(self) -> Dict[str, bool]:
        """
        Get the capabilities of the exchange.
        
        Returns:
            Dictionary mapping capability names to boolean values
        """
        pass
    
    @abstractmethod
    async def initialize(self) -> None:
        """
        Initialize the exchange instance.
        
        This method should be called before using any other methods.
        It typically loads markets, validates credentials, and performs
        any necessary setup operations.
        
        Raises:
            ExchangeError: If initialization fails
            NetworkError: If network communication fails
        """
        pass
    
    @abstractmethod
    async def load_markets(self, reload: bool = False) -> Dict[str, Any]:
        """
        Load exchange markets.
        
        Args:
            reload: Whether to reload markets even if already loaded
            
        Returns:
            Dictionary of market information
            
        Raises:
            ExchangeError: If market loading fails
            NetworkError: If network communication fails
        """
        pass
    
    @abstractmethod
    async def fetch_markets(self) -> List[Dict[str, Any]]:
        """
        Fetch all available markets from the exchange.
        
        Returns:
            List of market dictionaries
            
        Raises:
            ExchangeError: If market fetching fails
            NetworkError: If network communication fails
        """
        pass
    
    @abstractmethod
    async def fetch_ticker(self, symbol: str) -> Dict[str, Any]:
        """
        Fetch ticker data for a symbol.
        
        Args:
            symbol: Trading pair symbol (e.g., 'BTC/USDT')
            
        Returns:
            Dictionary containing ticker data
            
        Raises:
            ValueError: If symbol is invalid
            ExchangeError: If ticker fetching fails
            NetworkError: If network communication fails
        """
        pass
    
    @abstractmethod
    async def fetch_tickers(self, symbols: Optional[List[str]] = None) -> Dict[str, Dict[str, Any]]:
        """
        Fetch ticker data for multiple symbols.
        
        Args:
            symbols: List of trading pair symbols (None for all)
            
        Returns:
            Dictionary mapping symbols to ticker data
            
        Raises:
            ExchangeError: If ticker fetching fails
            NetworkError: If network communication fails
        """
        pass
    
    @abstractmethod
    async def fetch_order_book(self, symbol: str, limit: Optional[int] = None) -> Dict[str, Any]:
        """
        Fetch order book for a symbol.
        
        Args:
            symbol: Trading pair symbol (e.g., 'BTC/USDT')
            limit: Maximum number of orders to return
            
        Returns:
            Dictionary containing order book data
            
        Raises:
            ValueError: If symbol is invalid
            ExchangeError: If order book fetching fails
            NetworkError: If network communication fails
        """
        pass
    
    @abstractmethod
    async def fetch_ohlcv(self, symbol: str, timeframe: str = '1m', 
                         since: Optional[datetime] = None, limit: Optional[int] = None) -> List[List[Union[int, float]]]:
        """
        Fetch OHLCV (candlestick) data for a symbol.
        
        Args:
            symbol: Trading pair symbol (e.g., 'BTC/USDT')
            timeframe: Timeframe for the data (e.g., '1m', '5m', '1h', '1d')
            since: Start time for the data
            limit: Maximum number of candles to return
            
        Returns:
            List of OHLCV data arrays [timestamp, open, high, low, close, volume]
            
        Raises:
            ValueError: If symbol or timeframe is invalid
            ExchangeError: If OHLCV fetching fails
            NetworkError: If network communication fails
        """
        pass
    
    @abstractmethod
    async def fetch_trades(self, symbol: str, since: Optional[datetime] = None, 
                          limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Fetch recent trades for a symbol.
        
        Args:
            symbol: Trading pair symbol (e.g., 'BTC/USDT')
            since: Start time for the data
            limit: Maximum number of trades to return
            
        Returns:
            List of trade dictionaries
            
        Raises:
            ValueError: If symbol is invalid
            ExchangeError: If trades fetching fails
            NetworkError: If network communication fails
        """
        pass
    
    @abstractmethod
    async def create_order(self, request: CreateOrderRequest) -> OrderDTO:
        """
        Create a new order.
        
        Args:
            request: Order creation request
            
        Returns:
            Created order information
            
        Raises:
            ValueError: If order parameters are invalid
            InsufficientBalance: If account balance is insufficient
            ExchangeError: If order creation fails
            NetworkError: If network communication fails
        """
        pass
    
    @abstractmethod
    async def cancel_order(self, order_id: str, symbol: Optional[str] = None) -> OrderDTO:
        """
        Cancel an existing order.
        
        Args:
            order_id: Exchange-specific order ID
            symbol: Trading pair symbol (required by some exchanges)
            
        Returns:
            Canceled order information
            
        Raises:
            ValueError: If order ID is invalid
            OrderNotFound: If order doesn't exist
            ExchangeError: If order cancellation fails
            NetworkError: If network communication fails
        """
        pass
    
    @abstractmethod
    async def fetch_order(self, order_id: str, symbol: Optional[str] = None) -> OrderDTO:
        """
        Fetch order details.
        
        Args:
            order_id: Exchange-specific order ID
            symbol: Trading pair symbol (required by some exchanges)
            
        Returns:
            Order information
            
        Raises:
            ValueError: If order ID is invalid
            OrderNotFound: If order doesn't exist
            ExchangeError: If order fetching fails
            NetworkError: If network communication fails
        """
        pass
    
    @abstractmethod
    async def fetch_order_status(self, order_id: str, symbol: Optional[str] = None) -> OrderStatusDTO:
        """
        Fetch order status.
        
        Args:
            order_id: Exchange-specific order ID
            symbol: Trading pair symbol (required by some exchanges)
            
        Returns:
            Order status information
            
        Raises:
            ValueError: If order ID is invalid
            OrderNotFound: If order doesn't exist
            ExchangeError: If status fetching fails
            NetworkError: If network communication fails
        """
        pass
    
    @abstractmethod
    async def fetch_open_orders(self, symbol: Optional[str] = None) -> List[OrderDTO]:
        """
        Fetch open orders.
        
        Args:
            symbol: Trading pair symbol (None for all pairs)
            
        Returns:
            List of open orders
            
        Raises:
            ExchangeError: If orders fetching fails
            NetworkError: If network communication fails
        """
        pass
    
    @abstractmethod
    async def cancel_all_orders(self, symbol: Optional[str] = None) -> List[OrderDTO]:
        """
        Cancel all open orders.
        
        Args:
            symbol: Trading pair symbol (None for all pairs)
            
        Returns:
            List of canceled orders
            
        Raises:
            ExchangeError: If cancellation fails
            NetworkError: If network communication fails
        """
        pass
    
    @abstractmethod
    async def fetch_balance(self, currency: Optional[str] = None) -> Union[BalanceDTO, Dict[str, BalanceDTO]]:
        """
        Fetch account balance.
        
        Args:
            currency: Specific currency to query (None for all currencies)
            
        Returns:
            If currency is specified: BalanceDTO for that currency
            If currency is None: Dict mapping currency symbols to BalanceDTOs
            
        Raises:
            ExchangeError: If balance fetching fails
            NetworkError: If network communication fails
        """
        pass
    
    @abstractmethod
    async def fetch_positions(self, symbols: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Fetch trading positions (for derivatives exchanges).
        
        Args:
            symbols: List of trading pair symbols (None for all)
            
        Returns:
            List of position dictionaries
            
        Raises:
            ExchangeError: If positions fetching fails
            NetworkError: If network communication fails
        """
        pass
    
    @abstractmethod
    async def fetch_my_trades(self, symbol: Optional[str] = None, 
                             since: Optional[datetime] = None, 
                             limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Fetch user's trade history.
        
        Args:
            symbol: Trading pair symbol (None for all pairs)
            since: Start time for the data
            limit: Maximum number of trades to return
            
        Returns:
            List of trade dictionaries
            
        Raises:
            ExchangeError: If trades fetching fails
            NetworkError: If network communication fails
        """
        pass
    
    @abstractmethod
    def amount_to_precision(self, symbol: str, amount: Union[float, str, Decimal]) -> str:
        """
        Convert amount to exchange-specific precision.
        
        Args:
            symbol: Trading pair symbol
            amount: Amount to convert
            
        Returns:
            Formatted amount string
            
        Raises:
            ValueError: If symbol is invalid or amount is negative
        """
        pass
    
    @abstractmethod
    def price_to_precision(self, symbol: str, price: Union[float, str, Decimal]) -> str:
        """
        Convert price to exchange-specific precision.
        
        Args:
            symbol: Trading pair symbol
            price: Price to convert
            
        Returns:
            Formatted price string
            
        Raises:
            ValueError: If symbol is invalid or price is negative
        """
        pass
    
    @abstractmethod
    def cost_to_precision(self, symbol: str, cost: Union[float, str, Decimal]) -> str:
        """
        Convert cost to exchange-specific precision.
        
        Args:
            symbol: Trading pair symbol
            cost: Cost to convert
            
        Returns:
            Formatted cost string
            
        Raises:
            ValueError: If symbol is invalid or cost is negative
        """
        pass
    
    @abstractmethod
    def currency_to_precision(self, currency: str, amount: Union[float, str, Decimal]) -> str:
        """
        Convert currency amount to exchange-specific precision.
        
        Args:
            currency: Currency code
            amount: Amount to convert
            
        Returns:
            Formatted amount string
            
        Raises:
            ValueError: If currency is invalid or amount is negative
        """
        pass
    
    @abstractmethod
    async def close(self) -> None:
        """
        Close the exchange connection and cleanup resources.
        
        This method should be called when the exchange instance is no longer needed.
        It typically closes HTTP sessions, WebSocket connections, and other resources.
        """
        pass
    
    def __str__(self) -> str:
        """Return string representation of the exchange."""
        return f"{self.__class__.__name__}(name={self.name}, id={self.id})"
    
    def __repr__(self) -> str:
        """Return detailed string representation of the exchange."""
        return (f"{self.__class__.__name__}(name={self.name}, id={self.id}, "
                f"sandbox={self.sandbox}, initialized={self._initialized})")
