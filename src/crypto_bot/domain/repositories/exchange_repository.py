"""Exchange repository interface."""

from abc import abstractmethod

from crypto_bot.domain.repositories.base import IRepository
from crypto_bot.infrastructure.database.models import Exchange


class IExchangeRepository(IRepository[Exchange]):
    """Repository interface for Exchange entities."""

    @abstractmethod
    async def get_by_name(self, name: str) -> Exchange | None:
        """
        Get exchange by name.

        Args:
            name: The exchange name (e.g., 'binance', 'coinbase').

        Returns:
            The exchange if found, None otherwise.
        """
        pass

    @abstractmethod
    async def get_active_exchanges(
        self, skip: int = 0, limit: int = 100
    ) -> list[Exchange]:
        """
        Get all active exchanges.

        Args:
            skip: Number of records to skip.
            limit: Maximum number of records to return.

        Returns:
            List of active exchanges.
        """
        pass

    @abstractmethod
    async def get_testnet_exchanges(
        self, skip: int = 0, limit: int = 100
    ) -> list[Exchange]:
        """
        Get all testnet exchanges.

        Args:
            skip: Number of records to skip.
            limit: Maximum number of records to return.

        Returns:
            List of testnet exchanges.
        """
        pass
