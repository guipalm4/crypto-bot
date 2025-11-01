"""
Unit tests for Data Transfer Objects (DTOs).

Tests validation, initialization, and edge cases for all DTOs.
"""

from datetime import UTC, datetime
from decimal import Decimal

import pytest
from faker import Faker

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


@pytest.fixture
def faker() -> Faker:
    """Provide Faker instance."""
    fake = Faker()
    Faker.seed(42)
    return fake


class TestRetryPolicy:
    """Test suite for RetryPolicy."""

    def test_default_values(self) -> None:
        """Test RetryPolicy default values."""
        policy = RetryPolicy()
        assert policy.max_attempts == 3
        assert policy.initial_delay == 1.0
        assert policy.max_delay == 30.0
        assert policy.exponential_base == 2.0

    def test_custom_values(self) -> None:
        """Test RetryPolicy with custom values."""
        policy = RetryPolicy(
            max_attempts=5, initial_delay=2.0, max_delay=60.0, exponential_base=3.0
        )
        assert policy.max_attempts == 5
        assert policy.initial_delay == 2.0
        assert policy.max_delay == 60.0
        assert policy.exponential_base == 3.0

    def test_negative_max_attempts_raises_error(self) -> None:
        """Test RetryPolicy validation with negative max_attempts."""
        with pytest.raises(ValueError, match="max_attempts must be non-negative"):
            RetryPolicy(max_attempts=-1)

    def test_invalid_initial_delay_raises_error(self) -> None:
        """Test RetryPolicy validation with invalid initial_delay."""
        with pytest.raises(ValueError, match="initial_delay must be positive"):
            RetryPolicy(initial_delay=0)

    def test_invalid_max_delay_raises_error(self) -> None:
        """Test RetryPolicy validation with invalid max_delay."""
        with pytest.raises(ValueError, match="max_delay must be positive"):
            RetryPolicy(max_delay=0)

    def test_invalid_exponential_base_raises_error(self) -> None:
        """Test RetryPolicy validation with invalid exponential_base."""
        with pytest.raises(ValueError, match="exponential_base must be greater than 1"):
            RetryPolicy(exponential_base=1.0)


class TestCreateOrderRequest:
    """Test suite for CreateOrderRequest."""

    def test_market_order_creation(self, faker: Faker) -> None:
        """Test creating market order request."""
        request = CreateOrderRequest(
            exchange=faker.word(),
            symbol="BTC/USDT",
            side=OrderSide.BUY,
            type=OrderType.MARKET,
            quantity=Decimal("0.1"),
        )
        assert request.type == OrderType.MARKET
        assert request.price is None

    def test_limit_order_creation(self, faker: Faker) -> None:
        """Test creating limit order request."""
        request = CreateOrderRequest(
            exchange=faker.word(),
            symbol="BTC/USDT",
            side=OrderSide.BUY,
            type=OrderType.LIMIT,
            quantity=Decimal("0.1"),
            price=Decimal("50000"),
        )
        assert request.type == OrderType.LIMIT
        assert request.price == Decimal("50000")

    def test_limit_order_without_price_raises_error(self, faker: Faker) -> None:
        """Test limit order requires price."""
        with pytest.raises(ValueError, match="price is required for limit orders"):
            CreateOrderRequest(
                exchange=faker.word(),
                symbol="BTC/USDT",
                side=OrderSide.BUY,
                type=OrderType.LIMIT,
                quantity=Decimal("0.1"),
            )

    def test_negative_quantity_raises_error(self, faker: Faker) -> None:
        """Test CreateOrderRequest validation with negative quantity."""
        with pytest.raises(ValueError, match="quantity must be positive"):
            CreateOrderRequest(
                exchange=faker.word(),
                symbol="BTC/USDT",
                side=OrderSide.BUY,
                type=OrderType.MARKET,
                quantity=Decimal("-0.1"),
            )

    def test_zero_quantity_raises_error(self, faker: Faker) -> None:
        """Test CreateOrderRequest validation with zero quantity."""
        with pytest.raises(ValueError, match="quantity must be positive"):
            CreateOrderRequest(
                exchange=faker.word(),
                symbol="BTC/USDT",
                side=OrderSide.BUY,
                type=OrderType.MARKET,
                quantity=Decimal("0"),
            )

    def test_negative_price_raises_error(self, faker: Faker) -> None:
        """Test CreateOrderRequest validation with negative price."""
        with pytest.raises(ValueError, match="price must be positive"):
            CreateOrderRequest(
                exchange=faker.word(),
                symbol="BTC/USDT",
                side=OrderSide.BUY,
                type=OrderType.LIMIT,
                quantity=Decimal("0.1"),
                price=Decimal("-50000"),
            )

    def test_custom_retry_policy(self, faker: Faker) -> None:
        """Test CreateOrderRequest with custom retry policy."""
        custom_policy = RetryPolicy(max_attempts=5, initial_delay=2.0)
        request = CreateOrderRequest(
            exchange=faker.word(),
            symbol="BTC/USDT",
            side=OrderSide.BUY,
            type=OrderType.MARKET,
            quantity=Decimal("0.1"),
            retry_policy=custom_policy,
        )
        assert request.retry_policy.max_attempts == 5
        assert request.retry_policy.initial_delay == 2.0


class TestCancelOrderRequest:
    """Test suite for CancelOrderRequest."""

    def test_cancel_order_creation(self, faker: Faker) -> None:
        """Test creating cancel order request."""
        request = CancelOrderRequest(
            exchange=faker.word(),
            order_id=faker.uuid4(),
            symbol="BTC/USDT",
        )
        assert request.order_id is not None
        assert request.symbol == "BTC/USDT"

    def test_empty_order_id_raises_error(self, faker: Faker) -> None:
        """Test CancelOrderRequest validation with empty order_id."""
        with pytest.raises(ValueError, match="order_id cannot be empty"):
            CancelOrderRequest(
                exchange=faker.word(),
                order_id="",
                symbol="BTC/USDT",
            )

    def test_negative_timeout_raises_error(self, faker: Faker) -> None:
        """Test CancelOrderRequest validation with negative timeout."""
        with pytest.raises(ValueError, match="timeout must be positive"):
            CancelOrderRequest(
                exchange=faker.word(),
                order_id=faker.uuid4(),
                symbol="BTC/USDT",
                timeout=-1.0,
            )

    def test_cancel_order_without_symbol(self, faker: Faker) -> None:
        """Test cancel order request without symbol."""
        request = CancelOrderRequest(
            exchange=faker.word(),
            order_id=faker.uuid4(),
        )
        assert request.symbol is None


class TestOrderDTO:
    """Test suite for OrderDTO."""

    def test_order_dto_creation(self, faker: Faker) -> None:
        """Test creating OrderDTO."""
        order = OrderDTO(
            id=faker.uuid4(),
            exchange_order_id=faker.uuid4(),
            exchange=faker.word(),
            symbol="BTC/USDT",
            side=OrderSide.BUY,
            type=OrderType.MARKET,
            status=OrderStatus.OPEN,
            quantity=Decimal("0.1"),
            filled_quantity=Decimal("0"),
            remaining_quantity=Decimal("0.1"),
            price=None,
            average_price=None,
            cost=Decimal("5000"),
            fee=Decimal("5"),
            fee_currency="USDT",
            timestamp=datetime.now(UTC),
            last_trade_timestamp=None,
        )
        assert order.side == OrderSide.BUY
        assert order.type == OrderType.MARKET
        assert order.status == OrderStatus.OPEN

    def test_order_dto_limit_order(self, faker: Faker) -> None:
        """Test OrderDTO with limit order."""
        order = OrderDTO(
            id=faker.uuid4(),
            exchange_order_id=faker.uuid4(),
            exchange=faker.word(),
            symbol="BTC/USDT",
            side=OrderSide.SELL,
            type=OrderType.LIMIT,
            status=OrderStatus.OPEN,
            quantity=Decimal("0.1"),
            filled_quantity=Decimal("0"),
            remaining_quantity=Decimal("0.1"),
            price=Decimal("51000"),
            average_price=None,
            cost=Decimal("5100"),
            fee=Decimal("5.1"),
            fee_currency="USDT",
            timestamp=datetime.now(UTC),
            last_trade_timestamp=None,
        )
        assert order.type == OrderType.LIMIT
        assert order.price == Decimal("51000")


class TestOrderStatusDTO:
    """Test suite for OrderStatusDTO."""

    def test_order_status_dto_creation(self, faker: Faker) -> None:
        """Test creating OrderStatusDTO."""
        status = OrderStatusDTO(
            order_id=faker.uuid4(),
            status=OrderStatus.CLOSED,
            filled_quantity=Decimal("0.1"),
            remaining_quantity=Decimal("0"),
            average_price=Decimal("50500"),
            last_update=datetime.now(UTC),
        )
        assert status.status == OrderStatus.CLOSED
        assert status.filled_quantity == Decimal("0.1")
        assert status.remaining_quantity == Decimal("0")

    def test_order_status_partial_fill(self, faker: Faker) -> None:
        """Test OrderStatusDTO with partial fill."""
        status = OrderStatusDTO(
            order_id=faker.uuid4(),
            status=OrderStatus.OPEN,
            filled_quantity=Decimal("0.05"),
            remaining_quantity=Decimal("0.05"),
            average_price=Decimal("50250"),
            last_update=datetime.now(UTC),
        )
        assert status.filled_quantity == Decimal("0.05")
        assert status.remaining_quantity == Decimal("0.05")


class TestBalanceDTO:
    """Test suite for BalanceDTO."""

    def test_balance_dto_creation(self, faker: Faker) -> None:
        """Test creating BalanceDTO."""
        balance = BalanceDTO(
            exchange=faker.word(),
            currency="BTC",
            free=Decimal("1.0"),
            used=Decimal("0.1"),
            total=Decimal("1.1"),
            timestamp=datetime.now(UTC),
        )
        assert balance.currency == "BTC"
        assert balance.free == Decimal("1.0")
        assert balance.used == Decimal("0.1")
        assert balance.total == Decimal("1.1")

    def test_balance_dto_validation_negative_free(self, faker: Faker) -> None:
        """Test BalanceDTO validation with negative free balance."""
        with pytest.raises(ValueError, match="free balance cannot be negative"):
            BalanceDTO(
                exchange=faker.word(),
                currency="BTC",
                free=Decimal("-0.1"),
                used=Decimal("0"),
                total=Decimal("0"),
                timestamp=datetime.now(UTC),
            )

    def test_balance_dto_validation_negative_used(self, faker: Faker) -> None:
        """Test BalanceDTO validation with negative used balance."""
        with pytest.raises(ValueError, match="used balance cannot be negative"):
            BalanceDTO(
                exchange=faker.word(),
                currency="BTC",
                free=Decimal("1.0"),
                used=Decimal("-0.1"),
                total=Decimal("1.0"),
                timestamp=datetime.now(UTC),
            )

    def test_balance_dto_validation_total_mismatch(self, faker: Faker) -> None:
        """Test BalanceDTO validation when total doesn't match free + used."""
        with pytest.raises(ValueError, match="total must equal free \\+ used"):
            BalanceDTO(
                exchange=faker.word(),
                currency="BTC",
                free=Decimal("1.0"),
                used=Decimal("0.1"),
                total=Decimal("2.0"),  # Wrong total
                timestamp=datetime.now(UTC),
            )

    def test_balance_dto_validation_negative_total(self, faker: Faker) -> None:
        """Test BalanceDTO validation with negative total."""
        with pytest.raises(ValueError, match="total balance cannot be negative"):
            BalanceDTO(
                exchange=faker.word(),
                currency="BTC",
                free=Decimal("0"),
                used=Decimal("0"),
                total=Decimal("-0.1"),
                timestamp=datetime.now(UTC),
            )

    def test_balance_dto_zero_balance(self, faker: Faker) -> None:
        """Test BalanceDTO with zero balance."""
        balance = BalanceDTO(
            exchange=faker.word(),
            currency="BTC",
            free=Decimal("0"),
            used=Decimal("0"),
            total=Decimal("0"),
            timestamp=datetime.now(UTC),
        )
        assert balance.total == Decimal("0")
