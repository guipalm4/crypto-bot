"""Order repository interface."""

from abc import abstractmethod
from uuid import UUID

from crypto_bot.domain.repositories.base import IRepository
from crypto_bot.infrastructure.database.models import Order, OrderStatus


class IOrderRepository(IRepository[Order]):
    """Repository interface for Order entities."""

    @abstractmethod
    async def get_by_exchange_order_id(
        self, exchange_order_id: str, exchange_id: UUID
    ) -> Order | None:
        """
        Get order by exchange order ID.

        Args:
            exchange_order_id: The order ID from the exchange.
            exchange_id: The exchange UUID.

        Returns:
            The order if found, None otherwise.
        """
        pass

    @abstractmethod
    async def get_by_status(
        self, status: OrderStatus, skip: int = 0, limit: int = 100
    ) -> list[Order]:
        """
        Get orders by status.

        Args:
            status: The order status to filter by.
            skip: Number of records to skip.
            limit: Maximum number of records to return.

        Returns:
            List of orders with the specified status.
        """
        pass

    @abstractmethod
    async def get_by_trading_pair(
        self, trading_pair_id: UUID, skip: int = 0, limit: int = 100
    ) -> list[Order]:
        """
        Get orders by trading pair.

        Args:
            trading_pair_id: The trading pair UUID.
            skip: Number of records to skip.
            limit: Maximum number of records to return.

        Returns:
            List of orders for the specified trading pair.
        """
        pass

    @abstractmethod
    async def get_by_strategy(
        self, strategy_id: UUID, skip: int = 0, limit: int = 100
    ) -> list[Order]:
        """
        Get orders by strategy.

        Args:
            strategy_id: The strategy UUID.
            skip: Number of records to skip.
            limit: Maximum number of records to return.

        Returns:
            List of orders for the specified strategy.
        """
        pass

    @abstractmethod
    async def get_open_orders(
        self, exchange_id: UUID | None = None, skip: int = 0, limit: int = 100
    ) -> list[Order]:
        """
        Get all open orders (pending, partially filled).

        Args:
            exchange_id: Optional exchange UUID to filter by.
            skip: Number of records to skip.
            limit: Maximum number of records to return.

        Returns:
            List of open orders.
        """
        pass
