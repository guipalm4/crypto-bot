"""Trading pair repository interface."""

from abc import abstractmethod
from uuid import UUID

from crypto_bot.domain.repositories.base import IRepository
from crypto_bot.infrastructure.database.models import TradingPair


class ITradingPairRepository(IRepository[TradingPair]):
    """Repository interface for TradingPair entities."""

    @abstractmethod
    async def get_by_symbols(
        self, base_symbol: str, quote_symbol: str, exchange_id: UUID
    ) -> TradingPair | None:
        """
        Get trading pair by base and quote symbols and exchange.

        Args:
            base_symbol: The base asset symbol (e.g., 'BTC').
            quote_symbol: The quote asset symbol (e.g., 'USDT').
            exchange_id: The exchange UUID.

        Returns:
            The trading pair if found, None otherwise.
        """
        pass

    @abstractmethod
    async def get_by_exchange(
        self, exchange_id: UUID, skip: int = 0, limit: int = 100
    ) -> list[TradingPair]:
        """
        Get trading pairs by exchange.

        Args:
            exchange_id: The exchange UUID.
            skip: Number of records to skip.
            limit: Maximum number of records to return.

        Returns:
            List of trading pairs for the specified exchange.
        """
        pass

    @abstractmethod
    async def get_by_base_asset(
        self, base_asset_id: UUID, skip: int = 0, limit: int = 100
    ) -> list[TradingPair]:
        """
        Get trading pairs by base asset.

        Args:
            base_asset_id: The base asset UUID.
            skip: Number of records to skip.
            limit: Maximum number of records to return.

        Returns:
            List of trading pairs with the specified base asset.
        """
        pass

    @abstractmethod
    async def get_by_quote_asset(
        self, quote_asset_id: UUID, skip: int = 0, limit: int = 100
    ) -> list[TradingPair]:
        """
        Get trading pairs by quote asset.

        Args:
            quote_asset_id: The quote asset UUID.
            skip: Number of records to skip.
            limit: Maximum number of records to return.

        Returns:
            List of trading pairs with the specified quote asset.
        """
        pass

    @abstractmethod
    async def get_active_pairs(
        self, exchange_id: UUID | None = None, skip: int = 0, limit: int = 100
    ) -> list[TradingPair]:
        """
        Get all active trading pairs.

        Args:
            exchange_id: Optional exchange UUID to filter by.
            skip: Number of records to skip.
            limit: Maximum number of records to return.

        Returns:
            List of active trading pairs.
        """
        pass
