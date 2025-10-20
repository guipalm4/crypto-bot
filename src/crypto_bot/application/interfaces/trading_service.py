"""
Trading Service Interface.

Defines the contract for trading operations including order execution,
cancellation, status queries, and balance checks.
"""

from abc import ABC, abstractmethod
from typing import Dict, List

from crypto_bot.application.dtos.order import (
    BalanceDTO,
    CancelOrderRequest,
    CreateOrderRequest,
    OrderDTO,
    OrderStatusDTO,
)


class ITradingService(ABC):
    """
    Abstract interface for trading operations.

    This interface defines all trading-related operations that must be
    implemented by concrete trading service classes. It supports multiple
    exchanges through CCXT integration and provides async operations for
    better performance.
    """

    @abstractmethod
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
        pass

    @abstractmethod
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
        pass

    @abstractmethod
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
        pass

    @abstractmethod
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
        pass

    @abstractmethod
    async def get_balance(
        self, exchange: str, currency: str | None = None
    ) -> Dict[str, BalanceDTO] | BalanceDTO:
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
        pass

    @abstractmethod
    async def get_open_orders(
        self, exchange: str, symbol: str | None = None
    ) -> List[OrderDTO]:
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
        pass

    @abstractmethod
    async def cancel_all_orders(
        self, exchange: str, symbol: str | None = None
    ) -> List[OrderDTO]:
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
        pass

