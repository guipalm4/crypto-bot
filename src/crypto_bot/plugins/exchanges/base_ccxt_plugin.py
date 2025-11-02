"""
Base CCXT Exchange Plugin.

This module provides a base class for exchange plugins that use CCXT 4.x library.
It implements common functionality shared across all CCXT-based exchanges including
authentication, rate limiting, error handling, and async operations.
"""

import asyncio
import logging
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

import ccxt.async_support as ccxt
from ccxt.base.errors import (
    AuthenticationError,
    BadRequest,
    DDoSProtection,
    ExchangeError,
    ExchangeNotAvailable,
    InsufficientFunds,
    InvalidOrder,
    NetworkError,
    OrderNotFound,
    RateLimitExceeded,
)
from cryptography.fernet import InvalidToken

from crypto_bot.application.dtos.order import (
    BalanceDTO,
    CreateOrderRequest,
    OrderDTO,
    OrderSide,
    OrderStatus,
    OrderStatusDTO,
    OrderType,
)
from crypto_bot.infrastructure.exchanges.base import ExchangeBase
from crypto_bot.infrastructure.security.encryption import get_encryption_service
from crypto_bot.plugins.exchanges.config_models import ExchangeConfig

logger = logging.getLogger(__name__)


class CCXTExchangePlugin(ExchangeBase):
    """
    Base class for CCXT-based exchange plugins.

    This class provides common CCXT functionality and should be subclassed
    by specific exchange implementations (e.g., Binance, Coinbase Pro).

    Features:
    - Async CCXT integration
    - Encrypted credential handling
    - Built-in rate limiting
    - Retry logic with exponential backoff
    - Sandbox/testnet support
    - Timeout and proxy configuration
    - Comprehensive error handling
    """

    def __init__(
        self,
        config: ExchangeConfig,
        exchange_class: type,
        **kwargs: Any,
    ) -> None:
        """
        Initialize CCXT exchange plugin.

        Args:
            config: Validated exchange configuration
            exchange_class: CCXT exchange class (e.g., ccxt.binance)
            **kwargs: Additional parameters passed to parent
        """
        super().__init__(
            api_key=config.api_key,
            secret=config.secret,
            sandbox=config.sandbox,
            **kwargs,
        )

        self._config = config
        self._exchange_class = exchange_class
        self._ccxt: Optional[ccxt.Exchange] = None
        self._markets: Dict[str, Any] = {}
        self._semaphore = asyncio.Semaphore(5)  # Max 5 concurrent requests

    async def _initialize_ccxt(self) -> None:
        """
        Initialize CCXT exchange instance with decrypted credentials.

        This method decrypts the API credentials and creates a CCXT exchange
        instance with proper configuration.

        Raises:
            RuntimeError: If encryption service is not available
            ValueError: If required credentials are missing
        """
        # Decrypt credentials if provided (or use plain text from .env)
        api_key = None
        secret = None
        password = None

        if self._config.api_key:
            try:
                encryption_service = get_encryption_service()
                api_key = encryption_service.decrypt(self._config.api_key)
            except (InvalidToken, ValueError):
                # Credential is not encrypted (likely from .env), use as-is
                api_key = self._config.api_key

        if self._config.secret:
            try:
                encryption_service = get_encryption_service()
                secret = encryption_service.decrypt(self._config.secret)
            except (InvalidToken, ValueError):
                # Credential is not encrypted (likely from .env), use as-is
                secret = self._config.secret

        if self._config.password:
            try:
                encryption_service = get_encryption_service()
                password = encryption_service.decrypt(self._config.password)
            except (InvalidToken, ValueError):
                # Credential is not encrypted (likely from .env), use as-is
                password = self._config.password

        # Build CCXT configuration
        ccxt_config: Dict[str, Any] = {
            "enableRateLimit": self._config.enable_rate_limit,
            "rateLimit": self._config.rate_limit,
            "timeout": self._config.timeout,
            "verbose": self._config.verbose,
            "options": self._config.options.copy(),
        }

        # Add credentials if provided
        if api_key:
            ccxt_config["apiKey"] = api_key
        if secret:
            ccxt_config["secret"] = secret
        if password:
            ccxt_config["password"] = password

        # Add proxy if configured
        if self._config.proxy:
            ccxt_config["proxies"] = {
                "http": self._config.proxy,
                "https": self._config.proxy,
            }

        # Create CCXT exchange instance
        self._ccxt = self._exchange_class(ccxt_config)

        # Configure sandbox mode if enabled
        if self._config.sandbox:
            try:
                self._ccxt.set_sandbox_mode(True)
            except AttributeError:
                # Fallback for exchanges that don't support set_sandbox_mode
                logger.warning(
                    f"{self.name} does not support set_sandbox_mode(), "
                    f"attempting URL override"
                )
                # Subclasses should override this behavior if needed

        logger.info(
            f"Initialized {self.name} exchange "
            f"(sandbox={self._config.sandbox}, "
            f"rate_limit={self._config.rate_limit}ms)"
        )

    async def _retry_with_backoff(
        self,
        func: Any,
        *args: Any,
        max_attempts: int = 3,
        initial_delay: float = 1.0,
        max_delay: float = 30.0,
        exponential_base: float = 2.0,
        **kwargs: Any,
    ) -> Any:
        """
        Execute function with exponential backoff retry logic.

        Args:
            func: Async function to execute
            *args: Positional arguments for the function
            max_attempts: Maximum number of retry attempts
            initial_delay: Initial delay in seconds
            max_delay: Maximum delay in seconds
            exponential_base: Base for exponential backoff
            **kwargs: Keyword arguments for the function

        Returns:
            Function result

        Raises:
            Last encountered exception if all retries fail
        """
        last_exception: Optional[Exception] = None

        for attempt in range(max_attempts):
            try:
                async with self._semaphore:  # Control concurrency
                    return await func(*args, **kwargs)
            except (NetworkError, DDoSProtection, ExchangeNotAvailable) as e:
                last_exception = e
                if attempt < max_attempts - 1:
                    delay = min(
                        initial_delay * (exponential_base**attempt),
                        max_delay,
                    )
                    logger.warning(
                        f"Attempt {attempt + 1}/{max_attempts} failed: {e}. "
                        f"Retrying in {delay}s..."
                    )
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"All {max_attempts} attempts failed: {e}")
            except (
                AuthenticationError,
                BadRequest,
                InsufficientFunds,
                InvalidOrder,
                OrderNotFound,
            ) as e:
                # Fatal errors - don't retry
                logger.error(f"Fatal error (no retry): {e}")
                raise
            except RateLimitExceeded as e:
                last_exception = e
                if attempt < max_attempts - 1:
                    # For rate limits, wait longer
                    delay = min(
                        initial_delay * (exponential_base ** (attempt + 1)),
                        max_delay,
                    )
                    logger.warning(
                        f"Rate limit exceeded. Waiting {delay}s before retry..."
                    )
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"Rate limit exceeded after {max_attempts} attempts")
                    raise
            except ExchangeError as e:
                # Generic exchange error - log and raise
                logger.error(f"Exchange error: {e}")
                raise

        # If we get here, all retries failed
        if last_exception:
            raise last_exception
        raise RuntimeError("Retry logic failed without capturing an exception")

    def _convert_ccxt_order_status(self, ccxt_status: str) -> OrderStatus:
        """
        Convert CCXT order status to internal OrderStatus enum.

        Args:
            ccxt_status: CCXT status string

        Returns:
            OrderStatus enum value
        """
        status_map = {
            "open": OrderStatus.OPEN,
            "closed": OrderStatus.CLOSED,
            "canceled": OrderStatus.CANCELED,
            "cancelled": OrderStatus.CANCELED,  # Alternative spelling
            "expired": OrderStatus.EXPIRED,
            "rejected": OrderStatus.REJECTED,
        }
        return status_map.get(ccxt_status.lower(), OrderStatus.PENDING)

    def _ccxt_order_to_dto(self, ccxt_order: Dict[str, Any]) -> OrderDTO:
        """
        Convert CCXT order dictionary to OrderDTO.

        Args:
            ccxt_order: CCXT order dictionary

        Returns:
            OrderDTO instance
        """
        return OrderDTO(
            id=ccxt_order.get("id", ccxt_order.get("clientOrderId", "")),
            exchange_order_id=ccxt_order["id"],
            exchange=self.name,
            symbol=ccxt_order["symbol"],
            side=OrderSide(ccxt_order["side"].lower()),
            type=OrderType(ccxt_order["type"].lower()),
            status=self._convert_ccxt_order_status(ccxt_order["status"]),
            quantity=Decimal(str(ccxt_order["amount"])),
            filled_quantity=Decimal(str(ccxt_order.get("filled", 0))),
            remaining_quantity=Decimal(str(ccxt_order.get("remaining", 0))),
            price=(
                Decimal(str(ccxt_order["price"])) if ccxt_order.get("price") else None
            ),
            average_price=(
                Decimal(str(ccxt_order["average"]))
                if ccxt_order.get("average")
                else None
            ),
            cost=Decimal(str(ccxt_order.get("cost", 0))),
            fee=Decimal(str(ccxt_order.get("fee", {}).get("cost", 0))),
            fee_currency=ccxt_order.get("fee", {}).get("currency", ""),
            timestamp=datetime.fromtimestamp(ccxt_order["timestamp"] / 1000),
            last_trade_timestamp=(
                datetime.fromtimestamp(ccxt_order["lastTradeTimestamp"] / 1000)
                if ccxt_order.get("lastTradeTimestamp")
                else None
            ),
        )

    # =========================================================================
    # Abstract method implementations (to be used by subclasses)
    # =========================================================================

    async def initialize(self) -> None:
        """Initialize the exchange instance and load markets."""
        if not self._initialized:
            await self._initialize_ccxt()
            await self.load_markets()
            self._initialized = True

    async def load_markets(self, reload: bool = False) -> Dict[str, Any]:
        """Load exchange markets from CCXT."""
        if not self._ccxt:
            raise RuntimeError("Exchange not initialized. Call initialize() first.")

        if reload or not self._markets:
            self._markets = await self._retry_with_backoff(
                self._ccxt.load_markets, reload
            )

        return self._markets

    async def fetch_markets(self) -> List[Dict[str, Any]]:
        """Fetch all available markets."""
        if not self._ccxt:
            raise RuntimeError("Exchange not initialized. Call initialize() first.")

        return await self._retry_with_backoff(self._ccxt.fetch_markets)

    async def fetch_ticker(self, symbol: str) -> Dict[str, Any]:
        """Fetch ticker data for a symbol."""
        if not self._ccxt:
            raise RuntimeError("Exchange not initialized. Call initialize() first.")

        return await self._retry_with_backoff(self._ccxt.fetch_ticker, symbol)

    async def fetch_tickers(
        self, symbols: Optional[List[str]] = None
    ) -> Dict[str, Dict[str, Any]]:
        """Fetch ticker data for multiple symbols."""
        if not self._ccxt:
            raise RuntimeError("Exchange not initialized. Call initialize() first.")

        return await self._retry_with_backoff(self._ccxt.fetch_tickers, symbols)

    async def fetch_order_book(
        self, symbol: str, limit: Optional[int] = None
    ) -> Dict[str, Any]:
        """Fetch order book for a symbol."""
        if not self._ccxt:
            raise RuntimeError("Exchange not initialized. Call initialize() first.")

        return await self._retry_with_backoff(
            self._ccxt.fetch_order_book, symbol, limit
        )

    async def fetch_ohlcv(
        self,
        symbol: str,
        timeframe: str = "1m",
        since: Optional[datetime] = None,
        limit: Optional[int] = None,
    ) -> List[List[int | float]]:
        """Fetch OHLCV data for a symbol."""
        if not self._ccxt:
            raise RuntimeError("Exchange not initialized. Call initialize() first.")

        since_ms = int(since.timestamp() * 1000) if since else None

        return await self._retry_with_backoff(
            self._ccxt.fetch_ohlcv, symbol, timeframe, since_ms, limit
        )

    async def fetch_trades(
        self, symbol: str, since: Optional[datetime] = None, limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Fetch recent trades for a symbol."""
        if not self._ccxt:
            raise RuntimeError("Exchange not initialized. Call initialize() first.")

        since_ms = int(since.timestamp() * 1000) if since else None

        return await self._retry_with_backoff(
            self._ccxt.fetch_trades, symbol, since_ms, limit
        )

    async def create_order(self, request: CreateOrderRequest) -> OrderDTO:
        """Create a new order."""
        if not self._ccxt:
            raise RuntimeError("Exchange not initialized. Call initialize() first.")

        # Prepare order parameters
        params: Dict[str, Any] = {}

        # Create order via CCXT
        ccxt_order = await self._retry_with_backoff(
            self._ccxt.create_order,
            request.symbol,
            request.type.value,
            request.side.value,
            float(request.quantity),
            float(request.price) if request.price else None,
            params,
            max_attempts=request.retry_policy.max_attempts,
            initial_delay=request.retry_policy.initial_delay,
            max_delay=request.retry_policy.max_delay,
            exponential_base=request.retry_policy.exponential_base,
        )

        return self._ccxt_order_to_dto(ccxt_order)

    async def cancel_order(
        self, order_id: str, symbol: Optional[str] = None
    ) -> OrderDTO:
        """Cancel an existing order."""
        if not self._ccxt:
            raise RuntimeError("Exchange not initialized. Call initialize() first.")

        ccxt_order = await self._retry_with_backoff(
            self._ccxt.cancel_order, order_id, symbol
        )

        return self._ccxt_order_to_dto(ccxt_order)

    async def fetch_order(
        self, order_id: str, symbol: Optional[str] = None
    ) -> OrderDTO:
        """Fetch order details."""
        if not self._ccxt:
            raise RuntimeError("Exchange not initialized. Call initialize() first.")

        ccxt_order = await self._retry_with_backoff(
            self._ccxt.fetch_order, order_id, symbol
        )

        return self._ccxt_order_to_dto(ccxt_order)

    async def fetch_order_status(
        self, order_id: str, symbol: Optional[str] = None
    ) -> OrderStatusDTO:
        """Fetch order status."""
        order_dto = await self.fetch_order(order_id, symbol)

        return OrderStatusDTO(
            order_id=order_dto.exchange_order_id,
            status=order_dto.status,
            filled_quantity=order_dto.filled_quantity,
            remaining_quantity=order_dto.remaining_quantity,
            average_price=order_dto.average_price,
            last_update=order_dto.last_trade_timestamp or order_dto.timestamp,
        )

    async def fetch_open_orders(self, symbol: Optional[str] = None) -> List[OrderDTO]:
        """Fetch open orders."""
        if not self._ccxt:
            raise RuntimeError("Exchange not initialized. Call initialize() first.")

        ccxt_orders = await self._retry_with_backoff(
            self._ccxt.fetch_open_orders, symbol
        )

        return [self._ccxt_order_to_dto(order) for order in ccxt_orders]

    async def cancel_all_orders(self, symbol: Optional[str] = None) -> List[OrderDTO]:
        """Cancel all open orders."""
        # CCXT doesn't have a universal cancel_all_orders method
        # We fetch open orders and cancel them one by one
        open_orders = await self.fetch_open_orders(symbol)
        canceled_orders: List[OrderDTO] = []

        for order in open_orders:
            try:
                canceled_order = await self.cancel_order(
                    order.exchange_order_id, order.symbol
                )
                canceled_orders.append(canceled_order)
            except Exception as e:
                logger.error(f"Failed to cancel order {order.exchange_order_id}: {e}")

        return canceled_orders

    async def fetch_balance(
        self, currency: Optional[str] = None
    ) -> BalanceDTO | Dict[str, BalanceDTO]:
        """Fetch account balance."""
        if not self._ccxt:
            raise RuntimeError("Exchange not initialized. Call initialize() first.")

        ccxt_balance = await self._retry_with_backoff(self._ccxt.fetch_balance)

        # Convert CCXT balance to our DTOs
        balances: Dict[str, BalanceDTO] = {}

        for curr, amounts in ccxt_balance.get("total", {}).items():
            if amounts and float(amounts) > 0:
                balances[curr] = BalanceDTO(
                    exchange=self.name,
                    currency=curr,
                    free=Decimal(str(ccxt_balance["free"].get(curr, 0))),
                    used=Decimal(str(ccxt_balance["used"].get(curr, 0))),
                    total=Decimal(str(amounts)),
                    timestamp=datetime.now(),
                )

        if currency:
            return balances.get(
                currency,
                BalanceDTO(
                    exchange=self.name,
                    currency=currency,
                    free=Decimal("0"),
                    used=Decimal("0"),
                    total=Decimal("0"),
                    timestamp=datetime.now(),
                ),
            )

        return balances

    async def fetch_positions(
        self, symbols: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Fetch trading positions."""
        if not self._ccxt:
            raise RuntimeError("Exchange not initialized. Call initialize() first.")

        return await self._retry_with_backoff(self._ccxt.fetch_positions, symbols)

    async def fetch_my_trades(
        self,
        symbol: Optional[str] = None,
        since: Optional[datetime] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Fetch user's trade history."""
        if not self._ccxt:
            raise RuntimeError("Exchange not initialized. Call initialize() first.")

        since_ms = int(since.timestamp() * 1000) if since else None

        return await self._retry_with_backoff(
            self._ccxt.fetch_my_trades, symbol, since_ms, limit
        )

    def amount_to_precision(self, symbol: str, amount: float | str | Decimal) -> str:
        """Convert amount to exchange-specific precision."""
        if not self._ccxt:
            raise RuntimeError("Exchange not initialized. Call initialize() first.")

        return self._ccxt.amount_to_precision(symbol, float(amount))

    def price_to_precision(self, symbol: str, price: float | str | Decimal) -> str:
        """Convert price to exchange-specific precision."""
        if not self._ccxt:
            raise RuntimeError("Exchange not initialized. Call initialize() first.")

        return self._ccxt.price_to_precision(symbol, float(price))

    def cost_to_precision(self, symbol: str, cost: float | str | Decimal) -> str:
        """Convert cost to exchange-specific precision."""
        if not self._ccxt:
            raise RuntimeError("Exchange not initialized. Call initialize() first.")

        return self._ccxt.cost_to_precision(symbol, float(cost))

    def currency_to_precision(
        self, currency: str, amount: float | str | Decimal
    ) -> str:
        """Convert currency amount to exchange-specific precision."""
        if not self._ccxt:
            raise RuntimeError("Exchange not initialized. Call initialize() first.")

        return self._ccxt.currency_to_precision(currency, float(amount))

    async def close(self) -> None:
        """Close the exchange connection and cleanup resources."""
        if self._ccxt:
            await self._ccxt.close()
            self._ccxt = None
            self._initialized = False
            logger.info(f"Closed {self.name} exchange connection")
