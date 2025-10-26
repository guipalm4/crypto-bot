"""Strategy repository interface."""

from abc import abstractmethod

from crypto_bot.domain.repositories.base import IRepository
from crypto_bot.infrastructure.database.models import Strategy


class IStrategyRepository(IRepository[Strategy]):
    """Repository interface for Strategy entities."""

    @abstractmethod
    async def get_by_name(self, name: str) -> Strategy | None:
        """
        Get strategy by name.

        Args:
            name: The strategy name.

        Returns:
            The strategy if found, None otherwise.
        """
        pass

    @abstractmethod
    async def get_by_plugin_name(
        self, plugin_name: str, skip: int = 0, limit: int = 100
    ) -> list[Strategy]:
        """
        Get strategies by plugin name.

        Args:
            plugin_name: The plugin name (e.g., 'rsi_mean_reversion').
            skip: Number of records to skip.
            limit: Maximum number of records to return.

        Returns:
            List of strategies using the specified plugin.
        """
        pass

    @abstractmethod
    async def get_active_strategies(
        self, skip: int = 0, limit: int = 100
    ) -> list[Strategy]:
        """
        Get all active strategies.

        Args:
            skip: Number of records to skip.
            limit: Maximum number of records to return.

        Returns:
            List of active strategies.
        """
        pass
