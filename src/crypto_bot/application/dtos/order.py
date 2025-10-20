"""
Order-related Data Transfer Objects.
"""

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional


class OrderType(str, Enum):
    """Order type enumeration."""

    MARKET = "market"
    LIMIT = "limit"


class OrderSide(str, Enum):
    """Order side enumeration."""

    BUY = "buy"
    SELL = "sell"


class OrderStatus(str, Enum):
    """Order status enumeration."""

    PENDING = "pending"
    OPEN = "open"
    CLOSED = "closed"
    CANCELED = "canceled"
    EXPIRED = "expired"
    REJECTED = "rejected"
    FAILED = "failed"


@dataclass
class RetryPolicy:
    """
    Retry policy configuration for order operations.

    Attributes:
        max_attempts: Maximum number of retry attempts (default: 3)
        initial_delay: Initial delay in seconds between retries (default: 1.0)
        max_delay: Maximum delay in seconds between retries (default: 30.0)
        exponential_base: Base for exponential backoff (default: 2.0)
    """

    max_attempts: int = 3
    initial_delay: float = 1.0
    max_delay: float = 30.0
    exponential_base: float = 2.0

    def __post_init__(self) -> None:
        """Validate retry policy parameters."""
        if self.max_attempts < 0:
            raise ValueError("max_attempts must be non-negative")
        if self.initial_delay <= 0:
            raise ValueError("initial_delay must be positive")
        if self.max_delay <= 0:
            raise ValueError("max_delay must be positive")
        if self.exponential_base <= 1:
            raise ValueError("exponential_base must be greater than 1")


@dataclass
class CreateOrderRequest:
    """
    Request to create a new order.

    Attributes:
        exchange: Exchange name (e.g., 'binance', 'coinbase')
        symbol: Trading pair symbol (e.g., 'BTC/USDT')
        side: Order side (buy or sell)
        type: Order type (market or limit)
        quantity: Order quantity in base currency
        price: Limit price (required for limit orders, ignored for market orders)
        timeout: Operation timeout in seconds (default: 30.0)
        retry_policy: Retry policy for this operation (default: RetryPolicy())
    """

    exchange: str
    symbol: str
    side: OrderSide
    type: OrderType
    quantity: Decimal
    price: Optional[Decimal] = None
    timeout: float = 30.0
    retry_policy: RetryPolicy = field(default_factory=RetryPolicy)

    def __post_init__(self) -> None:
        """Validate order request parameters."""
        if self.quantity <= 0:
            raise ValueError("quantity must be positive")
        if self.type == OrderType.LIMIT and self.price is None:
            raise ValueError("price is required for limit orders")
        if self.price is not None and self.price <= 0:
            raise ValueError("price must be positive")
        if self.timeout <= 0:
            raise ValueError("timeout must be positive")


@dataclass
class CancelOrderRequest:
    """
    Request to cancel an existing order.

    Attributes:
        exchange: Exchange name
        order_id: Exchange-specific order ID
        symbol: Trading pair symbol (required by some exchanges)
        timeout: Operation timeout in seconds (default: 30.0)
        retry_policy: Retry policy for this operation (default: RetryPolicy())
    """

    exchange: str
    order_id: str
    symbol: Optional[str] = None
    timeout: float = 30.0
    retry_policy: RetryPolicy = field(default_factory=RetryPolicy)

    def __post_init__(self) -> None:
        """Validate cancel request parameters."""
        if not self.order_id:
            raise ValueError("order_id cannot be empty")
        if self.timeout <= 0:
            raise ValueError("timeout must be positive")


@dataclass
class OrderDTO:
    """
    Order data transfer object.

    Represents a complete order with all its details.

    Attributes:
        id: Internal order ID
        exchange_order_id: Exchange-specific order ID
        exchange: Exchange name
        symbol: Trading pair symbol
        side: Order side (buy or sell)
        type: Order type (market or limit)
        status: Current order status
        quantity: Order quantity
        filled_quantity: Quantity that has been filled
        remaining_quantity: Quantity remaining to be filled
        price: Order price (None for market orders)
        average_price: Average execution price
        cost: Total cost of the order
        fee: Trading fee
        fee_currency: Currency in which fee was paid
        timestamp: Order creation timestamp
        last_trade_timestamp: Last trade execution timestamp
    """

    id: str
    exchange_order_id: str
    exchange: str
    symbol: str
    side: OrderSide
    type: OrderType
    status: OrderStatus
    quantity: Decimal
    filled_quantity: Decimal
    remaining_quantity: Decimal
    price: Optional[Decimal]
    average_price: Optional[Decimal]
    cost: Decimal
    fee: Decimal
    fee_currency: str
    timestamp: datetime
    last_trade_timestamp: Optional[datetime]


@dataclass
class OrderStatusDTO:
    """
    Order status data transfer object.

    Simplified view of order status for quick queries.

    Attributes:
        order_id: Exchange-specific order ID
        status: Current order status
        filled_quantity: Quantity that has been filled
        remaining_quantity: Quantity remaining to be filled
        average_price: Average execution price
        last_update: Last status update timestamp
    """

    order_id: str
    status: OrderStatus
    filled_quantity: Decimal
    remaining_quantity: Decimal
    average_price: Optional[Decimal]
    last_update: datetime


@dataclass
class BalanceDTO:
    """
    Account balance data transfer object.

    Attributes:
        exchange: Exchange name
        currency: Currency symbol (e.g., 'BTC', 'USDT')
        free: Available balance for trading
        used: Balance currently in open orders
        total: Total balance (free + used)
        timestamp: Balance query timestamp
    """

    exchange: str
    currency: str
    free: Decimal
    used: Decimal
    total: Decimal
    timestamp: datetime

    def __post_init__(self) -> None:
        """Validate balance values."""
        if self.free < 0:
            raise ValueError("free balance cannot be negative")
        if self.used < 0:
            raise ValueError("used balance cannot be negative")
        if self.total < 0:
            raise ValueError("total balance cannot be negative")
        # Allow small floating-point discrepancies
        expected_total = self.free + self.used
        if abs(self.total - expected_total) > Decimal("0.00000001"):
            raise ValueError(f"total must equal free + used (got {self.total}, expected {expected_total})")

