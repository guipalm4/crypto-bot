"""
Trading Service Implementation.

Implements the ITradingService interface using CCXT for multi-exchange support.
Provides async order execution, cancellation, status queries, and balance checks
with configurable retry and timeout logic.
"""

import asyncio
import logging
from datetime import datetime
from decimal import Decimal
from typing import Any

import ccxt.async_support as ccxt

from crypto_bot.application.dtos.order import (
    BalanceDTO,
    CancelOrderRequest,
    CreateOrderRequest,
    OrderDTO,
    OrderSide,
    OrderStatus,
    OrderStatusDTO,
    OrderType,
    RetryPolicy,
)
from crypto_bot.application.exceptions import (
    ExchangeError,
    InsufficientBalance,
    InvalidOrder,
    NetworkError,
    OrderNotFound,
    RateLimitExceeded,
    TradingException,
)
from crypto_bot.application.interfaces.trading_service import ITradingService
from crypto_bot.config.settings import settings

logger = logging.getLogger(__name__)


class TradingService(ITradingService):
    """
    Trading service implementation using CCXT.

    Supports multiple exchanges with async operations, retry logic,
    and timeout handling. All operations are type-hinted and documented.
    """

    def __init__(self) -> None:
        """Initialize trading service with exchange connections."""
        self._exchanges: dict[str, ccxt.Exchange] = {}
        self._initialize_exchanges()

    def _initialize_exchanges(self) -> None:
        """
        Initialize configured exchanges from settings.

        Creates CCXT exchange instances for Binance and Coinbase based on
        configuration and available API credentials.
        """
        # Initialize Binance if configured
        if settings.binance_api_key and settings.binance_api_secret:
            exchange_class = ccxt.binance
            config = {
                "apiKey": settings.binance_api_key,
                "secret": settings.binance_api_secret,
                "enableRateLimit": True,
                "options": {
                    "defaultType": "spot",
                },
            }
            if settings.binance_sandbox:
                config["sandbox"] = True

            self._exchanges["binance"] = exchange_class(config)
            logger.info(
                "Initialized Binance exchange (sandbox: %s)",
                settings.binance_sandbox,
            )

        # Initialize Coinbase if configured
        if (
            settings.coinbase_api_key
            and settings.coinbase_api_secret
            and settings.coinbase_passphrase
        ):
            exchange_class = ccxt.coinbase
            config = {
                "apiKey": settings.coinbase_api_key,
                "secret": settings.coinbase_api_secret,
                "password": settings.coinbase_passphrase,
                "enableRateLimit": True,
            }
            if settings.coinbase_sandbox:
                config["sandbox"] = True

            self._exchanges["coinbase"] = exchange_class(config)
            logger.info(
                "Initialized Coinbase exchange (sandbox: %s)",
                settings.coinbase_sandbox,
            )

    def _get_exchange(self, exchange_name: str) -> ccxt.Exchange:
        """
        Get exchange instance by name.

        Args:
            exchange_name: Name of the exchange (e.g., 'binance', 'coinbase')

        Returns:
            CCXT exchange instance

        Raises:
            ValueError: If exchange is not configured
        """
        exchange = self._exchanges.get(exchange_name.lower())
        if not exchange:
            raise ValueError(
                f"Exchange '{exchange_name}' is not configured. "
                f"Available exchanges: {list(self._exchanges.keys())}"
            )
        return exchange

    async def _retry_with_backoff(
        self,
        operation: Any,
        retry_policy: RetryPolicy,
        operation_name: str = "operation",
    ) -> Any:
        """
        Execute an operation with retry and exponential backoff.

        Args:
            operation: Async function to execute
            retry_policy: Retry policy configuration
            operation_name: Name of the operation for logging

        Returns:
            Result of the operation

        Raises:
            TradingException: If all retry attempts fail
        """
        last_exception: TradingException | None = None
        delay = retry_policy.initial_delay

        for attempt in range(retry_policy.max_attempts):
            try:
                return await operation()
            except ccxt.RateLimitExceeded as e:
                # Must come before NetworkError since it's a subclass
                last_exception = RateLimitExceeded(
                    f"{operation_name} failed due to rate limit: {str(e)}"
                )
                logger.warning(
                    "Rate limit exceeded for %s (attempt %d/%d)",
                    operation_name,
                    attempt + 1,
                    retry_policy.max_attempts,
                )
            except ccxt.NetworkError as e:
                last_exception = NetworkError(
                    f"{operation_name} failed due to network error: {str(e)}"
                )
                logger.warning(
                    "%s failed (attempt %d/%d): %s",
                    operation_name,
                    attempt + 1,
                    retry_policy.max_attempts,
                    str(e),
                )

            # Don't sleep after the last attempt
            if attempt < retry_policy.max_attempts - 1:
                sleep_time = min(delay, retry_policy.max_delay)
                logger.debug("Retrying %s in %.2f seconds", operation_name, sleep_time)
                await asyncio.sleep(sleep_time)
                delay *= retry_policy.exponential_base

        # All retries failed
        raise last_exception or TradingException(
            f"{operation_name} failed after {retry_policy.max_attempts} attempts"
        )

    def _handle_ccxt_exception(self, e: Exception, operation: str) -> TradingException:
        """
        Convert CCXT exceptions to application exceptions.

        Args:
            e: CCXT exception
            operation: Name of the operation that failed

        Returns:
            Appropriate TradingException subclass
        """
        if isinstance(e, ccxt.OrderNotFound):
            return OrderNotFound(f"{operation}: Order not found - {str(e)}")
        elif isinstance(e, ccxt.InsufficientFunds):
            return InsufficientBalance(f"{operation}: Insufficient balance - {str(e)}")
        elif isinstance(e, ccxt.InvalidOrder):
            return InvalidOrder(f"{operation}: Invalid order - {str(e)}")
        elif isinstance(e, ccxt.NetworkError):
            return NetworkError(f"{operation}: Network error - {str(e)}")
        elif isinstance(e, ccxt.RateLimitExceeded):
            return RateLimitExceeded(f"{operation}: Rate limit exceeded - {str(e)}")
        elif isinstance(e, ccxt.ExchangeError):
            return ExchangeError(f"{operation}: Exchange error - {str(e)}")
        else:
            return TradingException(f"{operation}: Unexpected error - {str(e)}")

    def _ccxt_order_to_dto(self, ccxt_order: dict[str, Any]) -> OrderDTO:
        """
        Convert CCXT order to OrderDTO.

        Args:
            ccxt_order: Raw order data from CCXT

        Returns:
            OrderDTO instance
        """
        # Map CCXT status to our OrderStatus enum
        status_map = {
            "open": OrderStatus.OPEN,
            "closed": OrderStatus.CLOSED,
            "canceled": OrderStatus.CANCELED,
            "cancelled": OrderStatus.CANCELED,
            "expired": OrderStatus.EXPIRED,
            "rejected": OrderStatus.REJECTED,
        }
        status = status_map.get(
            ccxt_order.get("status", "").lower(), OrderStatus.PENDING
        )

        # Extract order details
        order_id = ccxt_order["id"]
        symbol = ccxt_order["symbol"]
        side = OrderSide.BUY if ccxt_order["side"] == "buy" else OrderSide.SELL
        order_type = (
            OrderType.MARKET if ccxt_order["type"] == "market" else OrderType.LIMIT
        )

        # Get quantities
        amount = Decimal(str(ccxt_order.get("amount", 0)))
        filled = Decimal(str(ccxt_order.get("filled", 0)))
        remaining = Decimal(str(ccxt_order.get("remaining", 0)))

        # Get prices
        price = Decimal(str(ccxt_order["price"])) if ccxt_order.get("price") else None
        average = (
            Decimal(str(ccxt_order["average"])) if ccxt_order.get("average") else None
        )

        # Get cost and fees
        cost = Decimal(str(ccxt_order.get("cost", 0)))
        fee_data = ccxt_order.get("fee", {})
        fee = Decimal(str(fee_data.get("cost", 0))) if fee_data else Decimal("0")
        fee_currency = fee_data.get("currency", "UNKNOWN") if fee_data else "UNKNOWN"

        # Get timestamps
        timestamp = datetime.fromtimestamp(ccxt_order["timestamp"] / 1000)
        last_trade = (
            datetime.fromtimestamp(ccxt_order["lastTradeTimestamp"] / 1000)
            if ccxt_order.get("lastTradeTimestamp")
            else None
        )

        return OrderDTO(
            id=order_id,
            exchange_order_id=order_id,
            exchange=ccxt_order.get("info", {}).get("exchange", "unknown"),
            symbol=symbol,
            side=side,
            type=order_type,
            status=status,
            quantity=amount,
            filled_quantity=filled,
            remaining_quantity=remaining,
            price=price,
            average_price=average,
            cost=cost,
            fee=fee,
            fee_currency=fee_currency,
            timestamp=timestamp,
            last_trade_timestamp=last_trade,
        )

    async def create_order(self, request: CreateOrderRequest) -> OrderDTO:
        """
        Create a new order (market or limit).

        Args:
            request: Order creation request with all parameters

        Returns:
            OrderDTO: Created order with all details

        Raises:
            ValueError: If order parameters are invalid
            ExchangeError: If exchange rejects the order
            NetworkError: If network communication fails
            TimeoutError: If operation exceeds timeout
        """
        exchange = self._get_exchange(request.exchange)

        # Prepare order parameters
        params: dict[str, Any] = {}

        async def _create() -> dict[str, Any]:
            """Inner function for retry logic."""
            if request.type == OrderType.MARKET:
                return await exchange.create_market_order(
                    symbol=request.symbol,
                    side=request.side.value,
                    amount=float(request.quantity),
                    params=params,
                )
            else:  # LIMIT
                return await exchange.create_limit_order(
                    symbol=request.symbol,
                    side=request.side.value,
                    amount=float(request.quantity),
                    price=float(request.price) if request.price is not None else 0.0,
                    params=params,
                )

        try:
            # Execute with timeout and retry
            ccxt_order = await asyncio.wait_for(
                self._retry_with_backoff(
                    _create,
                    request.retry_policy,
                    f"Create {request.type.value} {request.side.value} order",
                ),
                timeout=request.timeout,
            )
            logger.info(
                "Created %s %s order on %s: %s %s @ %s",
                request.type.value,
                request.side.value,
                request.exchange,
                request.quantity,
                request.symbol,
                request.price or "market",
            )
            return self._ccxt_order_to_dto(ccxt_order)

        except TimeoutError:
            logger.error("Order creation timed out after %.2f seconds", request.timeout)
            raise TimeoutError(
                f"Order creation exceeded timeout of {request.timeout} seconds"
            ) from None
        except ccxt.BaseError as e:
            raise self._handle_ccxt_exception(e, "Create order") from e

    async def cancel_order(self, request: CancelOrderRequest) -> OrderDTO:
        """
        Cancel an existing order.

        Args:
            request: Order cancellation request

        Returns:
            OrderDTO: Canceled order with updated status

        Raises:
            ValueError: If order ID is invalid
            OrderNotFound: If order doesn't exist
            ExchangeError: If exchange rejects the cancellation
            NetworkError: If network communication fails
            TimeoutError: If operation exceeds timeout
        """
        exchange = self._get_exchange(request.exchange)

        async def _cancel() -> dict[str, Any]:
            """Inner function for retry logic."""
            params: dict[str, Any] = {}
            if request.symbol:
                return await exchange.cancel_order(
                    request.order_id, request.symbol, params
                )
            else:
                return await exchange.cancel_order(request.order_id, None, params)

        try:
            ccxt_order = await asyncio.wait_for(
                self._retry_with_backoff(_cancel, request.retry_policy, "Cancel order"),
                timeout=request.timeout,
            )
            logger.info("Canceled order %s on %s", request.order_id, request.exchange)
            return self._ccxt_order_to_dto(ccxt_order)

        except TimeoutError:
            logger.error(
                "Order cancellation timed out after %.2f seconds", request.timeout
            )
            raise TimeoutError(
                f"Order cancellation exceeded timeout of {request.timeout} seconds"
            ) from None
        except ccxt.BaseError as e:
            raise self._handle_ccxt_exception(e, "Cancel order") from e

    async def get_order_status(
        self, exchange: str, order_id: str, symbol: str | None = None
    ) -> OrderStatusDTO:
        """
        Query the current status of an order.

        Args:
            exchange: Exchange name
            order_id: Exchange-specific order ID
            symbol: Trading pair symbol (required by some exchanges)

        Returns:
            OrderStatusDTO: Current order status

        Raises:
            ValueError: If parameters are invalid
            OrderNotFound: If order doesn't exist
            ExchangeError: If exchange query fails
            NetworkError: If network communication fails
        """
        order = await self.get_order(exchange, order_id, symbol)
        return OrderStatusDTO(
            order_id=order.exchange_order_id,
            status=order.status,
            filled_quantity=order.filled_quantity,
            remaining_quantity=order.remaining_quantity,
            average_price=order.average_price,
            last_update=order.last_trade_timestamp or order.timestamp,
        )

    async def get_order(
        self, exchange: str, order_id: str, symbol: str | None = None
    ) -> OrderDTO:
        """
        Retrieve full order details.

        Args:
            exchange: Exchange name
            order_id: Exchange-specific order ID
            symbol: Trading pair symbol (required by some exchanges)

        Returns:
            OrderDTO: Complete order information

        Raises:
            ValueError: If parameters are invalid
            OrderNotFound: If order doesn't exist
            ExchangeError: If exchange query fails
            NetworkError: If network communication fails
        """
        exchange_instance = self._get_exchange(exchange)

        try:
            if symbol:
                ccxt_order = await exchange_instance.fetch_order(order_id, symbol)
            else:
                ccxt_order = await exchange_instance.fetch_order(order_id)

            logger.debug(
                "Fetched order %s from %s: status=%s",
                order_id,
                exchange,
                ccxt_order.get("status"),
            )
            return self._ccxt_order_to_dto(ccxt_order)

        except ccxt.BaseError as e:
            raise self._handle_ccxt_exception(e, "Get order") from e

    async def get_balance(
        self, exchange: str, currency: str | None = None
    ) -> dict[str, BalanceDTO] | BalanceDTO:
        """
        Retrieve account balance(s).

        Args:
            exchange: Exchange name
            currency: Specific currency to query (None for all currencies)

        Returns:
            If currency is specified: BalanceDTO for that currency
            If currency is None: Dict mapping currency symbols to BalanceDTOs

        Raises:
            ValueError: If parameters are invalid
            ExchangeError: If exchange query fails
            NetworkError: If network communication fails
        """
        exchange_instance = self._get_exchange(exchange)

        try:
            balance_data = await exchange_instance.fetch_balance()
            timestamp = datetime.now()

            if currency:
                # Return single currency balance
                if currency not in balance_data:
                    raise ValueError(f"Currency {currency} not found in balance")

                currency_balance = balance_data[currency]
                return BalanceDTO(
                    exchange=exchange,
                    currency=currency,
                    free=Decimal(str(currency_balance.get("free", 0))),
                    used=Decimal(str(currency_balance.get("used", 0))),
                    total=Decimal(str(currency_balance.get("total", 0))),
                    timestamp=timestamp,
                )
            else:
                # Return all currency balances
                balances = {}
                for curr, data in balance_data.items():
                    if curr in ["free", "used", "total", "info", "timestamp"]:
                        # Skip metadata fields
                        continue
                    balances[curr] = BalanceDTO(
                        exchange=exchange,
                        currency=curr,
                        free=Decimal(str(data.get("free", 0))),
                        used=Decimal(str(data.get("used", 0))),
                        total=Decimal(str(data.get("total", 0))),
                        timestamp=timestamp,
                    )
                return balances

        except ccxt.BaseError as e:
            raise self._handle_ccxt_exception(e, "Get balance") from e

    async def get_open_orders(
        self, exchange: str, symbol: str | None = None
    ) -> list[OrderDTO]:
        """
        Retrieve all open orders for an exchange.

        Args:
            exchange: Exchange name
            symbol: Filter by trading pair (None for all pairs)

        Returns:
            List of open orders

        Raises:
            ValueError: If parameters are invalid
            ExchangeError: If exchange query fails
            NetworkError: If network communication fails
        """
        exchange_instance = self._get_exchange(exchange)

        try:
            if symbol:
                ccxt_orders = await exchange_instance.fetch_open_orders(symbol)
            else:
                ccxt_orders = await exchange_instance.fetch_open_orders()

            logger.debug("Fetched %d open orders from %s", len(ccxt_orders), exchange)
            return [self._ccxt_order_to_dto(order) for order in ccxt_orders]

        except ccxt.BaseError as e:
            raise self._handle_ccxt_exception(e, "Get open orders") from e

    async def cancel_all_orders(
        self, exchange: str, symbol: str | None = None
    ) -> list[OrderDTO]:
        """
        Cancel all open orders for an exchange.

        Args:
            exchange: Exchange name
            symbol: Cancel only orders for this trading pair (None for all)

        Returns:
            List of canceled orders

        Raises:
            ValueError: If parameters are invalid
            ExchangeError: If exchange rejects the operation
            NetworkError: If network communication fails
        """
        # Get all open orders
        open_orders = await self.get_open_orders(exchange, symbol)

        # Cancel each order
        canceled_orders = []
        for order in open_orders:
            try:
                cancel_request = CancelOrderRequest(
                    exchange=exchange,
                    order_id=order.exchange_order_id,
                    symbol=order.symbol,
                )
                canceled_order = await self.cancel_order(cancel_request)
                canceled_orders.append(canceled_order)
            except Exception as e:
                logger.warning(
                    "Failed to cancel order %s: %s", order.exchange_order_id, str(e)
                )

        logger.info(
            "Canceled %d/%d orders on %s",
            len(canceled_orders),
            len(open_orders),
            exchange,
        )
        return canceled_orders

    async def close(self) -> None:
        """Close all exchange connections."""
        for exchange_name, exchange in self._exchanges.items():
            try:
                await exchange.close()
                logger.info("Closed connection to %s", exchange_name)
            except Exception as e:
                logger.warning(
                    "Error closing connection to %s: %s", exchange_name, str(e)
                )

    async def __aenter__(self) -> "TradingService":
        """Async context manager entry."""
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: Any | None,
    ) -> None:
        """Async context manager exit."""
        await self.close()
