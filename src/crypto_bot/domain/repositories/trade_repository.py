"""Trade repository interface."""

from abc import abstractmethod
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from crypto_bot.domain.repositories.base import IRepository
from crypto_bot.infrastructure.database.models import Trade


class ITradeRepository(IRepository[Trade]):
    """Repository interface for Trade entities."""

    @abstractmethod
    async def get_by_order(
        self, order_id: UUID, skip: int = 0, limit: int = 100
    ) -> List[Trade]:
        """
        Get trades by order.

        Args:
            order_id: The order UUID.
            skip: Number of records to skip.
            limit: Maximum number of records to return.

        Returns:
            List of trades for the specified order.
        """
        pass

    @abstractmethod
    async def get_by_exchange_trade_id(
        self, exchange_trade_id: str
    ) -> Optional[Trade]:
        """
        Get trade by exchange trade ID.

        Args:
            exchange_trade_id: The trade ID from the exchange.

        Returns:
            The trade if found, None otherwise.
        """
        pass

    @abstractmethod
    async def get_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Trade]:
        """
        Get trades within a date range.

        Args:
            start_date: Start of the date range.
            end_date: End of the date range.
            skip: Number of records to skip.
            limit: Maximum number of records to return.

        Returns:
            List of trades within the specified date range.
        """
        pass

