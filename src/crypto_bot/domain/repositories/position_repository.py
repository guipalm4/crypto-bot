"""Position repository interface."""

from abc import abstractmethod
from typing import List, Optional
from uuid import UUID

from crypto_bot.domain.repositories.base import IRepository
from crypto_bot.infrastructure.database.models import Position, PositionStatus


class IPositionRepository(IRepository[Position]):
    """Repository interface for Position entities."""

    @abstractmethod
    async def get_by_status(
        self, status: PositionStatus, skip: int = 0, limit: int = 100
    ) -> List[Position]:
        """
        Get positions by status.

        Args:
            status: The position status to filter by.
            skip: Number of records to skip.
            limit: Maximum number of records to return.

        Returns:
            List of positions with the specified status.
        """
        pass

    @abstractmethod
    async def get_by_trading_pair(
        self, trading_pair_id: UUID, skip: int = 0, limit: int = 100
    ) -> List[Position]:
        """
        Get positions by trading pair.

        Args:
            trading_pair_id: The trading pair UUID.
            skip: Number of records to skip.
            limit: Maximum number of records to return.

        Returns:
            List of positions for the specified trading pair.
        """
        pass

    @abstractmethod
    async def get_by_strategy(
        self, strategy_id: UUID, skip: int = 0, limit: int = 100
    ) -> List[Position]:
        """
        Get positions by strategy.

        Args:
            strategy_id: The strategy UUID.
            skip: Number of records to skip.
            limit: Maximum number of records to return.

        Returns:
            List of positions for the specified strategy.
        """
        pass

    @abstractmethod
    async def get_open_positions(
        self,
        exchange_id: Optional[UUID] = None,
        trading_pair_id: Optional[UUID] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Position]:
        """
        Get all open positions.

        Args:
            exchange_id: Optional exchange UUID to filter by.
            trading_pair_id: Optional trading pair UUID to filter by.
            skip: Number of records to skip.
            limit: Maximum number of records to return.

        Returns:
            List of open positions.
        """
        pass

    @abstractmethod
    async def get_by_entry_order(self, entry_order_id: UUID) -> Optional[Position]:
        """
        Get position by entry order.

        Args:
            entry_order_id: The entry order UUID.

        Returns:
            The position if found, None otherwise.
        """
        pass

