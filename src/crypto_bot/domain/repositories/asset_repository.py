"""Asset repository interface."""

from abc import abstractmethod

from crypto_bot.domain.repositories.base import IRepository
from crypto_bot.infrastructure.database.models import Asset


class IAssetRepository(IRepository[Asset]):
    """Repository interface for Asset entities."""

    @abstractmethod
    async def get_by_symbol(self, symbol: str) -> Asset | None:
        """
        Get asset by symbol.

        Args:
            symbol: The asset symbol (e.g., 'BTC', 'ETH').

        Returns:
            The asset if found, None otherwise.
        """
        pass

    @abstractmethod
    async def get_active_assets(self, skip: int = 0, limit: int = 100) -> list[Asset]:
        """
        Get all active assets.

        Args:
            skip: Number of records to skip.
            limit: Maximum number of records to return.

        Returns:
            List of active assets.
        """
        pass

    @abstractmethod
    async def search_by_name(
        self, name: str, skip: int = 0, limit: int = 100
    ) -> list[Asset]:
        """
        Search assets by name (partial match).

        Args:
            name: The name or partial name to search for.
            skip: Number of records to skip.
            limit: Maximum number of records to return.

        Returns:
            List of matching assets.
        """
        pass
