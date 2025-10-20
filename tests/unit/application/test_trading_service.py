"""
Unit tests for Trading Service.

Tests all trading operations with mocked CCXT responses.
"""

import asyncio
from datetime import datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
import ccxt.async_support as ccxt

from crypto_bot.application.dtos.order import (
    CancelOrderRequest,
    CreateOrderRequest,
    OrderSide,
    OrderStatus,
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
)
from crypto_bot.application.services.trading_service import TradingService


@pytest.fixture
def mock_exchange() -> MagicMock:
    """Create a mock CCXT exchange."""
    exchange = MagicMock(spec=ccxt.Exchange)
    exchange.create_market_order = AsyncMock()
    exchange.create_limit_order = AsyncMock()
    exchange.cancel_order = AsyncMock()
    exchange.fetch_order = AsyncMock()
    exchange.fetch_balance = AsyncMock()
    exchange.fetch_open_orders = AsyncMock()
    exchange.close = AsyncMock()
    return exchange


@pytest_asyncio.fixture
async def trading_service(mock_exchange) -> TradingService:
    """Create trading service with mocked exchange."""
    with patch.dict(
        "sys.modules",
        {
            "crypto_bot.config.settings": MagicMock(
                settings=MagicMock(
                    binance_api_key="test_key",
                    binance_api_secret="test_secret",
                    binance_sandbox=True,
                    coinbase_api_key=None,
                    coinbase_api_secret=None,
                    coinbase_passphrase=None,
                    coinbase_sandbox=False,
                )
            )
        },
    ):
        service = TradingService()
        service._exchanges["binance"] = mock_exchange
        yield service
        await service.close()


def create_ccxt_order_response(
    order_id: str = "12345",
    symbol: str = "BTC/USDT",
    side: str = "buy",
    order_type: str = "limit",
    status: str = "open",
    amount: float = 0.1,
    filled: float = 0.0,
    remaining: float = 0.1,
    price: float | None = 50000.0,
    average: float | None = None,
    cost: float = 5000.0,
) -> dict:
    """Create a mock CCXT order response."""
    timestamp = int(datetime.now().timestamp() * 1000)
    return {
        "id": order_id,
        "symbol": symbol,
        "side": side,
        "type": order_type,
        "status": status,
        "amount": amount,
        "filled": filled,
        "remaining": remaining,
        "price": price,
        "average": average,
        "cost": cost,
        "fee": {"cost": 2.5, "currency": "USDT"},
        "timestamp": timestamp,
        "lastTradeTimestamp": timestamp if filled > 0 else None,
        "info": {"exchange": "binance"},
    }


@pytest.mark.asyncio
class TestCreateOrder:
    """Test order creation."""

    async def test_create_market_buy_order(
        self, trading_service: TradingService, mock_exchange: MagicMock
    ) -> None:
        """Test creating a market buy order."""
        # Arrange
        mock_exchange.create_market_order.return_value = create_ccxt_order_response(
            order_type="market", side="buy", filled=0.1, remaining=0.0, price=None
        )

        request = CreateOrderRequest(
            exchange="binance",
            symbol="BTC/USDT",
            side=OrderSide.BUY,
            type=OrderType.MARKET,
            quantity=Decimal("0.1"),
        )

        # Act
        order = await trading_service.create_order(request)

        # Assert
        assert order.side == OrderSide.BUY
        assert order.type == OrderType.MARKET
        assert order.quantity == Decimal("0.1")
        mock_exchange.create_market_order.assert_called_once()

    async def test_create_limit_sell_order(
        self, trading_service: TradingService, mock_exchange: MagicMock
    ) -> None:
        """Test creating a limit sell order."""
        # Arrange
        mock_exchange.create_limit_order.return_value = create_ccxt_order_response(
            side="sell", order_type="limit", price=51000.0
        )

        request = CreateOrderRequest(
            exchange="binance",
            symbol="BTC/USDT",
            side=OrderSide.SELL,
            type=OrderType.LIMIT,
            quantity=Decimal("0.1"),
            price=Decimal("51000"),
        )

        # Act
        order = await trading_service.create_order(request)

        # Assert
        assert order.side == OrderSide.SELL
        assert order.type == OrderType.LIMIT
        assert order.price == Decimal("51000.0")
        mock_exchange.create_limit_order.assert_called_once()

    async def test_create_order_insufficient_balance(
        self, trading_service: TradingService, mock_exchange: MagicMock
    ) -> None:
        """Test order creation with insufficient balance."""
        # Arrange
        mock_exchange.create_market_order.side_effect = ccxt.InsufficientFunds(
            "Insufficient balance"
        )

        request = CreateOrderRequest(
            exchange="binance",
            symbol="BTC/USDT",
            side=OrderSide.BUY,
            type=OrderType.MARKET,
            quantity=Decimal("100"),
        )

        # Act & Assert
        with pytest.raises(InsufficientBalance):
            await trading_service.create_order(request)

    async def test_create_order_invalid_parameters(
        self, trading_service: TradingService, mock_exchange: MagicMock
    ) -> None:
        """Test order creation with invalid parameters."""
        # Arrange - negative price should fail validation
        with pytest.raises(ValueError, match="price must be positive"):
            CreateOrderRequest(
                exchange="binance",
                symbol="BTC/USDT",
                side=OrderSide.BUY,
                type=OrderType.LIMIT,
                quantity=Decimal("0.1"),
                price=Decimal("-1000"),
            )

        # Also test exchange-level validation
        mock_exchange.create_limit_order.side_effect = ccxt.InvalidOrder(
            "Invalid price"
        )

        request = CreateOrderRequest(
            exchange="binance",
            symbol="BTC/USDT",
            side=OrderSide.BUY,
            type=OrderType.LIMIT,
            quantity=Decimal("0.1"),
            price=Decimal("50000"),
        )

        # Act & Assert
        with pytest.raises(InvalidOrder):
            await trading_service.create_order(request)

    async def test_create_order_timeout(
        self, trading_service: TradingService, mock_exchange: MagicMock
    ) -> None:
        """Test order creation timeout."""
        # Arrange
        async def slow_create(*args, **kwargs):
            await asyncio.sleep(5)

        mock_exchange.create_market_order.side_effect = slow_create

        request = CreateOrderRequest(
            exchange="binance",
            symbol="BTC/USDT",
            side=OrderSide.BUY,
            type=OrderType.MARKET,
            quantity=Decimal("0.1"),
            timeout=0.1,
        )

        # Act & Assert
        with pytest.raises(TimeoutError):
            await trading_service.create_order(request)

    async def test_create_order_with_retry(
        self, trading_service: TradingService, mock_exchange: MagicMock
    ) -> None:
        """Test order creation with retry after network error."""
        # Arrange
        call_count = 0

        async def fail_then_succeed(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise ccxt.NetworkError("Connection failed")
            return create_ccxt_order_response()

        mock_exchange.create_market_order.side_effect = fail_then_succeed

        request = CreateOrderRequest(
            exchange="binance",
            symbol="BTC/USDT",
            side=OrderSide.BUY,
            type=OrderType.MARKET,
            quantity=Decimal("0.1"),
            retry_policy=RetryPolicy(max_attempts=3, initial_delay=0.01),
        )

        # Act
        order = await trading_service.create_order(request)

        # Assert
        assert order is not None
        assert call_count == 2
        assert mock_exchange.create_market_order.call_count == 2


@pytest.mark.asyncio
class TestCancelOrder:
    """Test order cancellation."""

    async def test_cancel_order_success(
        self, trading_service: TradingService, mock_exchange: MagicMock
    ) -> None:
        """Test successful order cancellation."""
        # Arrange
        mock_exchange.cancel_order.return_value = create_ccxt_order_response(
            order_id="12345", status="canceled"
        )

        request = CancelOrderRequest(
            exchange="binance", order_id="12345", symbol="BTC/USDT"
        )

        # Act
        order = await trading_service.cancel_order(request)

        # Assert
        assert order.status == OrderStatus.CANCELED
        mock_exchange.cancel_order.assert_called_once_with(
            "12345", "BTC/USDT", {}
        )

    async def test_cancel_order_not_found(
        self, trading_service: TradingService, mock_exchange: MagicMock
    ) -> None:
        """Test canceling non-existent order."""
        # Arrange
        mock_exchange.cancel_order.side_effect = ccxt.OrderNotFound(
            "Order not found"
        )

        request = CancelOrderRequest(
            exchange="binance", order_id="99999", symbol="BTC/USDT"
        )

        # Act & Assert
        with pytest.raises(OrderNotFound):
            await trading_service.cancel_order(request)


@pytest.mark.asyncio
class TestGetOrder:
    """Test order status and details retrieval."""

    async def test_get_order_success(
        self, trading_service: TradingService, mock_exchange: MagicMock
    ) -> None:
        """Test retrieving order details."""
        # Arrange
        mock_exchange.fetch_order.return_value = create_ccxt_order_response(
            order_id="12345",
            filled=0.05,
            remaining=0.05,
            average=50500.0,
        )

        # Act
        order = await trading_service.get_order("binance", "12345", "BTC/USDT")

        # Assert
        assert order.exchange_order_id == "12345"
        assert order.filled_quantity == Decimal("0.05")
        assert order.remaining_quantity == Decimal("0.05")
        assert order.average_price == Decimal("50500.0")

    async def test_get_order_status(
        self, trading_service: TradingService, mock_exchange: MagicMock
    ) -> None:
        """Test retrieving order status."""
        # Arrange
        mock_exchange.fetch_order.return_value = create_ccxt_order_response(
            order_id="12345", status="closed", filled=0.1, remaining=0.0
        )

        # Act
        status = await trading_service.get_order_status(
            "binance", "12345", "BTC/USDT"
        )

        # Assert
        assert status.order_id == "12345"
        assert status.status == OrderStatus.CLOSED
        assert status.filled_quantity == Decimal("0.1")
        assert status.remaining_quantity == Decimal("0.0")


@pytest.mark.asyncio
class TestGetBalance:
    """Test balance retrieval."""

    async def test_get_single_currency_balance(
        self, trading_service: TradingService, mock_exchange: MagicMock
    ) -> None:
        """Test retrieving balance for a single currency."""
        # Arrange
        mock_exchange.fetch_balance.return_value = {
            "BTC": {"free": 1.5, "used": 0.5, "total": 2.0},
            "USDT": {"free": 10000.0, "used": 5000.0, "total": 15000.0},
        }

        # Act
        balance = await trading_service.get_balance("binance", "BTC")

        # Assert
        assert isinstance(balance, object)  # BalanceDTO
        assert balance.currency == "BTC"
        assert balance.free == Decimal("1.5")
        assert balance.used == Decimal("0.5")
        assert balance.total == Decimal("2.0")

    async def test_get_all_balances(
        self, trading_service: TradingService, mock_exchange: MagicMock
    ) -> None:
        """Test retrieving all currency balances."""
        # Arrange
        mock_exchange.fetch_balance.return_value = {
            "BTC": {"free": 1.5, "used": 0.5, "total": 2.0},
            "USDT": {"free": 10000.0, "used": 5000.0, "total": 15000.0},
            "free": {},
            "used": {},
            "total": {},
        }

        # Act
        balances = await trading_service.get_balance("binance")

        # Assert
        assert isinstance(balances, dict)
        assert "BTC" in balances
        assert "USDT" in balances
        assert balances["BTC"].free == Decimal("1.5")
        assert balances["USDT"].total == Decimal("15000.0")


@pytest.mark.asyncio
class TestGetOpenOrders:
    """Test open orders retrieval."""

    async def test_get_open_orders_for_symbol(
        self, trading_service: TradingService, mock_exchange: MagicMock
    ) -> None:
        """Test retrieving open orders for a specific symbol."""
        # Arrange
        mock_exchange.fetch_open_orders.return_value = [
            create_ccxt_order_response(order_id="1", status="open"),
            create_ccxt_order_response(order_id="2", status="open"),
        ]

        # Act
        orders = await trading_service.get_open_orders("binance", "BTC/USDT")

        # Assert
        assert len(orders) == 2
        assert all(order.status == OrderStatus.OPEN for order in orders)
        mock_exchange.fetch_open_orders.assert_called_once_with("BTC/USDT")

    async def test_get_all_open_orders(
        self, trading_service: TradingService, mock_exchange: MagicMock
    ) -> None:
        """Test retrieving all open orders."""
        # Arrange
        mock_exchange.fetch_open_orders.return_value = [
            create_ccxt_order_response(order_id="1", symbol="BTC/USDT"),
            create_ccxt_order_response(order_id="2", symbol="ETH/USDT"),
        ]

        # Act
        orders = await trading_service.get_open_orders("binance")

        # Assert
        assert len(orders) == 2
        mock_exchange.fetch_open_orders.assert_called_once_with()


@pytest.mark.asyncio
class TestCancelAllOrders:
    """Test canceling all orders."""

    async def test_cancel_all_orders_for_symbol(
        self, trading_service: TradingService, mock_exchange: MagicMock
    ) -> None:
        """Test canceling all orders for a specific symbol."""
        # Arrange
        mock_exchange.fetch_open_orders.return_value = [
            create_ccxt_order_response(order_id="1"),
            create_ccxt_order_response(order_id="2"),
        ]
        mock_exchange.cancel_order.return_value = create_ccxt_order_response(
            status="canceled"
        )

        # Act
        canceled = await trading_service.cancel_all_orders(
            "binance", "BTC/USDT"
        )

        # Assert
        assert len(canceled) == 2
        assert mock_exchange.cancel_order.call_count == 2


@pytest.mark.asyncio
class TestErrorHandling:
    """Test error handling and exception conversion."""

    async def test_rate_limit_exceeded(
        self, trading_service: TradingService, mock_exchange: MagicMock
    ) -> None:
        """Test handling rate limit exceeded."""
        # Arrange
        mock_exchange.create_market_order.side_effect = ccxt.RateLimitExceeded(
            "Rate limit"
        )

        request = CreateOrderRequest(
            exchange="binance",
            symbol="BTC/USDT",
            side=OrderSide.BUY,
            type=OrderType.MARKET,
            quantity=Decimal("0.1"),
            retry_policy=RetryPolicy(max_attempts=1),
        )

        # Act & Assert
        with pytest.raises(RateLimitExceeded):
            await trading_service.create_order(request)

    async def test_network_error(
        self, trading_service: TradingService, mock_exchange: MagicMock
    ) -> None:
        """Test handling network errors."""
        # Arrange
        mock_exchange.fetch_order.side_effect = ccxt.NetworkError(
            "Connection failed"
        )

        # Act & Assert
        with pytest.raises(NetworkError):
            await trading_service.get_order("binance", "12345")

    async def test_exchange_error(
        self, trading_service: TradingService, mock_exchange: MagicMock
    ) -> None:
        """Test handling generic exchange errors."""
        # Arrange
        mock_exchange.fetch_balance.side_effect = ccxt.ExchangeError(
            "Exchange error"
        )

        # Act & Assert
        with pytest.raises(ExchangeError):
            await trading_service.get_balance("binance")

